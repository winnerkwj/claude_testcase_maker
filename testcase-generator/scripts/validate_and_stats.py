#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TC 검증 및 통계 통합 스크립트

validate-tc와 tc-stats 기능을 통합하여 컨텍스트를 절약합니다.
한 번의 파일 로드로 검증과 통계를 동시에 출력합니다.
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import Counter, defaultdict


def load_tc_data(tc_data_path: Path) -> Dict[str, Any]:
    """tc_data.json 로드"""
    with open(tc_data_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 검증 (Validation) 함수들
# ============================================================

def validate_tc_id_sequence(testcases: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """TC ID 연속성 검증"""
    errors = []
    ids = [tc.get("test_case_id", "") for tc in testcases]

    # 중복 검사
    id_counts = Counter(ids)
    duplicates = [tc_id for tc_id, count in id_counts.items() if count > 1]
    if duplicates:
        for dup in duplicates:
            indices = [i + 1 for i, tc in enumerate(testcases) if tc.get("test_case_id") == dup]
            errors.append(f"TC ID 중복: {dup} (행 {', '.join(map(str, indices))})")

    # 연속성 검사
    id_numbers = []
    for tc_id in ids:
        match = re.search(r'_(\d+)$', tc_id)
        if match:
            id_numbers.append(int(match.group(1)))

    if id_numbers:
        expected = list(range(1, len(id_numbers) + 1))
        if id_numbers != expected:
            missing = set(expected) - set(id_numbers)
            if missing:
                errors.append(f"TC ID 누락: {sorted(missing)[:5]}...")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_depth_completeness(testcases: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Depth 완전성 검증"""
    errors = []
    depth_fields = ["depth1", "depth2", "depth3", "depth4"]

    for idx, tc in enumerate(testcases, start=1):
        tc_id = tc.get("test_case_id", f"행 {idx}")
        for field in depth_fields:
            value = tc.get(field, "").strip()
            if not value:
                errors.append(f"{tc_id}: {field} 누락")

    is_valid = len(errors) == 0
    return is_valid, errors[:10]  # 최대 10개만 표시


def validate_expected_result_format(testcases: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Expected Result 형식 검증 (# 시작)"""
    errors = []

    for idx, tc in enumerate(testcases, start=1):
        tc_id = tc.get("test_case_id", f"행 {idx}")
        expected = tc.get("expected_result", "").strip()

        if expected and not expected.startswith("#"):
            errors.append(f"{tc_id}: Expected Result '#' 누락")

    is_valid = len(errors) == 0
    return is_valid, errors[:10]


def validate_reference_format(testcases: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Reference 형식 검증 (숫자P)"""
    errors = []

    for idx, tc in enumerate(testcases, start=1):
        tc_id = tc.get("test_case_id", f"행 {idx}")
        reference = tc.get("reference", "").strip()

        if reference and not re.search(r'\d+P', reference):
            errors.append(f"{tc_id}: Reference 페이지 번호 누락 ({reference})")

    is_valid = len(errors) == 0
    return is_valid, errors[:10]


def validate_page_order(testcases: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """페이지 순서 검증"""
    errors = []
    prev_page = 0

    for idx, tc in enumerate(testcases, start=1):
        tc_id = tc.get("test_case_id", f"행 {idx}")
        reference = tc.get("reference", "")

        match = re.search(r'(\d+)P', reference)
        if match:
            page_num = int(match.group(1))
            if page_num < prev_page:
                errors.append(f"{tc_id}: 페이지 순서 역전 ({prev_page}P → {page_num}P)")
            prev_page = page_num

    is_valid = len(errors) == 0
    return is_valid, errors[:5]


def validate_test_step_quality(testcases: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Test Step 품질 검증 (단일 스텝, 위치 서술자, 진입 동작)"""
    errors = []
    total = len(testcases)
    if total == 0:
        return True, []

    single_step_count = 0
    missing_location_count = 0
    missing_entry_count = 0

    location_keywords = ["좌측", "우측", "상단", "하단", "중앙", "영역", "왼쪽", "오른쪽"]
    entry_keywords = ["진입", "화면 진입", "탭 진입", "탭 화면"]

    for idx, tc in enumerate(testcases, start=1):
        tc_id = tc.get("test_case_id", f"행 {idx}")
        test_step = tc.get("test_step", "").strip()

        if not test_step:
            continue

        # 단일 스텝 검출: "\n"이 없고 "2." 도 없으면 단일 스텝
        lines = [l.strip() for l in test_step.split("\n") if l.strip()]
        if len(lines) <= 1 and "2." not in test_step:
            single_step_count += 1

        # 위치 서술자 검출
        has_location = any(kw in test_step for kw in location_keywords)
        if not has_location:
            missing_location_count += 1

        # 진입 동작 검출
        has_entry = any(kw in test_step for kw in entry_keywords)
        if not has_entry:
            missing_entry_count += 1

    # 단일 스텝 TC 비율이 30% 초과 시 경고
    single_step_ratio = single_step_count / total if total > 0 else 0
    if single_step_ratio > 0.3:
        errors.append(
            f"단일 스텝 TC 과다: {single_step_count}개/{total}개 ({single_step_ratio:.0%}) - 목표: 0%"
        )

    # 위치 서술자 누락 비율이 30% 초과 시 경고
    missing_location_ratio = missing_location_count / total if total > 0 else 0
    if missing_location_ratio > 0.3:
        errors.append(
            f"위치 서술자 누락 과다: {missing_location_count}개/{total}개 ({missing_location_ratio:.0%}) - 목표: 30% 이하"
        )

    # 진입 동작 누락 비율이 30% 초과 시 경고
    missing_entry_ratio = missing_entry_count / total if total > 0 else 0
    if missing_entry_ratio > 0.3:
        errors.append(
            f"진입 동작 누락 과다: {missing_entry_count}개/{total}개 ({missing_entry_ratio:.0%}) - 목표: 30% 이하"
        )

    is_valid = len(errors) == 0
    return is_valid, errors


def run_validation(data: Dict[str, Any]) -> Dict[str, Any]:
    """전체 검증 실행"""
    testcases = data.get("testcases", [])

    results = {
        "total_tc": len(testcases),
        "checks": {},
        "passed": 0,
        "failed": 0,
        "errors": []
    }

    # 검증 항목 실행
    validations = [
        ("TC ID 연속성", validate_tc_id_sequence),
        ("Depth 완전성", validate_depth_completeness),
        ("Expected Result 형식", validate_expected_result_format),
        ("Reference 형식", validate_reference_format),
        ("페이지 순서", validate_page_order),
        ("Test Step 품질", validate_test_step_quality),
    ]

    for name, func in validations:
        is_valid, errors = func(testcases)
        results["checks"][name] = {
            "valid": is_valid,
            "errors": errors
        }
        if is_valid:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["errors"].extend(errors)

    results["all_passed"] = results["failed"] == 0

    return results


# ============================================================
# 통계 (Statistics) 함수들
# ============================================================

def count_by_page(testcases: List[Dict[str, Any]]) -> Dict[str, int]:
    """페이지별 TC 수"""
    page_counts = defaultdict(int)

    for tc in testcases:
        reference = tc.get("reference", "")
        match = re.search(r'(\d+)P', reference)
        if match:
            page = f"{match.group(1)}P"
            page_counts[page] += 1
        else:
            page_counts["기타"] += 1

    # 페이지 번호 순으로 정렬
    def sort_key(item):
        page = item[0]
        match = re.match(r'(\d+)', page)
        return int(match.group(1)) if match else 9999

    return dict(sorted(page_counts.items(), key=sort_key))


def count_by_test_type(testcases: List[Dict[str, Any]]) -> Dict[str, int]:
    """테스트 유형별 TC 수 (Depth4 기준)"""
    type_counts = defaultdict(int)

    for tc in testcases:
        depth4 = tc.get("depth4", "").strip()
        if depth4:
            type_counts[depth4] += 1
        else:
            type_counts["미분류"] += 1

    return dict(sorted(type_counts.items(), key=lambda x: -x[1]))


def count_by_depth1(testcases: List[Dict[str, Any]]) -> Dict[str, int]:
    """Depth1 별 TC 분포"""
    depth1_counts = defaultdict(int)

    for tc in testcases:
        depth1 = tc.get("depth1", "").strip()
        if depth1:
            depth1_counts[depth1] += 1
        else:
            depth1_counts["미분류"] += 1

    return dict(sorted(depth1_counts.items(), key=lambda x: -x[1]))


def count_cross_references(testcases: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """크로스 레퍼런스 현황"""
    cross_refs = []

    for tc in testcases:
        reference = tc.get("reference", "")
        if "(참조:" in reference or "참조:" in reference:
            tc_id = tc.get("test_case_id", "")
            cross_refs.append(f"{tc_id}: {reference}")

    return len(cross_refs), cross_refs[:10]


def count_special_tc(testcases: List[Dict[str, Any]]) -> Dict[str, int]:
    """특수 TC 현황 (단축키, 조건별 등)"""
    counts = {
        "단축키 TC": 0,
        "조건별 TC": 0,
        "Hover TC": 0
    }

    for tc in testcases:
        title = tc.get("title", "").lower()
        depth4 = tc.get("depth4", "").lower()

        if "단축키" in title or "shortcut" in title:
            counts["단축키 TC"] += 1
        if "hover" in title or "hover" in depth4:
            counts["Hover TC"] += 1
        if any(keyword in title for keyword in ["있음", "없음", "선택", "미선택"]):
            counts["조건별 TC"] += 1

    return counts


def count_step_quality_stats(testcases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test Step 품질 통계"""
    total = len(testcases)
    if total == 0:
        return {"total": 0, "avg_steps": 0, "single_step": 0, "location_included": 0, "entry_included": 0}

    step_counts = []
    single_step_count = 0
    location_count = 0
    entry_count = 0

    location_keywords = ["좌측", "우측", "상단", "하단", "중앙", "영역", "왼쪽", "오른쪽"]
    entry_keywords = ["진입", "화면 진입", "탭 진입", "탭 화면"]

    for tc in testcases:
        test_step = tc.get("test_step", "").strip()
        if not test_step:
            step_counts.append(0)
            single_step_count += 1
            continue

        lines = [l.strip() for l in test_step.split("\n") if l.strip()]
        num_steps = len(lines)
        step_counts.append(num_steps)

        if num_steps <= 1 and "2." not in test_step:
            single_step_count += 1

        if any(kw in test_step for kw in location_keywords):
            location_count += 1

        if any(kw in test_step for kw in entry_keywords):
            entry_count += 1

    avg_steps = sum(step_counts) / len(step_counts) if step_counts else 0

    return {
        "total": total,
        "avg_steps": round(avg_steps, 1),
        "single_step": single_step_count,
        "single_step_ratio": round(single_step_count / total * 100, 1) if total > 0 else 0,
        "location_included": location_count,
        "location_ratio": round(location_count / total * 100, 1) if total > 0 else 0,
        "entry_included": entry_count,
        "entry_ratio": round(entry_count / total * 100, 1) if total > 0 else 0,
    }


def generate_bar(count: int, total: int, width: int = 20) -> str:
    """막대 그래프 생성"""
    if total == 0:
        return ""
    filled = int((count / total) * width)
    return "#" * filled


def run_statistics(data: Dict[str, Any]) -> Dict[str, Any]:
    """전체 통계 실행"""
    testcases = data.get("testcases", [])
    project_info = data.get("project_info", {})

    stats = {
        "project_name": project_info.get("project_name", "Unknown"),
        "version": project_info.get("version", ""),
        "total_tc": len(testcases),
        "by_page": count_by_page(testcases),
        "by_test_type": count_by_test_type(testcases),
        "by_depth1": count_by_depth1(testcases),
        "special_tc": count_special_tc(testcases),
    }

    cross_ref_count, cross_ref_list = count_cross_references(testcases)
    stats["cross_references"] = {
        "count": cross_ref_count,
        "list": cross_ref_list
    }

    stats["step_quality"] = count_step_quality_stats(testcases)

    return stats


# ============================================================
# 출력 함수들
# ============================================================

def print_validation_results(results: Dict[str, Any]):
    """검증 결과 출력"""
    print("=" * 60)
    print("  TC 검증 결과")
    print("=" * 60)
    print(f"총 TC: {results['total_tc']}개")
    print()

    for check_name, check_result in results["checks"].items():
        status = "[PASS]" if check_result["valid"] else "[FAIL]"
        print(f"{status} {check_name}: {'정상' if check_result['valid'] else '오류 발견'}")

        if not check_result["valid"] and check_result["errors"]:
            for error in check_result["errors"][:3]:
                print(f"    - {error}")
            if len(check_result["errors"]) > 3:
                print(f"    ... 외 {len(check_result['errors']) - 3}건")

    print()
    total_checks = results["passed"] + results["failed"]
    if results["all_passed"]:
        print(f"검증 결과: [OK] 통과 ({results['passed']}/{total_checks} 항목)")
    else:
        print(f"검증 결과: [NG] 실패 ({results['passed']}/{total_checks} 항목)")


def print_statistics(stats: Dict[str, Any]):
    """통계 결과 출력"""
    print()
    print("=" * 60)
    print("  TC 통계 요약")
    print("=" * 60)
    print(f"프로젝트: {stats['project_name']} {stats['version']}")
    print(f"총 TC: {stats['total_tc']}개")

    # 페이지별 분포
    print()
    print("-" * 60)
    print("페이지별 분포")
    print("-" * 60)
    total = stats["total_tc"]
    for page, count in stats["by_page"].items():
        bar = generate_bar(count, total)
        pct = (count / total * 100) if total > 0 else 0
        print(f"{page:>6}  {bar}  {count}개 ({pct:.0f}%)")

    # 테스트 유형별 분포
    print()
    print("-" * 60)
    print("테스트 유형별 분포 (Depth4)")
    print("-" * 60)
    for test_type, count in list(stats["by_test_type"].items())[:5]:
        bar = generate_bar(count, total, 15)
        pct = (count / total * 100) if total > 0 else 0
        print(f"{test_type:<12}  {bar}  {count}개 ({pct:.0f}%)")

    # Depth1 분포
    print()
    print("-" * 60)
    print("Depth1 분포 (대분류)")
    print("-" * 60)
    for depth1, count in list(stats["by_depth1"].items())[:5]:
        bar = generate_bar(count, total, 15)
        pct = (count / total * 100) if total > 0 else 0
        # 긴 이름 자르기
        display_name = depth1[:15] + "..." if len(depth1) > 15 else depth1
        print(f"{display_name:<18}  {bar}  {count}개 ({pct:.0f}%)")

    # 특수 TC 현황
    print()
    print("-" * 60)
    print("특수 TC 현황")
    print("-" * 60)
    for tc_type, count in stats["special_tc"].items():
        print(f"{tc_type}: {count}개")

    # 크로스 레퍼런스
    cross_refs = stats["cross_references"]
    print(f"\n크로스 레퍼런스: {cross_refs['count']}건")
    if cross_refs["list"]:
        for ref in cross_refs["list"][:3]:
            print(f"  - {ref}")
        if len(cross_refs["list"]) > 3:
            print(f"  ... 외 {len(cross_refs['list']) - 3}건")

    # Test Step 품질
    sq = stats.get("step_quality", {})
    if sq and sq.get("total", 0) > 0:
        print()
        print("-" * 60)
        print("Test Step 품질")
        print("-" * 60)
        print(f"TC당 평균 단계 수: {sq['avg_steps']}단계")
        print(f"단일 스텝 TC: {sq['single_step']}개 ({sq['single_step_ratio']}%) - 목표: 0%")
        print(f"위치 서술자 포함: {sq['location_included']}개 ({sq['location_ratio']}%) - 목표: 70%+")
        print(f"진입 동작 포함: {sq['entry_included']}개 ({sq['entry_ratio']}%) - 목표: 70%+")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_and_stats.py <tc_data.json> [--validate-only] [--stats-only]")
        sys.exit(1)

    tc_data_path = Path(sys.argv[1])

    # 옵션 파싱
    validate_only = "--validate-only" in sys.argv
    stats_only = "--stats-only" in sys.argv

    if not tc_data_path.exists():
        print(f"Error: File not found: {tc_data_path}")
        sys.exit(1)

    # 데이터 로드 (한 번만)
    data = load_tc_data(tc_data_path)

    # 검증 실행
    if not stats_only:
        validation_results = run_validation(data)
        print_validation_results(validation_results)

    # 통계 실행
    if not validate_only:
        stats = run_statistics(data)
        print_statistics(stats)

    # 검증 실패 시 종료 코드 1
    if not stats_only and not validation_results["all_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
