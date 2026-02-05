#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
분산된 TC 청크들을 병합하는 스크립트

병렬 에이전트가 생성한 tc_chunk_*.json 파일들을 하나의 tc_data.json으로 병합합니다.
- Reference(페이지 번호) 기준 정렬
- TC ID 순차 재할당
- 프로젝트 정보 병합
- 크로스 레퍼런스 정규화
"""

import json
import sys
import re
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional


def extract_page_number(reference: str) -> int:
    """Reference 문자열에서 페이지 번호 추출"""
    if not reference:
        return 999999  # 페이지 번호 없으면 맨 뒤로

    # "5P", "5P (참조: 3P)", "5P (참조: [11-1])" 등에서 첫 번째 숫자 추출
    match = re.search(r'(\d+)P', reference)
    if match:
        return int(match.group(1))

    # 숫자만 있는 경우
    match = re.search(r'(\d+)', reference)
    if match:
        return int(match.group(1))

    return 999999


def load_chunk_files(output_dir: Path) -> List[Dict[str, Any]]:
    """tc_chunk_*.json 파일들 로드"""
    chunks = []
    pattern = str(output_dir / "tc_chunk_*.json")
    chunk_files = sorted(glob.glob(pattern))

    for chunk_file in chunk_files:
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)
            chunks.append({
                "file": chunk_file,
                "data": chunk_data
            })
        print(f"  로드: {Path(chunk_file).name}")

    return chunks


def merge_project_info(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """프로젝트 정보 병합 (첫 번째 청크 기준, 나머지는 보완)"""
    merged_info = {}

    for chunk in chunks:
        chunk_info = chunk["data"].get("project_info", {})
        for key, value in chunk_info.items():
            if key not in merged_info or not merged_info[key]:
                merged_info[key] = value

    return merged_info


def normalize_field_names(tc: Dict[str, Any]) -> Dict[str, Any]:
    """청크 에이전트 출력 필드명을 write_excel.py 기대 필드명으로 변환"""
    # 필드 매핑: 청크 출력 → Excel 기대값
    field_mapping = {
        "steps": "test_step",
        "expected": "expected_result",
        "precondition": "pre_condition",
    }

    for old_key, new_key in field_mapping.items():
        if old_key in tc and new_key not in tc:
            tc[new_key] = tc.pop(old_key)

    return tc


def collect_all_testcases(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """모든 청크에서 테스트케이스 수집"""
    all_testcases = []

    for chunk in chunks:
        # testcases 또는 test_cases 키 모두 지원
        testcases = chunk["data"].get("testcases", [])
        if not testcases:
            testcases = chunk["data"].get("test_cases", [])
        chunk_id = chunk["data"].get("chunk_id", 0)

        for tc in testcases:
            # 필드명 정규화
            tc = normalize_field_names(tc)
            # 원본 청크 정보 추가 (디버깅용)
            tc["_source_chunk"] = chunk_id
            all_testcases.append(tc)

    return all_testcases


def sort_testcases_by_page(testcases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """페이지 번호 기준 정렬"""
    def sort_key(tc):
        page_num = extract_page_number(tc.get("reference", ""))
        # 같은 페이지 내에서는 원래 순서 유지
        original_id = tc.get("test_case_id", "")
        # CHUNK1_001 → (1, 1), CHUNK2_015 → (2, 15)
        chunk_match = re.search(r'CHUNK(\d+)_(\d+)', original_id)
        if chunk_match:
            return (page_num, int(chunk_match.group(1)), int(chunk_match.group(2)))
        return (page_num, 0, 0)

    return sorted(testcases, key=sort_key)


def reassign_tc_ids(testcases: List[Dict[str, Any]], prefix: str = "IT_OP") -> List[Dict[str, Any]]:
    """TC ID 순차 재할당"""
    for idx, tc in enumerate(testcases, start=1):
        # 원래 ID 백업
        tc["_original_id"] = tc.get("test_case_id", "")
        # 새 ID 할당
        tc["test_case_id"] = f"{prefix}_{idx:03d}"

    return testcases


def normalize_cross_references(testcases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """크로스 레퍼런스 정규화 (청크 ID → 실제 TC ID 매핑)"""
    # ID 매핑 테이블 생성
    id_mapping = {}
    for tc in testcases:
        original_id = tc.get("_original_id", "")
        new_id = tc.get("test_case_id", "")
        if original_id:
            id_mapping[original_id] = new_id

    # 레퍼런스 내 ID 치환 (필요 시)
    for tc in testcases:
        reference = tc.get("reference", "")
        # 청크 ID가 레퍼런스에 포함된 경우 치환
        for old_id, new_id in id_mapping.items():
            if old_id in reference:
                reference = reference.replace(old_id, new_id)
        tc["reference"] = reference

    return testcases


def clean_internal_fields(testcases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """내부 사용 필드 제거"""
    for tc in testcases:
        tc.pop("_source_chunk", None)
        tc.pop("_original_id", None)
    return testcases


def detect_prefix_from_chunks(chunks: List[Dict[str, Any]]) -> str:
    """청크에서 TC ID 접두사 추출"""
    for chunk in chunks:
        testcases = chunk["data"].get("testcases", [])
        if not testcases:
            testcases = chunk["data"].get("test_cases", [])
        if testcases:
            tc_id = testcases[0].get("test_case_id", "")
            # IT_OP_001 → IT_OP
            match = re.match(r'(IT_[A-Z]+)_', tc_id)
            if match:
                return match.group(1)
    return "IT_OP"


def merge_tc_chunks(
    output_dir: Path,
    prefix: Optional[str] = None,
    output_file: Optional[Path] = None
) -> Dict[str, Any]:
    """TC 청크 병합 메인 함수"""
    print("=" * 60)
    print("  TC 청크 병합")
    print("=" * 60)

    # 청크 파일 로드
    print("\n청크 파일 로딩...")
    chunks = load_chunk_files(output_dir)

    if not chunks:
        print("Error: tc_chunk_*.json 파일을 찾을 수 없습니다.")
        return {}

    print(f"  총 {len(chunks)}개 청크 로드 완료")

    # 접두사 결정
    if not prefix:
        prefix = detect_prefix_from_chunks(chunks)
    print(f"\nTC ID 접두사: {prefix}")

    # 프로젝트 정보 병합
    print("\n프로젝트 정보 병합...")
    project_info = merge_project_info(chunks)

    # 테스트케이스 수집
    print("테스트케이스 수집...")
    all_testcases = collect_all_testcases(chunks)
    print(f"  총 {len(all_testcases)}개 TC 수집")

    # 페이지 순서로 정렬
    print("페이지 순서로 정렬...")
    sorted_testcases = sort_testcases_by_page(all_testcases)

    # TC ID 재할당
    print("TC ID 재할당...")
    reassigned_testcases = reassign_tc_ids(sorted_testcases, prefix)

    # 크로스 레퍼런스 정규화
    print("크로스 레퍼런스 정규화...")
    normalized_testcases = normalize_cross_references(reassigned_testcases)

    # 내부 필드 정리
    final_testcases = clean_internal_fields(normalized_testcases)

    # 결과 생성
    result = {
        "project_info": project_info,
        "total_testcases": len(final_testcases),
        "merged_from_chunks": len(chunks),
        "testcases": final_testcases
    }

    # 저장
    if output_file is None:
        output_file = output_dir / "tc_data.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "-" * 60)
    print(f"병합 완료: {len(final_testcases)}개 TC")
    print(f"출력 파일: {output_file}")
    print("=" * 60)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python merge_tc_chunks.py <output_dir> [--prefix IT_XX] [--output <path>]")
        sys.exit(1)

    output_dir = Path(sys.argv[1])

    # 옵션 파싱
    prefix = None
    output_file = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--prefix" and i + 1 < len(args):
            prefix = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_file = Path(args[i + 1])
            i += 2
        else:
            i += 1

    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)

    # 병합 실행
    result = merge_tc_chunks(output_dir, prefix, output_file)

    return result


if __name__ == "__main__":
    main()
