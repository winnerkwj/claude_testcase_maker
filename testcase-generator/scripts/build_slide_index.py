#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pptx_data.json에서 컴팩트 슬라이드 인덱스를 생성하는 스크립트

Reference 매핑 에이전트가 빠르게 후보 슬라이드를 찾을 수 있도록
슬라이드당 핵심 정보(섹션, 컴포넌트명, 키워드)를 추출하고
역방향 인덱스(keyword → slides, section → slides)를 구축합니다.

출력: slide_index.json (~100KB 이하)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict

# 중앙 설정에서 가져오기
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from config import OUTPUT_DIR
except ImportError:
    OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


# 불용어 (키워드 인덱스에서 제외)
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "this", "that", "it", "and", "or", "not", "no", "yes",
    "의", "를", "을", "에", "에서", "으로", "로", "와", "과",
    "이", "가", "은", "는", "도", "만", "등", "및", "또는",
    "시", "때", "경우", "위해", "통해", "대한", "해당",
}


def normalize_keyword(word: str) -> str:
    """키워드 정규화 (소문자, 특수문자 제거)"""
    word = word.lower().strip()
    word = re.sub(r'[^\w\s가-힣]', '', word)
    return word.strip()


def extract_keywords(text: str) -> Set[str]:
    """텍스트에서 의미 있는 키워드 추출"""
    if not text:
        return set()

    keywords = set()
    # 공백/특수문자 기준 토큰화
    tokens = re.split(r'[\s,./\-_()[\]{}:;|]+', text)

    for token in tokens:
        normalized = normalize_keyword(token)
        if not normalized:
            continue
        if len(normalized) < 2:
            continue
        if normalized in STOP_WORDS:
            continue
        keywords.add(normalized)

    return keywords


def extract_screen_id(slide: Dict[str, Any]) -> str:
    """슬라이드에서 화면 ID 추출 (SCR-XXX, Screen-XXX 등)"""
    header = slide.get("header", {})
    title = header.get("title", "")
    section = slide.get("section_title", "")

    for text in [title, section]:
        if not text:
            continue
        match = re.search(r'(SCR[-_]\d+|Screen[-_]\d+|화면[-_]?\d+)', text, re.IGNORECASE)
        if match:
            return match.group(1)

    return ""


def build_slide_entry(slide: Dict[str, Any]) -> Dict[str, Any]:
    """단일 슬라이드의 컴팩트 인덱스 엔트리 생성"""
    slide_num = slide.get("slide_number", 0)
    section_title = slide.get("section_title", "").strip()
    header = slide.get("header", {})
    header_title = header.get("title", "").strip()
    screen_id = extract_screen_id(slide)
    components = slide.get("components", [])

    # 컴포넌트명 목록
    component_names = []
    all_keywords = set()
    description_snippets = []

    for comp in components:
        comp_name = comp.get("component", "").strip()
        if comp_name:
            component_names.append(comp_name)
            all_keywords.update(extract_keywords(comp_name))

        desc = comp.get("description", "").strip()
        if desc:
            # 설명의 첫 80자만 스니펫으로 저장
            snippet = desc[:80].replace("\n", " ")
            description_snippets.append(snippet)
            all_keywords.update(extract_keywords(desc))

    # 섹션/헤더 키워드도 추가
    all_keywords.update(extract_keywords(section_title))
    all_keywords.update(extract_keywords(header_title))

    return {
        "section_title": section_title,
        "header_title": header_title,
        "screen_id": screen_id,
        "component_names": component_names,
        "description_snippets": description_snippets[:5],  # 최대 5개
        "keywords": sorted(all_keywords),
        "component_count": len(components),
    }


def build_keyword_index(slides_index: Dict[str, Dict]) -> Dict[str, List[int]]:
    """역방향 키워드 인덱스 구축 (keyword → [slide_numbers])"""
    keyword_map = defaultdict(set)

    for slide_num_str, entry in slides_index.items():
        slide_num = int(slide_num_str)
        for kw in entry.get("keywords", []):
            keyword_map[kw].add(slide_num)

    # set → sorted list
    return {kw: sorted(slides) for kw, slides in keyword_map.items()}


def build_section_map(slides_index: Dict[str, Dict]) -> Dict[str, List[int]]:
    """섹션 → 슬라이드 번호 매핑 구축"""
    section_map = defaultdict(list)

    for slide_num_str, entry in slides_index.items():
        section = entry.get("section_title", "")
        if section:
            section_map[section].append(int(slide_num_str))

    # 정렬
    return {sec: sorted(slides) for sec, slides in section_map.items()}


def build_slide_index(
    pptx_data_path: Path,
    output_path: Path = None,
) -> Dict[str, Any]:
    """슬라이드 인덱스 생성 메인 함수"""
    print("=" * 60)
    print("  슬라이드 인덱스 생성")
    print("=" * 60)

    # pptx_data 로드
    print("\npptx_data 로딩...")
    with open(pptx_data_path, "r", encoding="utf-8") as f:
        pptx_data = json.load(f)

    slides = pptx_data.get("slides", [])
    print(f"  총 {len(slides)}개 슬라이드")

    # 슬라이드별 인덱스 엔트리 생성
    print("슬라이드 인덱스 구축...")
    slides_index = {}
    for slide in slides:
        slide_num = slide.get("slide_number", 0)
        slides_index[str(slide_num)] = build_slide_entry(slide)

    # 역방향 인덱스 구축
    print("키워드 인덱스 구축...")
    keyword_index = build_keyword_index(slides_index)
    print(f"  총 {len(keyword_index)}개 키워드")

    print("섹션 맵 구축...")
    section_map = build_section_map(slides_index)
    print(f"  총 {len(section_map)}개 섹션")

    # 결과 구성
    result = {
        "total_slides": len(slides),
        "slides": slides_index,
        "keyword_index": keyword_index,
        "section_map": section_map,
    }

    # 저장
    if output_path is None:
        output_path = pptx_data_path.parent / "slide_index.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 파일 크기 확인
    file_size_kb = output_path.stat().st_size / 1024
    print(f"\n인덱스 생성 완료: {output_path}")
    print(f"  파일 크기: {file_size_kb:.1f}KB")
    print(f"  슬라이드: {len(slides_index)}개")
    print(f"  키워드: {len(keyword_index)}개")
    print(f"  섹션: {len(section_map)}개")
    print("=" * 60)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_slide_index.py <pptx_data.json> [options]")
        print()
        print("Options:")
        print("  --output <path>   출력 파일 경로 (기본: output/slide_index.json)")
        sys.exit(1)

    pptx_data_path = Path(sys.argv[1])

    # 옵션 파싱
    output_path = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            i += 1

    if not pptx_data_path.exists():
        print(f"Error: File not found: {pptx_data_path}")
        sys.exit(1)

    build_slide_index(pptx_data_path, output_path)


if __name__ == "__main__":
    main()
