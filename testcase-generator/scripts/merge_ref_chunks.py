#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reference 매핑 청크 병합 스크립트

병렬 매핑 에이전트가 생성한 ref_chunk_*.json 파일들을 하나의 ref_mapping.json으로 병합합니다.
- row_index 기준 정렬
- 중복 TC ID 처리 (높은 confidence 우선)
- 통계 요약
"""

import json
import sys
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional

# 중앙 설정에서 가져오기
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from config import OUTPUT_DIR, REF_MAP_CONFIDENCE_THRESHOLD
except ImportError:
    OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"
    REF_MAP_CONFIDENCE_THRESHOLD = 0.7


def load_ref_chunks(output_dir: Path) -> List[Dict[str, Any]]:
    """ref_chunk_*.json 파일들 로드"""
    chunks = []
    pattern = str(output_dir / "ref_chunk_*.json")
    chunk_files = sorted(glob.glob(pattern))

    for chunk_file in chunk_files:
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunk_data = json.load(f)
            chunks.append({
                "file": chunk_file,
                "data": chunk_data,
            })
        print(f"  로드: {Path(chunk_file).name}")

    return chunks


def merge_mappings(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """모든 청크에서 매핑 결과 수집 및 중복 처리"""
    # TC ID → 매핑 결과 (가장 높은 confidence 우선)
    best_mappings: Dict[str, Dict[str, Any]] = {}

    for chunk in chunks:
        mappings = chunk["data"].get("mappings", [])
        for mapping in mappings:
            tc_id = mapping.get("test_case_id", "")
            if not tc_id:
                continue

            confidence = mapping.get("confidence", 0)

            if tc_id not in best_mappings:
                best_mappings[tc_id] = mapping
            elif confidence > best_mappings[tc_id].get("confidence", 0):
                best_mappings[tc_id] = mapping

    # row_index 기준 정렬
    sorted_mappings = sorted(
        best_mappings.values(),
        key=lambda m: m.get("row_index", 0),
    )

    return sorted_mappings


def compute_stats(mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """통계 계산"""
    total = len(mappings)
    if total == 0:
        return {
            "total_tcs": 0,
            "mapped_count": 0,
            "unmapped_count": 0,
            "average_confidence": 0,
            "confidence_distribution": {},
        }

    mapped = [m for m in mappings if m.get("reference")]
    unmapped = [m for m in mappings if not m.get("reference")]

    confidences = [m.get("confidence", 0) for m in mapped]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    # confidence 분포
    dist = {"high_90+": 0, "good_70_89": 0, "medium_50_69": 0, "low_under_50": 0}
    for c in confidences:
        if c >= 0.90:
            dist["high_90+"] += 1
        elif c >= 0.70:
            dist["good_70_89"] += 1
        elif c >= 0.50:
            dist["medium_50_69"] += 1
        else:
            dist["low_under_50"] += 1

    return {
        "total_tcs": total,
        "mapped_count": len(mapped),
        "unmapped_count": len(unmapped),
        "average_confidence": round(avg_confidence, 3),
        "confidence_distribution": dist,
    }


def merge_ref_chunks(
    output_dir: Path,
    output_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Reference 매핑 청크 병합 메인 함수"""
    print("=" * 60)
    print("  Reference 매핑 청크 병합")
    print("=" * 60)

    # 청크 파일 로드
    print("\n청크 파일 로딩...")
    chunks = load_ref_chunks(output_dir)

    if not chunks:
        print("Error: ref_chunk_*.json 파일을 찾을 수 없습니다.")
        return {}

    print(f"  총 {len(chunks)}개 청크 로드 완료")

    # 매핑 결과 병합
    print("\n매핑 결과 병합...")
    mappings = merge_mappings(chunks)
    print(f"  총 {len(mappings)}개 TC 매핑")

    # 통계 계산
    stats = compute_stats(mappings)

    # 결과 구성
    result = {
        "total_tcs": stats["total_tcs"],
        "mapped_count": stats["mapped_count"],
        "unmapped_count": stats["unmapped_count"],
        "average_confidence": stats["average_confidence"],
        "confidence_distribution": stats["confidence_distribution"],
        "mappings": mappings,
    }

    # 저장
    if output_file is None:
        output_file = output_dir / "ref_mapping.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n병합 완료:")
    print(f"  총 TC: {stats['total_tcs']}")
    print(f"  매핑 성공: {stats['mapped_count']}")
    print(f"  매핑 실패: {stats['unmapped_count']}")
    print(f"  평균 confidence: {stats['average_confidence']:.1%}")
    print(f"  출력: {output_file}")
    print("=" * 60)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python merge_ref_chunks.py <output_dir> [options]")
        print()
        print("Options:")
        print("  --output <path>   출력 파일 경로 (기본: output/ref_mapping.json)")
        sys.exit(1)

    output_dir = Path(sys.argv[1])

    # 옵션 파싱
    output_file = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_file = Path(args[i + 1])
            i += 2
        else:
            i += 1

    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)

    merge_ref_chunks(output_dir, output_file)


if __name__ == "__main__":
    main()
