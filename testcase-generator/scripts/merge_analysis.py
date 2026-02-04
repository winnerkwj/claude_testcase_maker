#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이미지 분석 결과 병합 유틸리티

Claude Code가 분석한 이미지 결과를 텍스트 추출 데이터와 병합합니다.

워크플로우:
1. extract_pptx.py로 추출한 extracted_data.json
2. Claude Code가 생성한 image_analysis.json
3. merge_analysis.py로 병합 → merged_data.json

병합 로직:
- 컴포넌트명으로 매칭
- 시각적 위치/상태 정보 추가
- 이미지에서만 발견된 요소 추가

사용법:
    py merge_analysis.py extracted.json image_analysis.json --output merged.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def normalize_component_name(name: str) -> str:
    """컴포넌트 이름 정규화 (매칭용)

    - 공백 제거
    - 소문자 변환
    - 일반적인 접미사 제거
    """
    if not name:
        return ""

    normalized = name.lower().strip()

    # 접미사 제거
    suffixes = ["button", "btn", "버튼", "input", "field", "필드",
                "list", "목록", "area", "영역", "popup", "팝업"]
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()

    # 특수문자 제거
    normalized = normalized.replace("_", "").replace("-", "").replace(" ", "")

    return normalized


def find_matching_component(
    visual_element: dict,
    components: List[dict]
) -> Tuple[Optional[dict], float]:
    """시각적 요소와 매칭되는 컴포넌트 찾기

    Args:
        visual_element: 이미지 분석에서 추출한 UI 요소
        components: 텍스트에서 추출한 컴포넌트 목록

    Returns:
        (매칭된 컴포넌트, 신뢰도 점수)
    """
    element_name = visual_element.get("label", "") or visual_element.get("name", "")
    element_type = visual_element.get("type", "")
    normalized_element = normalize_component_name(element_name)

    best_match = None
    best_score = 0.0

    for component in components:
        comp_name = component.get("component", "")
        normalized_comp = normalize_component_name(comp_name)

        score = 0.0

        # 이름 매칭
        if normalized_element and normalized_comp:
            # 완전 일치
            if normalized_element == normalized_comp:
                score = 1.0
            # 포함 관계
            elif normalized_element in normalized_comp or normalized_comp in normalized_element:
                score = 0.7
            # 부분 일치 (첫 단어)
            elif normalized_element.split()[0] == normalized_comp.split()[0] if normalized_element.split() and normalized_comp.split() else False:
                score = 0.5

        # 타입 매칭 보너스
        comp_desc = component.get("description", "").lower()
        if element_type:
            type_keywords = {
                "button": ["button", "btn", "버튼", "클릭"],
                "input": ["input", "field", "입력", "필드", "text"],
                "list": ["list", "table", "grid", "목록", "테이블"],
                "popup": ["popup", "modal", "dialog", "팝업", "모달"],
                "label": ["label", "text", "레이블", "텍스트"],
                "icon": ["icon", "아이콘"],
            }
            keywords = type_keywords.get(element_type.lower(), [])
            if any(kw in comp_desc for kw in keywords):
                score += 0.2

        if score > best_score:
            best_score = score
            best_match = component

    return (best_match, best_score) if best_score >= 0.5 else (None, 0.0)


def merge_visual_info(component: dict, visual_element: dict) -> dict:
    """컴포넌트에 시각적 정보 병합

    Args:
        component: 기존 컴포넌트 정보
        visual_element: 이미지에서 추출한 시각 정보

    Returns:
        병합된 컴포넌트 정보
    """
    merged = component.copy()

    # visual_info 필드 추가
    visual_info = {}

    # 위치 정보
    if "position" in visual_element:
        visual_info["position"] = visual_element["position"]

    # 상태 정보
    if "state" in visual_element:
        visual_info["state"] = visual_element["state"]

    # 크기 정보
    if "size" in visual_element:
        visual_info["size"] = visual_element["size"]

    # 스타일 정보
    if "style" in visual_element:
        visual_info["style"] = visual_element["style"]

    # 색상 정보
    if "color" in visual_element:
        visual_info["color"] = visual_element["color"]

    # 레이아웃 영역
    if "layout_area" in visual_element:
        visual_info["layout_area"] = visual_element["layout_area"]

    # 관계 정보
    if "related_elements" in visual_element:
        visual_info["related_elements"] = visual_element["related_elements"]

    # 추가 설명
    if "visual_description" in visual_element:
        visual_info["visual_description"] = visual_element["visual_description"]

    if visual_info:
        merged["visual_info"] = visual_info

    return merged


def create_component_from_visual(visual_element: dict, slide_number: int) -> dict:
    """시각 요소에서 새 컴포넌트 생성

    이미지에서만 발견된 요소를 컴포넌트로 변환

    Args:
        visual_element: 이미지에서 추출한 UI 요소
        slide_number: 슬라이드 번호

    Returns:
        새 컴포넌트 딕셔너리
    """
    element_name = visual_element.get("label", "") or visual_element.get("name", "Unknown")
    element_type = visual_element.get("type", "")

    # 타입에 따른 컴포넌트명 생성
    type_suffix_map = {
        "button": " Button",
        "input": " Input",
        "list": " List",
        "popup": " Popup",
        "label": "",
        "icon": " Icon",
    }
    suffix = type_suffix_map.get(element_type.lower(), "")
    component_name = f"{element_name}{suffix}" if not element_name.lower().endswith(element_type.lower()) else element_name

    # description 생성
    descriptions = []
    if visual_element.get("visual_description"):
        descriptions.append(visual_element["visual_description"])
    if visual_element.get("position"):
        descriptions.append(f"위치: {visual_element['position']}")
    if visual_element.get("state"):
        descriptions.append(f"상태: {visual_element['state']}")

    return {
        "no": 0,  # 나중에 재할당
        "component": component_name,
        "description": "\n".join(descriptions) if descriptions else f"{element_name} UI 요소 (이미지 분석으로 발견)",
        "slide_number": slide_number,
        "section": "",
        "source": "image_analysis",
        "visual_info": {
            "position": visual_element.get("position", ""),
            "state": visual_element.get("state", ""),
            "type": element_type,
            "size": visual_element.get("size"),
            "style": visual_element.get("style"),
        }
    }


def merge_image_analysis(
    extracted_data: dict,
    image_analysis: dict,
    add_new_elements: bool = True
) -> dict:
    """텍스트 추출 데이터 + 이미지 분석 결과 병합

    Args:
        extracted_data: extract_pptx.py의 출력
        image_analysis: Claude Code의 이미지 분석 결과
        add_new_elements: 이미지에서만 발견된 요소 추가 여부

    Returns:
        병합된 데이터
    """
    merged_data = extracted_data.copy()
    components = merged_data.get("all_components", []).copy()

    # 통계
    stats = {
        "matched": 0,
        "updated": 0,
        "added": 0,
        "unmatched_visual": 0
    }

    # 이미지별 분석 결과 처리
    for image_result in image_analysis.get("images", []):
        slide_number = image_result.get("slide_number", 0)
        elements = image_result.get("elements", [])

        for element in elements:
            # 기존 컴포넌트와 매칭 시도
            match, score = find_matching_component(element, components)

            if match:
                # 매칭 성공: 시각 정보 병합
                idx = components.index(match)
                components[idx] = merge_visual_info(match, element)
                stats["matched"] += 1
                stats["updated"] += 1
            elif add_new_elements:
                # 매칭 실패: 새 컴포넌트로 추가
                new_component = create_component_from_visual(element, slide_number)
                components.append(new_component)
                stats["added"] += 1
            else:
                stats["unmatched_visual"] += 1

    # 컴포넌트 번호 재할당
    for i, comp in enumerate(components, 1):
        if comp.get("no", 0) == 0:
            comp["no"] = i

    merged_data["all_components"] = components
    merged_data["merge_stats"] = stats
    merged_data["merge_date"] = image_analysis.get("analysis_date", "")

    return merged_data


def load_json(path: str) -> dict:
    """JSON 파일 로드"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: str):
    """JSON 파일 저장"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="이미지 분석 결과를 텍스트 추출 데이터와 병합합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  py merge_analysis.py extracted.json image_analysis.json
  py merge_analysis.py extracted.json image_analysis.json --output merged.json
  py merge_analysis.py extracted.json image_analysis.json --no-add-new
        """
    )

    parser.add_argument(
        "extracted_data",
        help="텍스트 추출 데이터 JSON 파일 (extract_pptx.py 출력)"
    )

    parser.add_argument(
        "image_analysis",
        help="이미지 분석 결과 JSON 파일 (Claude Code 출력)"
    )

    parser.add_argument(
        "--output", "-o",
        dest="output_path",
        default=None,
        help="출력 파일 경로 (기본값: merged_data.json)"
    )

    parser.add_argument(
        "--no-add-new",
        action="store_true",
        help="이미지에서만 발견된 요소를 추가하지 않음"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="간략한 출력"
    )

    args = parser.parse_args()

    try:
        # 파일 로드
        if not args.quiet:
            print("[병합] 데이터 로드 중...")

        extracted_data = load_json(args.extracted_data)
        image_analysis = load_json(args.image_analysis)

        if not args.quiet:
            print(f"  텍스트 추출: {len(extracted_data.get('all_components', []))}개 컴포넌트")
            print(f"  이미지 분석: {len(image_analysis.get('images', []))}개 이미지")

        # 병합
        if not args.quiet:
            print("[병합] 데이터 병합 중...")

        merged_data = merge_image_analysis(
            extracted_data,
            image_analysis,
            add_new_elements=not args.no_add_new
        )

        # 저장
        output_path = args.output_path or "merged_data.json"
        save_json(merged_data, output_path)

        # 결과 출력
        stats = merged_data.get("merge_stats", {})
        if not args.quiet:
            print()
            print("-" * 60)
            print("  병합 결과 요약")
            print("-" * 60)
            print(f"  매칭 성공     : {stats.get('matched', 0)}개")
            print(f"  정보 업데이트 : {stats.get('updated', 0)}개")
            print(f"  새로 추가     : {stats.get('added', 0)}개")
            print(f"  매칭 실패     : {stats.get('unmatched_visual', 0)}개")
            print(f"  총 컴포넌트   : {len(merged_data.get('all_components', []))}개")
            print(f"  출력 파일     : {output_path}")
            print("-" * 60)
        else:
            print(f"출력: {output_path}")
            print(f"컴포넌트: {len(merged_data.get('all_components', []))}개")

        return 0

    except FileNotFoundError as e:
        print(f"[오류] 파일을 찾을 수 없습니다: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 파싱 오류: {e}")
        return 1
    except Exception as e:
        print(f"[오류] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
