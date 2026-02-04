#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPTX 화면정의서에서 이미지를 추출하는 스크립트

이미지 추출 워크플로우:
1. PPTX 파일에서 모든 이미지 추출
2. output/images/ 폴더에 저장
3. image_manifest.json 생성 (메타데이터)

보안 기능:
- .gitignore 자동 생성
- 민감 정보 경고 메시지
- cleanup 함수 제공

사용법:
    py extract_images.py "화면정의서.pptx" --output "output"
"""

import argparse
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def print_security_warning():
    """보안 경고 메시지 출력"""
    print()
    print("=" * 60)
    print("  [보안 알림]")
    print("=" * 60)
    print("  화면정의서에서 이미지를 추출합니다.")
    print("  - 민감한 정보(환자 데이터, 개인정보 등)가 포함된 경우 주의하세요.")
    print("  - 추출된 이미지는 output/images/ 폴더에 저장됩니다.")
    print("  - --cleanup 옵션으로 TC 생성 후 자동 삭제할 수 있습니다.")
    print("=" * 60)
    print()


def create_gitignore(output_dir: Path):
    """output 폴더에 .gitignore 생성

    추출된 이미지와 임시 JSON 파일이 버전 관리에 포함되지 않도록 합니다.
    """
    gitignore_path = output_dir / ".gitignore"
    gitignore_content = """# 테스트케이스 생성기 임시 파일
# 이 폴더의 이미지는 화면정의서에서 추출된 것으로
# 민감한 정보가 포함될 수 있습니다.

images/
image_manifest.json
image_analysis.json
*.png
*.jpg
*.jpeg
*.gif
*.bmp
*.tiff

# 분석 결과는 유지 (필요시 주석 해제)
# !image_analysis.json
"""
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    print(f"  .gitignore 생성됨: {gitignore_path}")


def cleanup_images(output_dir: str, keep_manifest: bool = False):
    """TC 생성 완료 후 이미지 파일 삭제

    Args:
        output_dir: 출력 폴더 경로
        keep_manifest: manifest 파일 유지 여부 (기본: False)
    """
    output_path = Path(output_dir)
    images_dir = output_path / "images"

    deleted_count = 0

    # 이미지 폴더 삭제
    if images_dir.exists():
        file_count = len(list(images_dir.glob("*")))
        shutil.rmtree(images_dir)
        deleted_count += file_count
        print(f"  이미지 폴더 삭제됨: {images_dir} ({file_count}개 파일)")

    # manifest 삭제 (옵션)
    if not keep_manifest:
        manifest_path = output_path / "image_manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()
            print(f"  manifest 삭제됨: {manifest_path}")

    # 분석 결과 삭제 (선택적)
    analysis_path = output_path / "image_analysis.json"
    if analysis_path.exists() and not keep_manifest:
        analysis_path.unlink()
        print(f"  분석 결과 삭제됨: {analysis_path}")

    print(f"  총 {deleted_count}개 파일 삭제 완료")


def get_image_extension(content_type: str) -> str:
    """컨텐츠 타입에서 확장자 추출"""
    extension_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
        "image/x-wmf": ".wmf",
        "image/x-emf": ".emf",
    }
    return extension_map.get(content_type, ".png")


def extract_images_from_pptx(pptx_path: Path, output_dir: Path) -> dict:
    """PPTX에서 모든 이미지를 추출하여 저장

    Args:
        pptx_path: PPTX 파일 경로
        output_dir: 출력 폴더 경로

    Returns:
        image_manifest: 추출된 이미지 목록과 메타데이터
    """
    prs = Presentation(str(pptx_path))

    # 이미지 출력 폴더 생성
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # manifest 초기화
    manifest = {
        "pptx_file": pptx_path.name,
        "pptx_path": str(pptx_path.resolve()),
        "extraction_date": datetime.now().isoformat(),
        "output_dir": str(output_dir.resolve()),
        "total_images": 0,
        "images": []
    }

    image_count = 0

    for slide_num, slide in enumerate(prs.slides, 1):
        slide_image_index = 0

        for shape in slide.shapes:
            # 이미지 shape 확인
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    image = shape.image
                    content_type = image.content_type
                    extension = get_image_extension(content_type)

                    # 파일명 생성
                    filename = f"slide_{slide_num:02d}_image_{slide_image_index:02d}{extension}"
                    image_path = images_dir / filename

                    # 이미지 저장
                    with open(image_path, "wb") as f:
                        f.write(image.blob)

                    # 이미지 크기 정보 (shape의 크기)
                    width = shape.width.inches if hasattr(shape.width, 'inches') else 0
                    height = shape.height.inches if hasattr(shape.height, 'inches') else 0

                    # 위치 정보
                    left = shape.left.inches if hasattr(shape.left, 'inches') else 0
                    top = shape.top.inches if hasattr(shape.top, 'inches') else 0

                    # manifest에 추가
                    image_info = {
                        "filename": filename,
                        "path": str(image_path.resolve()),
                        "slide_number": slide_num,
                        "image_index": slide_image_index,
                        "content_type": content_type,
                        "size": {
                            "width_inches": round(width, 2),
                            "height_inches": round(height, 2)
                        },
                        "position": {
                            "left_inches": round(left, 2),
                            "top_inches": round(top, 2)
                        },
                        "analysis": None  # Claude Code 분석 후 채워짐
                    }
                    manifest["images"].append(image_info)

                    image_count += 1
                    slide_image_index += 1

                except Exception as e:
                    print(f"  [경고] 슬라이드 {slide_num} 이미지 추출 실패: {e}")

    manifest["total_images"] = image_count

    return manifest


def save_manifest(manifest: dict, output_dir: Path):
    """manifest 파일 저장"""
    manifest_path = output_dir / "image_manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest_path


def extract_and_save_images(pptx_path: str, output_dir: str = None) -> dict:
    """PPTX에서 이미지 추출 및 저장 (메인 함수)

    Args:
        pptx_path: PPTX 파일 경로
        output_dir: 출력 폴더 경로 (기본: ./output)

    Returns:
        manifest: 추출 결과 정보
    """
    pptx_path = Path(pptx_path).resolve()

    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTX 파일을 찾을 수 없습니다: {pptx_path}")

    if not pptx_path.suffix.lower() == ".pptx":
        raise ValueError(f"PPTX 파일이 아닙니다: {pptx_path}")

    # 출력 폴더 설정
    if output_dir:
        output_path = Path(output_dir).resolve()
    else:
        output_path = pptx_path.parent / "output"

    output_path.mkdir(parents=True, exist_ok=True)

    # .gitignore 생성
    create_gitignore(output_path)

    # 이미지 추출
    print(f"  PPTX 파일: {pptx_path}")
    manifest = extract_images_from_pptx(pptx_path, output_path)

    # manifest 저장
    manifest_path = save_manifest(manifest, output_path)
    print(f"  manifest 생성됨: {manifest_path}")

    return manifest


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="PPTX 화면정의서에서 이미지를 추출합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  py extract_images.py "화면정의서.pptx"
  py extract_images.py "화면정의서.pptx" --output "output"
  py extract_images.py --cleanup "output"
        """
    )

    parser.add_argument(
        "pptx_file",
        nargs="?",
        help="입력 PPTX 파일 경로"
    )

    parser.add_argument(
        "--output", "-o",
        dest="output_dir",
        default=None,
        help="출력 폴더 경로 (기본값: ./output)"
    )

    parser.add_argument(
        "--cleanup", "-c",
        dest="cleanup_dir",
        metavar="DIR",
        help="지정된 폴더의 추출된 이미지 삭제"
    )

    parser.add_argument(
        "--keep-manifest",
        action="store_true",
        help="cleanup 시 manifest 파일 유지"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="보안 경고 메시지 생략"
    )

    args = parser.parse_args()

    # cleanup 모드
    if args.cleanup_dir:
        print(f"[정리] 추출된 이미지 삭제 중...")
        cleanup_images(args.cleanup_dir, args.keep_manifest)
        print("[정리] 완료")
        return 0

    # 추출 모드
    if not args.pptx_file:
        parser.print_help()
        return 1

    if not args.quiet:
        print_security_warning()

    print("[추출] 이미지 추출 시작...")

    try:
        manifest = extract_and_save_images(
            pptx_path=args.pptx_file,
            output_dir=args.output_dir
        )

        print()
        print("-" * 60)
        print("  추출 결과 요약")
        print("-" * 60)
        print(f"  입력 파일      : {manifest['pptx_file']}")
        print(f"  추출된 이미지  : {manifest['total_images']}개")
        print(f"  출력 폴더      : {manifest['output_dir']}")
        print("-" * 60)
        print()
        print("[추출] 완료!")
        print()
        print("다음 단계:")
        print("  1. Claude Code에서 이미지 분석 요청")
        print('     "output/images 폴더의 이미지들을 분석해줘"')
        print("  2. 분석 결과로 TC 생성")
        print('     py run_all.py "화면정의서.pptx" --with-analysis "output/image_analysis.json"')

        return 0

    except FileNotFoundError as e:
        print(f"[오류] 파일을 찾을 수 없습니다: {e}")
        return 1
    except ValueError as e:
        print(f"[오류] 잘못된 입력: {e}")
        return 1
    except Exception as e:
        print(f"[오류] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
