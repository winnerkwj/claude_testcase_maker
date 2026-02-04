#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
테스트 설계 기법 지원 모듈

지원 기법:
- 2-wise (Pairwise) 조합 테스트
- 동등분할 (Equivalence Partitioning)
- 조합 테스트 (Combinatorial Testing)
"""

from typing import List, Dict, Tuple, Any
from itertools import combinations, product
from dataclasses import dataclass


@dataclass
class TestCondition:
    """테스트 조건 데이터 클래스"""
    name: str           # 조건명 (예: "환자 유형")
    values: List[str]   # 가능한 값 목록 (예: ["신환", "재진", "응급"])
    is_valid: List[bool] = None  # 각 값의 유효성 (동등분할용)

    def __post_init__(self):
        if self.is_valid is None:
            self.is_valid = [True] * len(self.values)


@dataclass
class TestCombination:
    """테스트 조합 결과 데이터 클래스"""
    conditions: Dict[str, str]  # {조건명: 값}
    test_type: str = "normal"   # normal, boundary, invalid
    description: str = ""


def generate_pairwise_combinations(conditions: List[TestCondition]) -> List[TestCombination]:
    """2-wise (Pairwise) 조합 테스트 생성

    모든 조건 쌍의 값 조합이 최소 1번 이상 나타나도록 테스트 조합 생성.
    전체 조합보다 훨씬 적은 수로 높은 결함 발견율 달성.

    Args:
        conditions: 테스트 조건 목록

    Returns:
        2-wise 조합된 테스트케이스 목록
    """
    if len(conditions) < 2:
        # 조건이 2개 미만이면 전체 조합 반환
        return _all_combinations(conditions)

    result = []
    covered_pairs = set()

    # 모든 조건 쌍에 대해 커버해야 할 값 쌍 계산
    uncovered_pairs = []
    for i, cond1 in enumerate(conditions):
        for j, cond2 in enumerate(conditions):
            if i < j:
                for v1 in cond1.values:
                    for v2 in cond2.values:
                        uncovered_pairs.append((i, j, v1, v2))

    # Greedy 알고리즘으로 조합 생성
    while uncovered_pairs:
        best_combo = None
        best_coverage = 0

        # 모든 가능한 조합 중 가장 많은 쌍을 커버하는 것 선택
        all_values = [cond.values for cond in conditions]
        for combo in product(*all_values):
            coverage = 0
            for i, j, v1, v2 in uncovered_pairs:
                if combo[i] == v1 and combo[j] == v2:
                    coverage += 1

            if coverage > best_coverage:
                best_coverage = coverage
                best_combo = combo

        if best_combo is None:
            break

        # 선택된 조합 추가
        combo_dict = {cond.name: best_combo[i] for i, cond in enumerate(conditions)}
        result.append(TestCombination(
            conditions=combo_dict,
            test_type="normal",
            description="Pairwise 조합"
        ))

        # 커버된 쌍 제거
        uncovered_pairs = [
            (i, j, v1, v2) for (i, j, v1, v2) in uncovered_pairs
            if not (best_combo[i] == v1 and best_combo[j] == v2)
        ]

    return result


def generate_equivalence_partitions(
    condition_name: str,
    valid_values: List[str],
    invalid_values: List[str] = None
) -> List[TestCombination]:
    """동등분할 테스트 생성

    유효/무효 파티션별로 대표값 선택하여 테스트케이스 생성.

    Args:
        condition_name: 조건명
        valid_values: 유효한 값 목록 (각 파티션의 대표값)
        invalid_values: 무효한 값 목록 (각 파티션의 대표값)

    Returns:
        동등분할 테스트케이스 목록
    """
    result = []

    # 유효 파티션 테스트케이스
    for value in valid_values:
        result.append(TestCombination(
            conditions={condition_name: value},
            test_type="normal",
            description=f"유효 파티션: {value}"
        ))

    # 무효 파티션 테스트케이스
    if invalid_values:
        for value in invalid_values:
            result.append(TestCombination(
                conditions={condition_name: value},
                test_type="invalid",
                description=f"무효 파티션: {value}"
            ))

    return result


def generate_boundary_values(
    condition_name: str,
    min_value: Any,
    max_value: Any,
    include_invalid: bool = True
) -> List[TestCombination]:
    """경계값 분석 테스트 생성

    최소/최대 경계값과 그 주변값으로 테스트케이스 생성.

    Args:
        condition_name: 조건명
        min_value: 최소값
        max_value: 최대값
        include_invalid: 무효 경계값 포함 여부

    Returns:
        경계값 테스트케이스 목록
    """
    result = []

    # 정수형 경계값 처리
    if isinstance(min_value, int) and isinstance(max_value, int):
        # 유효 경계값
        valid_boundaries = [min_value, min_value + 1, max_value - 1, max_value]
        for value in valid_boundaries:
            if min_value <= value <= max_value:
                result.append(TestCombination(
                    conditions={condition_name: str(value)},
                    test_type="boundary",
                    description=f"유효 경계값: {value}"
                ))

        # 무효 경계값
        if include_invalid:
            invalid_boundaries = [min_value - 1, max_value + 1]
            for value in invalid_boundaries:
                result.append(TestCombination(
                    conditions={condition_name: str(value)},
                    test_type="invalid",
                    description=f"무효 경계값: {value}"
                ))
    else:
        # 문자열/기타 경계값
        result.append(TestCombination(
            conditions={condition_name: str(min_value)},
            test_type="boundary",
            description=f"최소 경계값: {min_value}"
        ))
        result.append(TestCombination(
            conditions={condition_name: str(max_value)},
            test_type="boundary",
            description=f"최대 경계값: {max_value}"
        ))

    return result


def generate_all_combinations(conditions: List[TestCondition]) -> List[TestCombination]:
    """전체 조합 테스트 생성 (모든 값 조합)

    주의: 조건/값이 많으면 조합 수가 폭발적으로 증가함.
    조건 3개 이하, 값 4개 이하 권장.

    Args:
        conditions: 테스트 조건 목록

    Returns:
        전체 조합 테스트케이스 목록
    """
    return _all_combinations(conditions)


def _all_combinations(conditions: List[TestCondition]) -> List[TestCombination]:
    """내부 헬퍼: 전체 조합 생성"""
    if not conditions:
        return []

    result = []
    all_values = [cond.values for cond in conditions]

    for combo in product(*all_values):
        combo_dict = {cond.name: combo[i] for i, cond in enumerate(conditions)}
        result.append(TestCombination(
            conditions=combo_dict,
            test_type="normal",
            description="전체 조합"
        ))

    return result


def generate_state_transition_tests(
    states: List[str],
    valid_transitions: List[Tuple[str, str, str]]
) -> List[TestCombination]:
    """상태 전이 테스트 생성

    Args:
        states: 상태 목록
        valid_transitions: 유효 전이 목록 [(시작상태, 이벤트, 종료상태), ...]

    Returns:
        상태 전이 테스트케이스 목록
    """
    result = []

    for from_state, event, to_state in valid_transitions:
        result.append(TestCombination(
            conditions={
                "시작상태": from_state,
                "이벤트": event,
                "종료상태": to_state
            },
            test_type="normal",
            description=f"상태 전이: {from_state} --[{event}]--> {to_state}"
        ))

    return result


def combinations_to_testcase_data(
    combinations: List[TestCombination],
    base_title: str,
    base_precondition: str = "",
    base_step_prefix: str = ""
) -> List[Dict]:
    """조합 결과를 테스트케이스 데이터 형식으로 변환

    Args:
        combinations: 테스트 조합 목록
        base_title: 기본 Title
        base_precondition: 기본 Pre-condition
        base_step_prefix: Test Step 접두사

    Returns:
        테스트케이스 딕셔너리 목록
    """
    testcases = []

    for i, combo in enumerate(combinations, 1):
        # 조건값을 Test Step으로 변환
        condition_steps = "\n".join([
            f"- {name}: {value}"
            for name, value in combo.conditions.items()
        ])

        # 테스트 유형에 따른 Expected Result
        if combo.test_type == "invalid":
            expected = "# 오류 메시지 표시 또는 입력 거부됨"
        elif combo.test_type == "boundary":
            expected = "# 경계값 정상 처리됨"
        else:
            expected = "# 정상 동작"

        tc_data = {
            "title": f"{base_title} - 조합 {i}",
            "pre_condition": base_precondition or combo.description,
            "test_step": f"{base_step_prefix}\n조건:\n{condition_steps}",
            "expected_result": expected,
            "test_type": combo.test_type,
            "description": combo.description
        }

        testcases.append(tc_data)

    return testcases


# ===== 사용 예시 =====

def example_pairwise():
    """Pairwise 사용 예시"""
    conditions = [
        TestCondition("브라우저", ["Chrome", "Firefox", "Safari", "Edge"]),
        TestCondition("OS", ["Windows", "macOS", "Linux"]),
        TestCondition("해상도", ["1920x1080", "1366x768", "2560x1440"]),
    ]

    combos = generate_pairwise_combinations(conditions)
    print(f"Pairwise 결과: {len(combos)}개 조합 (전체 조합: {4*3*3}=36개)")

    for i, combo in enumerate(combos, 1):
        print(f"  {i}. {combo.conditions}")


def example_equivalence():
    """동등분할 사용 예시"""
    combos = generate_equivalence_partitions(
        condition_name="나이",
        valid_values=["25", "50", "75"],  # 유효 파티션 대표값
        invalid_values=["-1", "150", "abc"]  # 무효 파티션 대표값
    )

    print(f"동등분할 결과: {len(combos)}개")
    for combo in combos:
        print(f"  - {combo.conditions}: {combo.test_type} ({combo.description})")


def example_boundary():
    """경계값 분석 사용 예시"""
    combos = generate_boundary_values(
        condition_name="수량",
        min_value=1,
        max_value=100,
        include_invalid=True
    )

    print(f"경계값 결과: {len(combos)}개")
    for combo in combos:
        print(f"  - {combo.conditions}: {combo.test_type} ({combo.description})")


if __name__ == "__main__":
    print("=== Pairwise 예시 ===")
    example_pairwise()
    print()

    print("=== 동등분할 예시 ===")
    example_equivalence()
    print()

    print("=== 경계값 분석 예시 ===")
    example_boundary()
