#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPTX 데이터를 청크로 분할하는 계획 생성 스크립트

대용량 문서 처리를 위해 페이지를 청크 단위로 분할합니다.
- 섹션 기반 그룹핑
- 15페이지 초과 섹션 분할
- 컴포넌트 80개 초과 시 추가 분할
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# 중앙 설정에서 가져오기
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from config import (
        MAX_PAGES_PER_CHUNK,
        MAX_COMPONENTS_PER_CHUNK,
        MAX_PARALLEL_AGENTS,
    )
except ImportError:
    # config.py를 찾을 수 없는 경우 기본값 사용
    MAX_PAGES_PER_CHUNK = 15
    MAX_COMPONENTS_PER_CHUNK = 80
    MAX_PARALLEL_AGENTS = 10


def load_pptx_data(pptx_data_path: Path) -> Dict[str, Any]:
    """pptx_data.json 로드"""
    with open(pptx_data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_section_for_slide(slide: Dict[str, Any]) -> str:
    """슬라이드의 섹션 제목 추출"""
    section = slide.get("section_title", "").strip()
    if not section:
        # 섹션 제목이 없으면 헤더에서 추출 시도
        header = slide.get("header", {})
        section = header.get("title", f"Page {slide.get('slide_number', 0)}")
    return section


def count_components_in_slides(slides: List[Dict[str, Any]]) -> int:
    """슬라이드 목록의 총 컴포넌트 수 계산"""
    total = 0
    for slide in slides:
        total += len(slide.get("components", []))
    return total


def group_slides_by_section(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """섹션별로 슬라이드 그룹화"""
    slides = data.get("slides", [])
    sections = []
    current_section = None
    current_slides = []

    for slide in slides:
        section_title = get_section_for_slide(slide)

        if section_title != current_section:
            if current_slides:
                sections.append({
                    "section": current_section,
                    "slides": current_slides.copy()
                })
            current_section = section_title
            current_slides = [slide]
        else:
            current_slides.append(slide)

    # 마지막 섹션 추가
    if current_slides:
        sections.append({
            "section": current_section,
            "slides": current_slides
        })

    return sections


def split_section_into_chunks(section: Dict[str, Any], max_pages: int, max_components: int) -> List[Dict[str, Any]]:
    """큰 섹션을 서브청크로 분할"""
    slides = section["slides"]
    section_title = section["section"]

    if len(slides) <= max_pages:
        component_count = count_components_in_slides(slides)
        if component_count <= max_components:
            return [section]

    # 분할 필요
    chunks = []
    current_chunk_slides = []
    current_component_count = 0
    chunk_index = 1

    for slide in slides:
        slide_components = len(slide.get("components", []))

        # 현재 청크가 한계에 도달했는지 확인
        would_exceed_pages = len(current_chunk_slides) >= max_pages
        would_exceed_components = (current_component_count + slide_components) > max_components

        if current_chunk_slides and (would_exceed_pages or would_exceed_components):
            # 현재 청크 저장
            chunks.append({
                "section": f"{section_title} (Part {chunk_index})",
                "slides": current_chunk_slides.copy()
            })
            current_chunk_slides = []
            current_component_count = 0
            chunk_index += 1

        current_chunk_slides.append(slide)
        current_component_count += slide_components

    # 마지막 청크 저장
    if current_chunk_slides:
        if chunk_index > 1:
            chunks.append({
                "section": f"{section_title} (Part {chunk_index})",
                "slides": current_chunk_slides
            })
        else:
            chunks.append({
                "section": section_title,
                "slides": current_chunk_slides
            })

    return chunks


def create_chunk_plan(data: Dict[str, Any], max_pages: int = MAX_PAGES_PER_CHUNK) -> Dict[str, Any]:
    """청크 분할 계획 생성"""
    # 섹션별 그룹화
    sections = group_slides_by_section(data)

    # 각 섹션을 필요 시 분할
    all_chunks = []
    for section in sections:
        chunks = split_section_into_chunks(section, max_pages, MAX_COMPONENTS_PER_CHUNK)
        all_chunks.extend(chunks)

    # 청크 병합 (작은 청크들을 합쳐서 효율성 향상)
    merged_chunks = merge_small_chunks(all_chunks, max_pages, MAX_COMPONENTS_PER_CHUNK)

    # 최종 청크 계획 생성
    chunk_plan = {
        "source_file": data.get("file_path", ""),
        "total_slides": data.get("total_slides", 0),
        "total_chunks": len(merged_chunks),
        "max_pages_per_chunk": max_pages,
        "max_components_per_chunk": MAX_COMPONENTS_PER_CHUNK,
        "project_info": data.get("project_info", {}),
        "chunks": []
    }

    for idx, chunk in enumerate(merged_chunks, start=1):
        slide_numbers = [s.get("slide_number", 0) for s in chunk["slides"]]
        component_count = count_components_in_slides(chunk["slides"])

        chunk_info = {
            "id": idx,
            "section": chunk["section"],
            "slides": slide_numbers,
            "slide_range": [min(slide_numbers), max(slide_numbers)] if slide_numbers else [0, 0],
            "page_count": len(slide_numbers),
            "component_count": component_count
        }
        chunk_plan["chunks"].append(chunk_info)

    return chunk_plan


def merge_small_chunks(chunks: List[Dict[str, Any]], max_pages: int, max_components: int) -> List[Dict[str, Any]]:
    """작은 청크들을 병합하여 효율성 향상"""
    if not chunks:
        return []

    merged = []
    current = {
        "section": chunks[0]["section"],
        "slides": chunks[0]["slides"].copy()
    }

    for chunk in chunks[1:]:
        current_pages = len(current["slides"])
        current_components = count_components_in_slides(current["slides"])
        new_pages = len(chunk["slides"])
        new_components = count_components_in_slides(chunk["slides"])

        # 병합 가능 여부 확인
        can_merge = (
            (current_pages + new_pages) <= max_pages and
            (current_components + new_components) <= max_components
        )

        if can_merge:
            # 병합
            current["slides"].extend(chunk["slides"])
            # 섹션명 업데이트 (여러 섹션 병합 시)
            if chunk["section"] != current["section"]:
                current["section"] = f"{current['section']} + {chunk['section']}"
        else:
            # 현재 청크 저장하고 새로 시작
            merged.append(current)
            current = {
                "section": chunk["section"],
                "slides": chunk["slides"].copy()
            }

    # 마지막 청크 저장
    merged.append(current)

    return merged


def save_chunk_plan(chunk_plan: Dict[str, Any], output_path: Path):
    """청크 계획 저장"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunk_plan, f, ensure_ascii=False, indent=2)


def print_chunk_summary(chunk_plan: Dict[str, Any]):
    """청크 계획 요약 출력"""
    print("=" * 60)
    print("  청크 분할 계획")
    print("=" * 60)
    print(f"총 슬라이드: {chunk_plan['total_slides']}페이지")
    print(f"총 청크: {chunk_plan['total_chunks']}개")
    print(f"청크당 최대 페이지: {chunk_plan['max_pages_per_chunk']}페이지")
    print("-" * 60)

    for chunk in chunk_plan["chunks"]:
        print(f"Chunk {chunk['id']}:")
        print(f"  섹션: {chunk['section']}")
        print(f"  슬라이드: {chunk['slide_range'][0]}P ~ {chunk['slide_range'][1]}P ({chunk['page_count']}페이지)")
        print(f"  컴포넌트: {chunk['component_count']}개")

    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python plan_chunks.py <pptx_data.json> [--max-pages N] [--output <path>]")
        sys.exit(1)

    pptx_data_path = Path(sys.argv[1])

    # 옵션 파싱
    max_pages = MAX_PAGES_PER_CHUNK
    output_path = pptx_data_path.parent / "chunk_plan.json"

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--max-pages" and i + 1 < len(args):
            max_pages = int(args[i + 1])
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            i += 1

    if not pptx_data_path.exists():
        print(f"Error: File not found: {pptx_data_path}")
        sys.exit(1)

    # pptx_data.json 로드
    data = load_pptx_data(pptx_data_path)

    # 청크 계획 생성
    chunk_plan = create_chunk_plan(data, max_pages)

    # 저장
    save_chunk_plan(chunk_plan, output_path)

    # 요약 출력
    print_chunk_summary(chunk_plan)
    print(f"\n청크 계획 저장: {output_path}")

    return chunk_plan


if __name__ == "__main__":
    main()
