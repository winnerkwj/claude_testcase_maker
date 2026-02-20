#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TC 플래닝 사전 분석 스크립트

pptx_data.json + image_manifest.json + chunk_plan.json에서
결정적(deterministic) 데이터를 추출하여 TC 플래닝 에이전트에 제공합니다.

출력: pre_analysis_raw.json
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 중앙 설정에서 가져오기
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from config import OUTPUT_DIR
except ImportError:
    OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


def load_json(path: Path) -> Dict[str, Any]:
    """JSON 파일 로드"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_cross_references(slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Description에서 크로스 레퍼런스 패턴 추출

    [번호-번호], p.XX, XX페이지 참조 등의 패턴을 찾아 매핑합니다.
    """
    cross_refs = []
    # 패턴: [11-1], [번호-번호], p.XX, XX페이지
    patterns = [
        (r'\[(\d+)-(\d+)\]', 'bracket_ref'),      # [11-1]
        (r'\[(\d+)\]', 'bracket_single'),           # [11]
        (r'[pP]\.?\s*(\d+)', 'page_ref'),           # p.11, P.11, p 11
        (r'(\d+)\s*페이지\s*참[고조]', 'korean_ref'),  # 11페이지 참고/참조
    ]

    for slide in slides:
        slide_num = slide.get("slide_number", 0)
        components = slide.get("components", [])

        for comp in components:
            desc = comp.get("description", "")
            if not desc:
                continue

            for pattern, ref_type in patterns:
                for match in re.finditer(pattern, desc):
                    ref_entry = {
                        "source_slide": slide_num,
                        "component": comp.get("component", ""),
                        "ref_type": ref_type,
                        "match_text": match.group(0),
                        "description_snippet": desc[:100]
                    }
                    if ref_type == 'bracket_ref':
                        ref_entry["ref_id"] = f"[{match.group(1)}-{match.group(2)}]"
                    elif ref_type == 'bracket_single':
                        ref_entry["ref_id"] = f"[{match.group(1)}]"
                    elif ref_type in ('page_ref', 'korean_ref'):
                        ref_entry["ref_page"] = int(match.group(1))

                    cross_refs.append(ref_entry)

    return cross_refs


def build_section_structure(slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """섹션별 슬라이드/컴포넌트 요약 구축"""
    sections = []
    current_section = None
    current_slides = []

    for slide in slides:
        section_title = slide.get("section_title", "").strip()
        if not section_title:
            header = slide.get("header", {})
            section_title = header.get("title", f"Page {slide.get('slide_number', 0)}")

        if section_title != current_section:
            if current_slides:
                sections.append({
                    "section_title": current_section,
                    "slides": current_slides
                })
            current_section = section_title
            current_slides = []

        slide_num = slide.get("slide_number", 0)
        components = slide.get("components", [])
        comp_summary = []

        for comp in components:
            comp_name = comp.get("component", "")
            desc = comp.get("description", "")
            comp_summary.append({
                "name": comp_name,
                "has_description": bool(desc and desc.strip()),
                "description_length": len(desc) if desc else 0,
                "source": comp.get("source", "table")
            })

        current_slides.append({
            "slide_number": slide_num,
            "header_title": slide.get("header", {}).get("title", ""),
            "component_count": len(components),
            "components": comp_summary
        })

    # 마지막 섹션
    if current_slides:
        sections.append({
            "section_title": current_section,
            "slides": current_slides
        })

    return sections


def suggest_depth_structure(slides: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """섹션 제목에서 Depth2/3 후보 추출

    각 슬라이드별로 pptx_data에서 추출 가능한 Depth 후보를 제시합니다.
    최종 결정은 TC 플래닝 에이전트가 이미지를 보고 합니다.
    """
    depth_suggestions = {}

    for slide in slides:
        slide_num = str(slide.get("slide_number", 0))
        section_title = slide.get("section_title", "").strip()
        header = slide.get("header", {})
        header_title = header.get("title", "")

        # 섹션 제목에서 번호 제거
        clean_section = re.sub(r'^\d+[\.\-\s]+', '', section_title).strip()

        depth_suggestions[slide_num] = {
            "raw_section_title": section_title,
            "raw_header_title": header_title,
            "depth2_candidate": clean_section if clean_section else header_title,
            "depth3_candidates": []
        }

        # 컴포넌트에서 Depth3 후보 추출 (그룹핑 키워드)
        seen_groups = set()
        for comp in slide.get("components", []):
            comp_name = comp.get("component", "")
            # [그룹명] 패턴에서 추출
            group_match = re.match(r'\[([^\]]+)\]', comp_name)
            if group_match:
                group = group_match.group(1)
                if group not in seen_groups:
                    seen_groups.add(group)
                    depth_suggestions[slide_num]["depth3_candidates"].append(group)

    return depth_suggestions


def build_image_inventory(
    manifest: Optional[Dict[str, Any]],
    slides: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """슬라이드별 이미지 목록 정리"""
    inventory = {}

    if not manifest:
        # manifest 없으면 빈 목록 반환
        for slide in slides:
            slide_num = str(slide.get("slide_number", 0))
            inventory[slide_num] = {
                "fullpage": None,
                "individual_images": [],
                "total_images": 0
            }
        return inventory

    # fullpage 이미지 매핑
    fullpage_map = {}
    for fp in manifest.get("fullpage_images", []):
        slide_num = fp.get("slide_number", 0)
        fullpage_map[str(slide_num)] = fp.get("filename", "")

    # 개별 이미지 매핑
    individual_map = {}
    for img in manifest.get("images", []):
        slide_num = str(img.get("slide_number", 0))
        if slide_num not in individual_map:
            individual_map[slide_num] = []
        individual_map[slide_num].append(img.get("filename", ""))

    for slide in slides:
        slide_num = str(slide.get("slide_number", 0))
        fp = fullpage_map.get(slide_num)
        indiv = individual_map.get(slide_num, [])
        inventory[slide_num] = {
            "fullpage": fp,
            "individual_images": indiv,
            "total_images": (1 if fp else 0) + len(indiv)
        }

    return inventory


def build_chunk_summaries(
    chunk_plan: Optional[Dict[str, Any]],
    slides: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """청크별 핵심 컴포넌트 목록"""
    if not chunk_plan:
        return []

    # 슬라이드 번호 → 슬라이드 데이터 매핑
    slide_map = {s.get("slide_number", 0): s for s in slides}

    summaries = []
    for chunk in chunk_plan.get("chunks", []):
        chunk_id = chunk.get("id", 0)
        chunk_slides = chunk.get("slides", [])

        key_components = []
        for sn in chunk_slides:
            slide = slide_map.get(sn, {})
            for comp in slide.get("components", []):
                comp_name = comp.get("component", "")
                if comp_name:
                    key_components.append(comp_name)

        summaries.append({
            "chunk_id": chunk_id,
            "section": chunk.get("section", ""),
            "slides": chunk_slides,
            "slide_range": chunk.get("slide_range", [0, 0]),
            "component_count": chunk.get("component_count", 0),
            "key_components": key_components[:20]  # 상위 20개만
        })

    return summaries


def run_pre_analysis(
    pptx_data_path: Path,
    manifest_path: Optional[Path] = None,
    chunk_plan_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """사전 분석 실행"""
    print("=" * 60)
    print("  TC 플래닝 사전 분석")
    print("=" * 60)

    # 데이터 로드
    print("\n데이터 로딩...")
    pptx_data = load_json(pptx_data_path)
    slides = pptx_data.get("slides", [])
    print(f"  pptx_data: {len(slides)}개 슬라이드")

    manifest = None
    if manifest_path and manifest_path.exists():
        manifest = load_json(manifest_path)
        print(f"  image_manifest: 로드 완료")
    else:
        print(f"  image_manifest: 없음 (이미지 인벤토리 비활성)")

    chunk_plan = None
    if chunk_plan_path and chunk_plan_path.exists():
        chunk_plan = load_json(chunk_plan_path)
        print(f"  chunk_plan: {chunk_plan.get('total_chunks', 0)}개 청크")
    else:
        print(f"  chunk_plan: 없음 (청크 요약 비활성)")

    # 분석 실행
    print("\n분석 중...")

    print("  1/5 크로스 레퍼런스 추출...")
    cross_refs = extract_cross_references(slides)
    print(f"      → {len(cross_refs)}건 발견")

    print("  2/5 섹션 구조 분석...")
    section_structure = build_section_structure(slides)
    print(f"      → {len(section_structure)}개 섹션")

    print("  3/5 Depth 구조 후보 추출...")
    depth_suggestions = suggest_depth_structure(slides)
    print(f"      → {len(depth_suggestions)}개 슬라이드 분석")

    print("  4/5 이미지 인벤토리 구축...")
    image_inventory = build_image_inventory(manifest, slides)
    total_images = sum(v["total_images"] for v in image_inventory.values())
    print(f"      → 총 {total_images}개 이미지")

    print("  5/5 청크 요약 구축...")
    chunk_summaries = build_chunk_summaries(chunk_plan, slides)
    print(f"      → {len(chunk_summaries)}개 청크 요약")

    # 결과 구성
    result = {
        "version": "1.0",
        "source": str(pptx_data_path),
        "project_info": pptx_data.get("project_info", {}),
        "total_slides": len(slides),
        "cross_references": cross_refs,
        "section_structure": section_structure,
        "depth_suggestions": depth_suggestions,
        "image_inventory": image_inventory,
        "chunk_summaries": chunk_summaries
    }

    # 저장
    if output_path is None:
        output_path = pptx_data_path.parent / "pre_analysis_raw.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n사전 분석 완료: {output_path}")
    print("=" * 60)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python pre_analyze.py <pptx_data.json> [options]")
        print()
        print("Options:")
        print("  --manifest <path>     image_manifest.json 경로")
        print("  --chunk-plan <path>   chunk_plan.json 경로")
        print("  --output <path>       출력 파일 경로")
        sys.exit(1)

    pptx_data_path = Path(sys.argv[1])

    # 옵션 파싱
    manifest_path = None
    chunk_plan_path = None
    output_path = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--manifest" and i + 1 < len(args):
            manifest_path = Path(args[i + 1])
            i += 2
        elif args[i] == "--chunk-plan" and i + 1 < len(args):
            chunk_plan_path = Path(args[i + 1])
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])
            i += 2
        else:
            i += 1

    if not pptx_data_path.exists():
        print(f"Error: File not found: {pptx_data_path}")
        sys.exit(1)

    # 기본 경로 설정 (같은 디렉토리에서 찾기)
    parent_dir = pptx_data_path.parent
    if manifest_path is None:
        manifest_path = parent_dir / "image_manifest.json"
    if chunk_plan_path is None:
        chunk_plan_path = parent_dir / "chunk_plan.json"

    run_pre_analysis(pptx_data_path, manifest_path, chunk_plan_path, output_path)


if __name__ == "__main__":
    main()
