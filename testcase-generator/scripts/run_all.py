#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
테스트케이스 생성 통합 스크립트

PPTX 화면정의서에서 테스트케이스 Excel 파일을 한 번에 생성합니다.

사용법:
    py run_all.py "화면정의서.pptx" --output "출력폴더" --prefix "IT_OP"
    py run_all.py "화면정의서.pptx" --with-analysis "output/image_analysis.json"
    py run_all.py "화면정의서.pptx" --cleanup
"""

import argparse
import json
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 같은 디렉토리의 모듈 import
from extract_pptx import extract_pptx
from generate_testcase import generate_testcases, testcases_to_dict
from write_excel import create_new_testcase_excel


# 예외 테스트케이스 포함 여부 기본값
DEFAULT_INCLUDE_EXCEPTIONS = False


def print_header():
    """헤더 출력"""
    print("=" * 60)
    print("  테스트케이스 자동 생성 도구")
    print("  PPTX -> Test Cases Excel")
    print("=" * 60)
    print()


def print_summary(result: dict):
    """결과 요약 출력"""
    print()
    print("-" * 60)
    print("  실행 결과 요약")
    print("-" * 60)
    print(f"  입력 파일      : {result['input_file']}")
    print(f"  출력 파일      : {result['output_file']}")
    print(f"  총 슬라이드 수 : {result['total_slides']}")
    print(f"  추출된 컴포넌트: {result['total_components']}")
    print(f"  생성된 TC 수   : {result['total_testcases']}")
    print(f"  TC ID 접두사   : {result['prefix']}")
    if result.get('used_image_analysis'):
        print(f"  이미지 분석    : 적용됨")
    print(f"  처리 시간      : {result['elapsed_time']:.2f}초")
    print("-" * 60)
    print()


def merge_image_analysis_data(extracted_data: dict, analysis_path: str) -> dict:
    """이미지 분석 결과를 추출 데이터에 병합

    Args:
        extracted_data: PPTX에서 추출한 데이터
        analysis_path: 이미지 분석 결과 JSON 파일 경로

    Returns:
        병합된 데이터
    """
    try:
        from merge_analysis import merge_image_analysis
    except ImportError:
        # merge_analysis 모듈이 없으면 간단한 병합만 수행
        with open(analysis_path, "r", encoding="utf-8") as f:
            image_analysis = json.load(f)

        # 간단한 병합: 슬라이드 번호로 매칭
        components = extracted_data.get("all_components", [])

        for image_result in image_analysis.get("images", []):
            slide_number = image_result.get("slide_number", 0)
            elements = image_result.get("elements", [])

            # 해당 슬라이드의 컴포넌트에 시각 정보 추가
            for comp in components:
                if comp.get("slide_number") == slide_number:
                    # 첫 번째 element의 정보로 보강
                    if elements:
                        comp["visual_info"] = {
                            "position": elements[0].get("position", ""),
                            "state": elements[0].get("state", ""),
                            "layout_area": elements[0].get("layout_area", ""),
                        }

        return extracted_data

    # merge_analysis 모듈 사용
    with open(analysis_path, "r", encoding="utf-8") as f:
        image_analysis = json.load(f)

    return merge_image_analysis(extracted_data, image_analysis)


def run_all(
    pptx_path: str,
    output_dir: str = None,
    prefix: str = "IT_OO",
    keep_temp: bool = False,
    include_exceptions: bool = False,
    analysis_path: str = None,
    cleanup_images: bool = False
) -> dict:
    """
    전체 프로세스 실행

    Args:
        pptx_path: PPTX 파일 경로
        output_dir: 출력 폴더 경로 (None이면 PPTX 파일과 같은 폴더)
        prefix: 테스트케이스 ID 접두사
        keep_temp: 임시 파일 유지 여부
        include_exceptions: 예외 테스트케이스 포함 여부
        analysis_path: 이미지 분석 결과 JSON 파일 경로 (선택)
        cleanup_images: TC 생성 후 추출된 이미지 삭제 여부

    Returns:
        실행 결과 딕셔너리
    """
    start_time = datetime.now()

    # 경로 처리
    pptx_path = Path(pptx_path).resolve()

    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTX 파일을 찾을 수 없습니다: {pptx_path}")

    if not pptx_path.suffix.lower() == ".pptx":
        raise ValueError(f"PPTX 파일이 아닙니다: {pptx_path}")

    # 출력 폴더 설정
    if output_dir:
        output_dir = Path(output_dir).resolve()
    else:
        output_dir = pptx_path.parent

    output_dir.mkdir(parents=True, exist_ok=True)

    # 출력 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{pptx_path.stem}_TestCases_{timestamp}.xlsx"
    output_path = output_dir / output_filename

    # 임시 폴더 생성
    temp_dir = Path(tempfile.mkdtemp(prefix="tc_generator_"))

    # 분석 결과 사용 여부
    using_analysis = analysis_path and Path(analysis_path).exists()

    try:
        print(f"[1/3] PPTX 파일 분석 중...")
        print(f"      입력: {pptx_path}")

        # Step 1: PPTX 추출
        extracted_data = extract_pptx(pptx_path)

        total_slides = extracted_data.get("total_slides", 0)
        all_components = extracted_data.get("all_components", [])
        total_components = len(all_components)

        print(f"      -> {total_slides}개 슬라이드에서 {total_components}개 컴포넌트 추출")

        if total_components == 0:
            print("      [경고] 추출된 컴포넌트가 없습니다.")
            print("             PPTX 파일에 컴포넌트 테이블이 있는지 확인하세요.")

        # 이미지 분석 결과 병합 (있는 경우)
        if using_analysis:
            print()
            print(f"[이미지 분석] 분석 결과 병합 중...")
            print(f"              분석 파일: {analysis_path}")
            extracted_data = merge_image_analysis_data(extracted_data, analysis_path)
            print(f"              -> 시각 정보 병합 완료")

        print()
        print(f"[2/3] 테스트케이스 생성 중...")
        print(f"      접두사: {prefix}")
        if include_exceptions:
            print(f"      예외 TC: 포함")
        if using_analysis:
            print(f"      이미지 분석: 반영됨")

        # Step 2: 테스트케이스 생성 (개선된 버전)
        testcases = generate_testcases(extracted_data, id_prefix=prefix, include_exceptions=include_exceptions)
        total_testcases = len(testcases)

        print(f"      -> {total_testcases}개 테스트케이스 생성")

        # 테스트케이스 데이터 구성
        testcases_data = {
            "project_info": extracted_data.get("project_info", {}),
            "total_testcases": total_testcases,
            "testcases": testcases_to_dict(testcases)
        }

        print()
        print(f"[3/3] Excel 파일 생성 중...")
        print(f"      출력: {output_path}")

        # Step 3: Excel 작성
        create_new_testcase_excel(testcases_data, output_path)

        print(f"      -> 완료!")

        # 이미지 정리 (옵션)
        if cleanup_images:
            print()
            print(f"[정리] 추출된 이미지 삭제 중...")
            try:
                from extract_images import cleanup_images as do_cleanup
                do_cleanup(str(output_dir), keep_manifest=False)
                print(f"       -> 완료!")
            except ImportError:
                print(f"       [경고] extract_images 모듈을 찾을 수 없어 정리를 건너뜁니다.")

        elapsed_time = (datetime.now() - start_time).total_seconds()

        result = {
            "success": True,
            "input_file": str(pptx_path),
            "output_file": str(output_path),
            "total_slides": total_slides,
            "total_components": total_components,
            "total_testcases": total_testcases,
            "prefix": prefix,
            "elapsed_time": elapsed_time,
            "used_image_analysis": using_analysis
        }

        return result

    except Exception as e:
        elapsed_time = (datetime.now() - start_time).total_seconds()
        return {
            "success": False,
            "input_file": str(pptx_path),
            "output_file": None,
            "error": str(e),
            "elapsed_time": elapsed_time
        }

    finally:
        # 임시 폴더 정리
        if not keep_temp and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="PPTX 화면정의서에서 테스트케이스 Excel 파일을 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  py run_all.py "화면정의서.pptx"
  py run_all.py "화면정의서.pptx" --output "결과폴더"
  py run_all.py "화면정의서.pptx" --output "결과폴더" --prefix "IT_OP"
  py run_all.py "화면정의서.pptx" --with-analysis "output/image_analysis.json"
  py run_all.py "화면정의서.pptx" --with-analysis "output/image_analysis.json" --cleanup

이미지 분석 워크플로우:
  1. py extract_images.py "화면정의서.pptx" --output "output"
  2. Claude Code에서 이미지 분석 요청
  3. py run_all.py "화면정의서.pptx" --with-analysis "output/image_analysis.json"
        """
    )

    parser.add_argument(
        "pptx_file",
        help="입력 PPTX 파일 경로"
    )

    parser.add_argument(
        "--output", "-o",
        dest="output_dir",
        default=None,
        help="출력 폴더 경로 (기본값: PPTX 파일과 같은 폴더)"
    )

    parser.add_argument(
        "--prefix", "-p",
        default="IT_OO",
        help="테스트케이스 ID 접두사 (기본값: IT_OO)"
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="임시 파일 유지 (디버깅용)"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="간략한 출력"
    )

    parser.add_argument(
        "--include-exceptions", "-e",
        action="store_true",
        help="예외/에러 테스트케이스 포함"
    )

    parser.add_argument(
        "--with-analysis", "-a",
        dest="analysis_path",
        default=None,
        help="이미지 분석 JSON 파일 경로 (Claude Code 분석 결과)"
    )

    parser.add_argument(
        "--cleanup", "-c",
        action="store_true",
        help="TC 생성 후 추출된 이미지 자동 삭제"
    )

    args = parser.parse_args()

    if not args.quiet:
        print_header()

    try:
        result = run_all(
            pptx_path=args.pptx_file,
            output_dir=args.output_dir,
            prefix=args.prefix,
            keep_temp=args.keep_temp,
            include_exceptions=args.include_exceptions,
            analysis_path=args.analysis_path,
            cleanup_images=args.cleanup
        )

        if result["success"]:
            if not args.quiet:
                print_summary(result)
            else:
                print(f"출력: {result['output_file']}")
                print(f"TC 수: {result['total_testcases']}")

            return 0
        else:
            print(f"\n[오류] {result.get('error', '알 수 없는 오류')}")
            return 1

    except FileNotFoundError as e:
        print(f"\n[오류] 파일을 찾을 수 없습니다: {e}")
        return 1
    except ValueError as e:
        print(f"\n[오류] 잘못된 입력: {e}")
        return 1
    except Exception as e:
        print(f"\n[오류] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
