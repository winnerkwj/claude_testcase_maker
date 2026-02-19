#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
테스트케이스 생성기 중앙 설정 파일

모든 설정값을 중앙 관리하며, 환경변수로 오버라이드 가능합니다.

우선순위: CLI 인자 > 환경변수 > config 파일 > 자동감지
"""

import os
from pathlib import Path
from typing import Optional


def _auto_detect_project_root() -> Path:
    """프로젝트 루트 자동 감지 (CLAUDE.md 위치 기준)"""
    current = Path(__file__).resolve().parent

    # testcase-generator 폴더에서 시작하여 상위로 탐색
    for _ in range(5):
        if (current / "CLAUDE.md").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    # 찾지 못하면 testcase-generator의 부모 디렉토리 반환
    return Path(__file__).resolve().parent.parent


def _get_env_int(key: str, default: int) -> int:
    """환경변수에서 정수 값 가져오기"""
    value = os.environ.get(key)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            pass
    return default


def _get_env_str(key: str, default: str) -> str:
    """환경변수에서 문자열 값 가져오기"""
    return os.environ.get(key, default)


def _get_env_path(key: str, default: Path) -> Path:
    """환경변수에서 경로 값 가져오기"""
    value = os.environ.get(key)
    if value:
        return Path(value)
    return default


# ============================================================
# 경로 설정
# ============================================================

# 프로젝트 루트 (CLAUDE.md 위치)
PROJECT_ROOT: Path = _get_env_path(
    "TC_PROJECT_ROOT",
    _auto_detect_project_root()
)

# 출력 디렉토리
OUTPUT_DIR: Path = _get_env_path(
    "TC_OUTPUT_DIR",
    PROJECT_ROOT / "output"
)

# 스크립트 디렉토리
SCRIPTS_DIR: Path = Path(__file__).resolve().parent / "scripts"

# 템플릿 파일
TEMPLATE_PATH: Path = Path(__file__).resolve().parent / "assets" / "template.xlsx"


# ============================================================
# 청크 처리 설정
# ============================================================

# 청크당 최대 페이지 수
MAX_PAGES_PER_CHUNK: int = _get_env_int("TC_MAX_PAGES_PER_CHUNK", 15)

# 청크당 최대 컴포넌트 수
MAX_COMPONENTS_PER_CHUNK: int = _get_env_int("TC_MAX_COMPONENTS_PER_CHUNK", 80)

# 동시 실행 최대 에이전트 수
MAX_PARALLEL_AGENTS: int = _get_env_int("TC_MAX_PARALLEL_AGENTS", 10)

# 최소 청크 수 (항상 이 수 이상의 에이전트로 병렬 처리)
MIN_CHUNKS: int = _get_env_int("TC_MIN_CHUNKS", 3)


# ============================================================
# TC ID 설정
# ============================================================

# 기본 TC ID 접두사 (IT_{PREFIX}_001 형식)
DEFAULT_TC_PREFIX: str = _get_env_str("TC_PREFIX", "IT_XX")


# ============================================================
# Excel 색상 설정
# ============================================================

EXCEL_COLORS = {
    # 헤더 색상
    "header": "4472C4",         # 진한 파랑
    "subheader": "5B9BD5",      # 연한 파랑
    "summary": "D9E2F3",        # 아주 연한 파랑

    # 테스트 회차 색상
    "round1": "70AD47",         # 녹색 (1차)
    "round2": "FFC000",         # 주황 (2차)
    "round3": "ED7D31",         # 빨강 (3차)

    # 특수 색상
    "blank_field": "FFFF00",    # 노란색 (공란 표시)
}


# ============================================================
# Excel 드롭다운 옵션
# ============================================================

RESULT_OPTIONS = ["Pass", "Fail", "N/T", "Block"]
SEVERITY_OPTIONS = ["Critical", "Major", "Minor", "Trivial"]


# ============================================================
# Excel 컬럼 정의
# ============================================================

# 기본 컬럼 (컬럼명, 컬럼 너비)
BASE_COLUMNS = [
    ("No", 5),
    ("Test Case ID", 15),
    ("Depth 1", 12),
    ("Depth 2", 18),
    ("Depth 3", 15),
    ("Depth 4", 12),
    ("Title", 25),
    ("Pre-condition", 20),
    ("Test Step", 45),
    ("Expected Result", 45),
    ("요구사항 ID", 12),
    ("Reference", 10),
    ("중요도", 8),
    ("Writer", 10),
]

# 테스트 회차 서브 컬럼
ROUND_SUBCOLUMNS = ["Result", "Severity", "Comments", "Issue #", "Tester"]

# 테스트 회차 수
NUM_TEST_ROUNDS = 3


# ============================================================
# 유틸리티 함수
# ============================================================

def get_output_dir() -> Path:
    """출력 디렉토리 가져오기 (없으면 생성)"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def get_images_dir() -> Path:
    """이미지 디렉토리 가져오기 (없으면 생성)"""
    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def resolve_output_path(filename: str) -> Path:
    """출력 파일 경로 생성"""
    return get_output_dir() / filename


# ============================================================
# 설정 출력 (디버깅용)
# ============================================================

def print_config():
    """현재 설정값 출력"""
    print("=" * 60)
    print("  TC Generator Configuration")
    print("=" * 60)
    print(f"PROJECT_ROOT:           {PROJECT_ROOT}")
    print(f"OUTPUT_DIR:             {OUTPUT_DIR}")
    print(f"SCRIPTS_DIR:            {SCRIPTS_DIR}")
    print(f"TEMPLATE_PATH:          {TEMPLATE_PATH}")
    print("-" * 60)
    print(f"MAX_PAGES_PER_CHUNK:    {MAX_PAGES_PER_CHUNK}")
    print(f"MAX_COMPONENTS_PER_CHUNK: {MAX_COMPONENTS_PER_CHUNK}")
    print(f"MAX_PARALLEL_AGENTS:    {MAX_PARALLEL_AGENTS}")
    print(f"MIN_CHUNKS:             {MIN_CHUNKS}")
    print(f"DEFAULT_TC_PREFIX:      {DEFAULT_TC_PREFIX}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
