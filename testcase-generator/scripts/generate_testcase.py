#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
컴포넌트 정보를 기반으로 테스트케이스를 생성하는 스크립트

개선된 버전:
- TC ID: 순차 번호 방식 (IT_OP_001)
- Title: 간결한 명사형 키워드
- Test Step: ">" 네비게이션 형식
- Expected Result: 단일 "#" 접두사
- Depth: 기능 영역 기반 구조
"""

import json
import sys
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict


@dataclass
class TestCase:
    """테스트케이스 데이터 클래스"""
    test_case_id: str
    depth1: str
    depth2: str
    depth3: str
    depth4: str
    title: str
    pre_condition: str
    test_step: str
    expected_result: str
    requirement_id: str = ""
    reference: str = ""
    importance: str = ""
    writer: str = ""


# 컴포넌트 타입별 Pre-condition (개선: 기본 TC는 비움, 특수 조건만 명시)
# 값이 빈 문자열이면 Pre-condition 비움
PRECONDITION_BY_TYPE = {
    "button": "",  # 기본 버튼 TC는 Pre-condition 비움
    "button_disabled": "버튼 비활성화 상태",  # 비활성 버튼 테스트시
    "input": "",  # 기본 입력 TC는 Pre-condition 비움
    "input_validation": "입력 필드에 값이 입력된 상태",  # 유효성 검증시
    "list": "",  # 기본 목록 TC는 Pre-condition 비움
    "list_empty": "데이터가 없는 상태",  # 빈 목록 테스트시
    "popup": "팝업이 표시된 상태",  # 팝업 관련 TC
    "popup_trigger": "",  # 팝업 트리거 TC는 Pre-condition 비움
    "minimize": "화면이 최소화된 상태",  # 최소화 복원 테스트
    "maximize": "화면이 최대화된 상태",  # 최대화 복원 테스트
    "undo": "작업 내역이 있는 상태",  # Undo 기능 테스트
    "redo": "실행 취소된 작업이 있는 상태",  # Redo 기능 테스트
    "save": "저장할 변경사항이 있는 상태",  # 저장 기능 테스트
    "validation": "",  # 기본 유효성 검증 TC는 Pre-condition 비움
    "default": "",  # 기본값: Pre-condition 비움
}

# 컴포넌트 이름 → 간결한 Title 키워드 매핑
TITLE_KEYWORD_MAP = {
    # 버튼
    "save": "저장",
    "cancel": "취소",
    "close": "닫기",
    "back": "뒤로가기",
    "next": "다음",
    "minimize": "최소화",
    "maximize": "최대화",
    "search": "검색",
    "reset": "초기화",
    "refresh": "새로고침",
    "delete": "삭제",
    "add": "추가",
    "edit": "수정",
    "apply": "적용",
    "confirm": "확인",
    # 레이아웃
    "title": "타이틀",
    "header": "헤더",
    "footer": "푸터",
    "sidebar": "사이드바",
    "toolbar": "툴바",
    "menu": "메뉴",
    # 입력
    "input": "입력",
    "field": "필드",
    "textbox": "텍스트박스",
    # 목록
    "list": "목록",
    "table": "테이블",
    "grid": "그리드",
    "chart": "차트",
    # 팝업
    "popup": "팝업",
    "modal": "모달",
    "dialog": "다이얼로그",
    # 기타
    "option": "옵션",
    "setting": "설정",
    "patient": "환자",
    "thumbnail": "썸네일",
    "modality": "Modality",
}

# 테스트 유형별 Depth4 라벨
TEST_TYPE_LABELS = {
    "functional": "기능 확인",
    "ui": "표시 확인",
    "hover": "Hover 확인",
    "validation": "유효성 확인",
    "boundary": "경계값 확인",
    "selection": "선택 확인",
    "close": "닫기 확인",
    "shortcut": "단축키 확인",
}

# ===== Part 3: 단축키 TC 자동 생성 =====

# 단축키 매핑 (컴포넌트 키워드 -> 단축키)
SHORTCUT_MAP = {
    "save": "Ctrl+S",
    "저장": "Ctrl+S",
    "close": "Alt+F4",
    "닫기": "Alt+F4",
    "환경설정": "F12",
    "setting": "F12",
    "도움말": "F1",
    "help": "F1",
    "취소": "Esc",
    "cancel": "Esc",
    "새로만들기": "Ctrl+N",
    "new": "Ctrl+N",
    "열기": "Ctrl+O",
    "open": "Ctrl+O",
    "인쇄": "Ctrl+P",
    "print": "Ctrl+P",
    "실행취소": "Ctrl+Z",
    "undo": "Ctrl+Z",
    "다시실행": "Ctrl+Y",
    "redo": "Ctrl+Y",
    "복사": "Ctrl+C",
    "copy": "Ctrl+C",
    "붙여넣기": "Ctrl+V",
    "paste": "Ctrl+V",
    "잘라내기": "Ctrl+X",
    "cut": "Ctrl+X",
    "전체선택": "Ctrl+A",
    "selectall": "Ctrl+A",
    "찾기": "Ctrl+F",
    "find": "Ctrl+F",
    "새로고침": "F5",
    "refresh": "F5",
}

# ===== Part 3: 조건별 TC 분리 =====

# 조건 분리가 필요한 컴포넌트 패턴
CONDITION_PATTERNS = {
    "popup": ["작업내역 없음", "작업내역 있음"],
    "save": ["작업내역 없음", "작업내역 있음"],
    "close": ["작업내역 없음", "작업내역 있음"],
    "저장": ["작업내역 없음", "작업내역 있음"],
    "닫기": ["작업내역 없음", "작업내역 있음"],
    "delete": ["단일 항목 선택", "다중 항목 선택"],
    "삭제": ["단일 항목 선택", "다중 항목 선택"],
}

# 컴포넌트 타입별 테스트케이스 패턴
COMPONENT_PATTERNS = {
    # 버튼 관련
    "button": [
        {
            "type": "functional",
            "title_suffix": "클릭 기능 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 메인 화면 로딩 완료 확인\n3. [{component}] 버튼 위치 확인\n4. [{component}] 버튼 클릭",
            "expected_result_template": "# 버튼 클릭 동작 정상 수행\n- {description}\n- 관련 기능이 정상 동작함"
        },
        {
            "type": "ui",
            "title_suffix": "UI 상태 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 메인 화면 로딩 완료 확인\n3. [{component}] 버튼 영역 확인",
            "expected_result_template": "# 버튼이 정상적으로 표시됨\n- 버튼 아이콘/텍스트 표시 정상\n- 활성화 상태 확인\n- 버튼 위치 및 크기 정상"
        },
        {
            "type": "hover",
            "title_suffix": "Hover 상태 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 메인 화면 로딩 완료 확인\n3. [{component}] 버튼에 마우스 오버\n4. 툴팁 표시 대기 (1~2초)",
            "expected_result_template": "# Hover 시 시각적 피드백 확인\n- 마우스 오버 시 버튼 스타일 변경됨\n- 툴팁 표시됨: \"{hint}\""
        }
    ],
    # 입력 필드 관련
    "input": [
        {
            "type": "functional",
            "title_suffix": "입력 기능 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 해당 기능 화면 진입\n3. [{component}] 필드 클릭\n4. 테스트 값 입력\n5. 입력 완료 확인 (Enter 또는 포커스 이동)",
            "expected_result_template": "# 입력 기능 정상 동작\n- 입력값이 필드에 정상 표시됨\n- 입력값이 시스템에 반영됨"
        },
        {
            "type": "validation",
            "title_suffix": "유효성 검사 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 해당 기능 화면 진입\n3. [{component}] 필드 클릭\n4. 유효하지 않은 값 입력 (빈값/특수문자/범위초과)\n5. 입력 완료 시도",
            "expected_result_template": "# 유효성 검사 동작 확인\n- 잘못된 입력 시 오류 메시지 표시됨\n- 유효하지 않은 값은 저장되지 않음"
        },
        {
            "type": "boundary",
            "title_suffix": "경계값 테스트",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 해당 기능 화면 진입\n3. [{component}] 필드에 최소값 입력 후 확인\n4. [{component}] 필드에 최대값 입력 후 확인",
            "expected_result_template": "# 경계값 처리 정상\n- 최소값 입력 시 정상 처리됨\n- 최대값 입력 시 정상 처리됨\n- 범위 초과 시 적절한 처리됨"
        }
    ],
    # 테이블/리스트 관련
    "list": [
        {
            "type": "functional",
            "title_suffix": "목록 표시 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 해당 기능 화면 진입\n3. 데이터 로딩 완료 대기\n4. [{component}] 영역 확인",
            "expected_result_template": "# 목록 표시 정상\n- 데이터 목록이 정상 표시됨\n- 컬럼/행 구조 정상\n- {description}"
        },
        {
            "type": "selection",
            "title_suffix": "항목 선택 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 해당 기능 화면 진입\n3. [{component}] 목록에서 임의 항목 클릭\n4. 선택 상태 확인",
            "expected_result_template": "# 항목 선택 동작 정상\n- 선택한 항목 하이라이트 표시됨\n- 선택 정보가 관련 영역에 반영됨"
        }
    ],
    # 팝업/모달 관련
    "popup": [
        {
            "type": "functional",
            "title_suffix": "팝업 표시 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 팝업 트리거 조건 수행\n3. [{component}] 팝업 표시 확인",
            "expected_result_template": "# 팝업 정상 표시\n- [{component}] 팝업창 정상 표시됨\n- 팝업 내용 정상 로딩됨\n- {description}"
        },
        {
            "type": "close",
            "title_suffix": "팝업 닫기 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 팝업 트리거 조건 수행\n3. [{component}] 팝업 표시 확인\n4. 닫기 버튼 클릭 또는 ESC 키 입력",
            "expected_result_template": "# 팝업 닫기 정상\n- 팝업창이 정상적으로 닫힘\n- 기존 화면으로 복귀됨"
        }
    ],
    # 기본 패턴
    "default": [
        {
            "type": "ui",
            "title_suffix": "표시 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 메인 화면 로딩 완료 확인\n3. [{component}] 영역 위치 확인\n4. 표시 상태 확인",
            "expected_result_template": "# 화면 요소 정상 표시\n- [{component}] 영역이 정상 표시됨\n- {description}"
        },
        {
            "type": "functional",
            "title_suffix": "기능 확인",
            "test_step_template": "1. {app_name} 프로그램 실행\n2. 메인 화면 로딩 완료 확인\n3. [{component}] 기능 실행",
            "expected_result_template": "# 기능 정상 동작\n- {description}\n- 기대한 결과가 정상 표시됨"
        }
    ]
}

# 컴포넌트 이름으로 타입 분류
COMPONENT_TYPE_KEYWORDS = {
    "button": ["button", "btn", "버튼", "save", "back", "next", "close", "닫기", "저장", "최소화", "최대화"],
    "input": ["input", "field", "text", "입력", "필드", "search", "검색"],
    "list": ["list", "table", "grid", "목록", "리스트", "chart", "object list"],
    "popup": ["popup", "modal", "dialog", "팝업", "모달", "알림", "창"]
}


def classify_component_type(component_name: str, description: str) -> str:
    """컴포넌트 이름과 설명으로 타입 분류"""
    text = f"{component_name} {description}".lower()

    for comp_type, keywords in COMPONENT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return comp_type

    return "default"


def extract_hints_from_description(description: str) -> dict:
    """Description에서 Hint, 단축키 등 추출"""
    info = {"hint": "", "shortcut": "", "actions": []}

    # Hint 추출
    hint_match = description.split("Hint")
    if len(hint_match) > 1:
        hint_part = hint_match[1].split("\n")[0]
        info["hint"] = hint_part.replace(":", "").strip()

    # 단축키 추출
    if "Ctrl" in description or "F1" in description or "단축키" in description:
        for line in description.split("\n"):
            if "Ctrl" in line or "F1" in line.upper():
                info["shortcut"] = line.strip()

    return info


def generate_test_id(prefix: str, counter: int) -> str:
    """테스트케이스 ID 생성 (순차 번호 방식)

    Args:
        prefix: ID 접두사 (예: IT_OP)
        counter: 전역 순번

    Returns:
        예: IT_OP_001, IT_OP_002
    """
    return f"{prefix}_{counter:03d}"


def generate_concise_title(component_name: str, description: str = "") -> str:
    """간결한 명사형 Title 생성 (레거시 호환용)

    Args:
        component_name: 컴포넌트 이름
        description: 설명 텍스트

    Returns:
        간결한 키워드 형식 (예: "저장", "환자검색", "타이틀 확인")
    """
    return generate_detailed_title(component_name, description, "default")


def generate_detailed_title(component_name: str, description: str = "", test_type: str = "default") -> str:
    """상세한 Title 생성 (수작업 TC 스타일)

    개선 사항:
    - 버튼명 명시: `[Save] 버튼 클릭`
    - 동작 방식 구분: `저장 단축키 입력`, `저장 버튼 클릭`
    - 컴포넌트명 + 동작: `최소화 버튼 클릭`

    Args:
        component_name: 컴포넌트 이름
        description: 설명 텍스트 (단축키 정보 추출용)
        test_type: 테스트 유형 (functional, ui, hover, shortcut 등)

    Returns:
        상세한 Title 형식 (예: "[Save] 버튼 클릭", "저장 단축키 입력")
    """
    text_lower = f"{component_name} {description}".lower()
    clean_name = component_name.strip()

    # 단축키 정보 추출
    shortcut = ""
    if "ctrl" in description.lower() or "f1" in description.lower():
        # Ctrl+S, Ctrl+Z 등 단축키 패턴 추출
        shortcut_match = re.search(r'(Ctrl\s*\+\s*\w+|F\d+)', description, re.IGNORECASE)
        if shortcut_match:
            shortcut = shortcut_match.group(1)

    # 버튼 타입 판별 및 Title 생성
    if "button" in text_lower or "btn" in text_lower or "버튼" in text_lower:
        # 버튼 이름 추출 (Button, Btn 접미사 제거)
        btn_name = re.sub(r'(Button|Btn|버튼)\s*$', '', clean_name, flags=re.IGNORECASE).strip()

        # 매핑 테이블에서 한글 키워드 찾기
        korean_name = None
        for keyword, title in TITLE_KEYWORD_MAP.items():
            if keyword in btn_name.lower():
                korean_name = title
                break

        if test_type == "shortcut" and shortcut:
            # 단축키 테스트: "저장 단축키 입력" 또는 "[Ctrl+S] 단축키 입력"
            if korean_name:
                return f"{korean_name} 단축키 입력"
            else:
                return f"[{shortcut}] 단축키 입력"
        elif test_type == "hover":
            # Hover 테스트: "[Save] 버튼 Hover"
            if korean_name:
                return f"{korean_name} 버튼 Hover"
            else:
                return f"[{btn_name}] 버튼 Hover"
        else:
            # 기본 클릭 테스트: "[Save] 버튼 클릭" 또는 "저장 버튼 클릭"
            if korean_name:
                return f"{korean_name} 버튼 클릭"
            else:
                return f"[{btn_name}] 버튼 클릭"

    # 입력 필드 타입
    elif "input" in text_lower or "field" in text_lower or "필드" in text_lower or "입력" in text_lower:
        field_name = re.sub(r'(Input|Field|필드|입력)\s*$', '', clean_name, flags=re.IGNORECASE).strip()

        # 매핑에서 한글명 찾기
        korean_name = None
        for keyword, title in TITLE_KEYWORD_MAP.items():
            if keyword in field_name.lower():
                korean_name = title
                break

        if korean_name:
            return f"{korean_name} 입력"
        else:
            return f"[{field_name}] 필드 입력"

    # 목록/테이블 타입
    elif "list" in text_lower or "table" in text_lower or "grid" in text_lower or "목록" in text_lower:
        list_name = re.sub(r'(List|Table|Grid|목록)\s*$', '', clean_name, flags=re.IGNORECASE).strip()

        if test_type == "selection":
            return f"[{list_name}] 항목 선택"
        else:
            return f"[{list_name}] 목록 표시"

    # 팝업/모달 타입
    elif "popup" in text_lower or "modal" in text_lower or "dialog" in text_lower or "팝업" in text_lower:
        popup_name = re.sub(r'(Popup|Modal|Dialog|팝업)\s*$', '', clean_name, flags=re.IGNORECASE).strip()

        if test_type == "close":
            return f"[{popup_name}] 팝업 닫기"
        else:
            return f"[{popup_name}] 팝업 표시"

    # 기타 컴포넌트: 매핑 테이블 확인
    for keyword, title in TITLE_KEYWORD_MAP.items():
        if keyword in text_lower:
            if test_type == "ui":
                return f"{title} 표시 확인"
            elif test_type == "functional":
                return f"{title} 기능 확인"
            else:
                return title

    # 매핑에 없으면 컴포넌트 이름 정리하여 반환
    suffixes = ["Button", "Input", "Field", "List", "Table", "버튼", "필드", "입력", "Area", "영역"]
    for suffix in suffixes:
        if clean_name.endswith(suffix):
            clean_name = clean_name[:-len(suffix)].strip()
            break

    words = re.split(r'[\s_]+', clean_name)
    if words:
        result = " ".join(words[:2]) if len(words) > 1 else words[0]
        if test_type == "ui":
            return f"[{result}] 표시 확인"
        elif test_type == "functional":
            return f"[{result}] 기능 확인"
        return f"[{result}]" if result else component_name

    return component_name


def _build_navigation_path(depth1: str, depth2: str, component_name: str) -> str:
    """Test Step용 네비게이션 경로 생성

    Args:
        depth1: Depth1 값 (기능 영역)
        depth2: Depth2 값 (컴포넌트 그룹)
        component_name: 컴포넌트 이름

    Returns:
        ">" 구분자를 사용한 경로 (예: "공통 Layout > Title 영역")
    """
    parts = []

    if depth1:
        parts.append(depth1)
    if depth2 and depth2 != depth1:
        parts.append(depth2)

    # 컴포넌트 영역 추가
    comp_area = f"{component_name} 영역" if component_name else ""
    if comp_area and comp_area not in parts:
        parts.append(comp_area)

    return " > ".join(parts) if parts else component_name


def generate_test_step(component_name: str, test_type: str, depths: dict,
                       description: str = "", context: dict = None,
                       visual_info: dict = None) -> str:
    """Test Step 생성 (화면정의서 데이터 기반)

    원칙: PPTX에서 추출된 데이터만 사용, 하드코딩 금지

    Args:
        component_name: 컴포넌트 이름 (PPTX에서 추출)
        test_type: 테스트 유형 (functional, ui, hover, close 등)
        depths: Depth 구조 딕셔너리 (PPTX 데이터 기반)
        description: 컴포넌트 설명 (PPTX에서 추출)
        context: 추가 컨텍스트 (shortcut 등)
        visual_info: 이미지 분석에서 추출한 시각 정보 (선택)

    Returns:
        Test Step 문자열
    """
    context = context or {}
    visual_info = visual_info or {}
    steps = []

    # 화면 이름: Depth2(섹션명)를 사용, 없으면 "해당 화면"
    # 하드코딩된 "탭" 접미사 제거
    screen_name = depths.get("depth2", "") if depths.get("depth2") else "해당 화면"

    # 컴포넌트 위치 추출 (시각 정보 또는 description에서)
    position = _extract_position(component_name, description, visual_info)

    # 위치 문자열 생성 (시각 정보가 있으면 더 상세하게)
    if visual_info and position:
        # 시각 정보의 레이아웃 영역도 포함
        layout_area = visual_info.get("layout_area", "")
        if layout_area and layout_area not in position:
            position_str = f"화면 {position} ({layout_area}) "
        else:
            position_str = f"화면 {position} "
    elif position:
        position_str = f"화면 {position} "
    else:
        position_str = ""

    comp_lower = component_name.lower()

    # Step 1: 화면 진입
    steps.append(f"1. {screen_name} 화면 진입")

    # 테스트 유형별 Step 생성
    if test_type == "ui":
        steps.append(f"2. {position_str}{component_name} 영역 확인")

    elif test_type == "functional":
        # 컴포넌트별 구체적인 동작 단계
        if "minimize" in comp_lower or "최소화" in comp_lower:
            steps.append(f"2. {position_str}최소화 버튼 클릭")
        elif "maximize" in comp_lower or "최대화" in comp_lower:
            steps.append(f"2. {position_str}최대화 버튼 클릭")
        elif "close" in comp_lower or "닫기" in comp_lower:
            steps.append(f"2. {position_str}닫기 버튼 클릭")
            # 후속 동작: 저장 확인 팝업
            steps.append("3. 팝업창 Save 버튼 클릭 (변경사항 있는 경우)")
        elif "save" in comp_lower or "저장" in comp_lower:
            steps.append(f"2. {position_str}저장 버튼 클릭")
        elif "cancel" in comp_lower or "취소" in comp_lower:
            steps.append(f"2. {position_str}취소 버튼 클릭")
        elif "search" in comp_lower or "검색" in comp_lower:
            steps.append(f"2. {position_str}검색 필드에 검색어 입력")
            steps.append("3. 검색 버튼 클릭 또는 Enter 키 입력")
        elif "delete" in comp_lower or "삭제" in comp_lower:
            steps.append("2. 삭제할 항목 선택")
            steps.append(f"3. {position_str}삭제 버튼 클릭")
            steps.append("4. 확인 팝업에서 확인 버튼 클릭")
        elif "add" in comp_lower or "추가" in comp_lower:
            steps.append(f"2. {position_str}추가 버튼 클릭")
            steps.append("3. 필요한 정보 입력")
            steps.append("4. 저장/확인 버튼 클릭")
        elif "refresh" in comp_lower or "새로고침" in comp_lower:
            steps.append(f"2. {position_str}새로고침 버튼 클릭")
        elif "back" in comp_lower or "뒤로" in comp_lower:
            steps.append(f"2. {position_str}뒤로가기 버튼 클릭")
        elif "undo" in comp_lower or "실행취소" in comp_lower:
            steps.append("2. 임의의 작업 수행")
            steps.append(f"3. {position_str}실행취소 버튼 클릭")
        elif "redo" in comp_lower or "다시실행" in comp_lower:
            steps.append("2. 임의의 작업 수행 후 실행취소")
            steps.append(f"3. {position_str}다시실행 버튼 클릭")
        else:
            # 일반 버튼
            steps.append(f"2. {position_str}{component_name} 버튼 클릭")

    elif test_type == "hover":
        steps.append(f"2. {position_str}{component_name}에 마우스 오버")
        steps.append("3. 툴팁 표시 대기 (1~2초)")

    elif test_type == "selection":
        steps.append(f"2. {component_name} 목록에서 항목 선택")
        steps.append("3. 선택 상태 확인")

    elif test_type == "close":
        steps.append(f"2. {position_str}닫기 버튼 클릭 또는 ESC 키 입력")

    elif test_type == "shortcut":
        shortcut = context.get("shortcut", "")
        if shortcut:
            steps.append(f"2. 단축키 [{shortcut}] 입력")
        else:
            steps.append("2. 해당 단축키 입력")

    elif test_type == "validation":
        steps.append(f"2. {component_name} 필드에 유효하지 않은 값 입력")
        steps.append("3. 저장/확인 시도")

    elif test_type == "boundary":
        steps.append(f"2. {component_name} 필드에 최소값 입력")
        steps.append("3. 결과 확인")
        steps.append(f"4. {component_name} 필드에 최대값 입력")
        steps.append("5. 결과 확인")

    else:
        steps.append(f"2. {position_str}{component_name} 동작 수행")

    return "\n".join(steps)


def _extract_position(component_name: str, description: str, visual_info: dict = None) -> str:
    """컴포넌트 설명에서 위치 정보 추출

    개선: 시각적 위치 데이터 우선 사용

    Args:
        component_name: 컴포넌트 이름
        description: 컴포넌트 설명
        visual_info: 이미지 분석에서 추출한 시각 정보 (선택)

    Returns:
        위치 문자열 (예: "좌측 상단", "우측 상단")
    """
    # 1. 시각적 위치 데이터 우선 사용
    if visual_info:
        visual_position = visual_info.get("position", "")
        if visual_position:
            # 영문 위치를 한글로 변환
            position_map = {
                "top-left": "좌측 상단",
                "top-center": "상단 중앙",
                "top-right": "우측 상단",
                "center-left": "좌측 중앙",
                "center": "중앙",
                "center-right": "우측 중앙",
                "bottom-left": "좌측 하단",
                "bottom-center": "하단 중앙",
                "bottom-right": "우측 하단",
                "header": "헤더 영역",
                "sidebar": "사이드바 영역",
                "footer": "푸터 영역",
                "main": "메인 콘텐츠 영역",
                "toolbar": "툴바 영역",
            }
            mapped = position_map.get(visual_position.lower().replace(" ", "-"), "")
            if mapped:
                return mapped
            # 이미 한글인 경우 그대로 반환
            if any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in visual_position):
                return visual_position

        # 레이아웃 영역 정보 사용
        layout_area = visual_info.get("layout_area", "")
        if layout_area:
            area_map = {
                "header": "헤더 영역",
                "title bar": "타이틀바 영역",
                "titlebar": "타이틀바 영역",
                "sidebar": "사이드바",
                "left panel": "좌측 패널",
                "right panel": "우측 패널",
                "main content": "메인 콘텐츠 영역",
                "footer": "하단 영역",
                "toolbar": "툴바",
                "menu bar": "메뉴바",
                "status bar": "상태 표시줄",
            }
            mapped = area_map.get(layout_area.lower(), "")
            if mapped:
                return mapped

    # 2. 텍스트 기반 위치 추출 (description에 명시된 경우만)
    # 화면정의서에 위치가 명시되어 있으면 추출
    text = f"{component_name} {description}".lower()

    # 한글 위치 키워드 (화면정의서에 명시된 경우)
    if "우측 상단" in text or "상단 우측" in text:
        return "우측 상단"
    elif "좌측 상단" in text or "상단 좌측" in text:
        return "좌측 상단"
    elif "우측 하단" in text or "하단 우측" in text:
        return "우측 하단"
    elif "좌측 하단" in text or "하단 좌측" in text:
        return "좌측 하단"
    elif "상단" in text:
        return "상단"
    elif "하단" in text:
        return "하단"
    elif "좌측" in text:
        return "좌측"
    elif "우측" in text:
        return "우측"
    elif "중앙" in text or "가운데" in text:
        return "가운데"

    # 위치 정보가 화면정의서에 없으면 빈 문자열 반환 (하드코딩된 추정 금지)
    return ""


def _get_special_precondition(component_name: str, component_type: str) -> str:
    """특수 컴포넌트의 Pre-condition 반환 (수작업 TC 스타일)

    개선된 Pre-condition 로직:
    - 기본 TC: Pre-condition 비움 (빈 문자열)
    - 특수 조건 필요시만 명시: "화면 최소화 상태", "작업내역 있음"

    Args:
        component_name: 컴포넌트 이름
        component_type: 컴포넌트 타입

    Returns:
        Pre-condition 문자열 (기본값: 빈 문자열)
    """
    comp_lower = component_name.lower() if component_name else ""

    # 특수 컴포넌트별 Pre-condition
    if "undo" in comp_lower or "실행취소" in comp_lower:
        return PRECONDITION_BY_TYPE.get("undo", "작업 내역이 있는 상태")
    elif "redo" in comp_lower or "다시실행" in comp_lower:
        return PRECONDITION_BY_TYPE.get("redo", "실행 취소된 작업이 있는 상태")
    elif "minimize" in comp_lower or "최소화" in comp_lower:
        # 최소화 복원 테스트의 경우
        return PRECONDITION_BY_TYPE.get("minimize", "화면이 최소화된 상태")
    elif "maximize" in comp_lower or "최대화" in comp_lower:
        # 최대화 복원 테스트의 경우
        return PRECONDITION_BY_TYPE.get("maximize", "화면이 최대화된 상태")
    elif component_type == "popup":
        # 팝업 닫기 테스트의 경우
        return PRECONDITION_BY_TYPE.get("popup", "팝업이 표시된 상태")

    # 기본값: Pre-condition 비움
    return ""


def generate_expected_result(component_name: str, test_type: str, description: str = "",
                             position: str = "", context: dict = None,
                             visual_info: dict = None) -> str:
    """Expected Result 생성 (수작업 스타일 - 여러 # 결과문장)

    Part 2 개선 사항:
    - 여러 `#` 결과문장 사용 (bullet 대신)
    - 부정 조건 명시 ("종료 안 됨", "저장되지 않고")
    - 구체적 UI 요소/문구 명시
    - 위치 정보 포함

    이미지 분석 개선:
    - 시각적 상태 변화 설명 추가
    - 색상/스타일 변화 명시

    Args:
        component_name: 컴포넌트 이름
        test_type: 테스트 유형
        description: 화면정의서의 상세 설명
        position: 위치 정보 (좌측 상단, 우측 상단 등)
        context: 추가 컨텍스트 정보 (hint, shortcut 등)
        visual_info: 이미지 분석에서 추출한 시각 정보 (선택)

    Returns:
        여러 "# 결과문장" 형식
    """
    context = context or {}
    visual_info = visual_info or {}
    results = []

    # 시각적 상태/스타일 정보 추출
    visual_state = visual_info.get("state", "")
    visual_style = visual_info.get("style", {})
    visual_color = visual_info.get("color", {})
    visual_desc = visual_info.get("visual_description", "")

    # description에서 유의미한 정보 추출
    clean_desc = description.strip()
    if clean_desc.startswith("#"):
        clean_desc = clean_desc[1:].strip()

    # description 라인들을 # 형식으로 변환
    desc_results = []
    if clean_desc:
        for line in clean_desc.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                # 유의미한 설명만 추가
                if len(line) > 3:
                    desc_results.append(f"# {line}")

    # 위치 정보 문자열
    position_str = f"{position}에 " if position else ""

    # 테스트 유형별 기대 결과 (수작업 스타일)
    if test_type == "ui":
        results.append(f"# {position_str}{component_name} 영역이 화면에 정상 표시됨")
        if desc_results:
            results.extend(desc_results[:2])  # 최대 2개의 description 결과 추가
        else:
            results.append(f"# {component_name} UI 요소가 디자인 명세와 일치함")

    elif test_type == "functional":
        # 컴포넌트별 구체적인 기능 결과
        comp_lower = component_name.lower()

        if "minimize" in comp_lower or "최소화" in comp_lower:
            results.append("# 화면이 최소화되며, 프로그램 종료 안 됨")
            results.append("# 프로그램이 작업 표시줄에 표시되며, 백그라운드에서 상태 유지됨")
        elif "maximize" in comp_lower or "최대화" in comp_lower:
            results.append("# 화면이 전체 화면으로 최대화됨")
            results.append("# 다시 클릭 시 원래 크기로 복원됨")
        elif "close" in comp_lower or "닫기" in comp_lower:
            results.append(f"# {component_name} 클릭 시 해당 창/팝업이 닫힘")
            results.append("# 저장되지 않은 데이터가 있는 경우 확인 팝업 표시됨")
        elif "save" in comp_lower or "저장" in comp_lower:
            results.append("# 입력/수정된 데이터가 정상적으로 저장됨")
            results.append("# 저장 완료 메시지 표시됨")
        elif "cancel" in comp_lower or "취소" in comp_lower:
            results.append("# 변경사항이 저장되지 않고 이전 상태로 복원됨")
            results.append("# 해당 화면/팝업이 닫힘")
        elif "search" in comp_lower or "검색" in comp_lower:
            results.append("# 검색 조건에 맞는 결과 목록이 표시됨")
            results.append("# 검색 결과가 없는 경우 '검색 결과 없음' 메시지 표시됨")
        elif "delete" in comp_lower or "삭제" in comp_lower:
            results.append("# 삭제 확인 팝업이 표시됨")
            results.append("# 확인 시 해당 항목이 삭제되며, 목록에서 제거됨")
        elif "add" in comp_lower or "추가" in comp_lower:
            results.append("# 새 항목 입력/추가 화면이 표시됨")
            results.append("# 입력 완료 후 목록에 새 항목이 추가됨")
        elif "refresh" in comp_lower or "새로고침" in comp_lower:
            results.append("# 현재 화면 데이터가 최신 상태로 갱신됨")
            results.append("# 로딩 인디케이터 표시 후 갱신 완료됨")
        elif "back" in comp_lower or "뒤로" in comp_lower:
            results.append("# 이전 화면으로 이동됨")
            results.append("# 저장되지 않은 변경사항이 있는 경우 확인 팝업 표시됨")
        elif "undo" in comp_lower or "실행취소" in comp_lower:
            results.append("# 마지막 작업이 취소됨")
            results.append("# 이전 상태로 복원됨")
        elif "redo" in comp_lower or "다시실행" in comp_lower:
            results.append("# 취소된 작업이 다시 실행됨")
            results.append("# 작업 결과가 화면에 반영됨")
        else:
            results.append(f"# {component_name} 클릭 시 해당 기능이 정상 동작함")
            if desc_results:
                results.extend(desc_results[:2])
            else:
                results.append("# 기대한 동작 결과가 화면에 반영됨")

    elif test_type == "hover":
        results.append(f"# {component_name}에 마우스 오버 시 커서 모양 변경됨")

        # 시각적 스타일 변화 추가 (이미지 분석 결과 활용)
        if visual_style:
            hover_style = visual_style.get("hover", {})
            if hover_style:
                bg_change = hover_style.get("background_color", "")
                border_change = hover_style.get("border_color", "")
                if bg_change:
                    results.append(f"# 버튼 Hover 시 배경색 변경됨 ({bg_change})")
                if border_change:
                    results.append(f"# 테두리 색상 변경됨 ({border_change})")

        if visual_color and visual_color.get("hover"):
            results.append(f"# Hover 시 색상 변경: {visual_color.get('hover')}")

        if context.get("hint"):
            results.append(f"# 툴팁 표시됨: \"{context['hint']}\"")
        else:
            results.append("# 해당 요소의 툴팁 또는 설명이 표시됨")
        results.append("# 마우스 아웃 시 원래 상태로 복귀됨")

    elif test_type == "validation":
        results.append("# 유효하지 않은 값 입력 시 오류 메시지 표시됨")
        results.append("# 유효하지 않은 값은 저장되지 않음")
        results.append("# 오류 필드가 시각적으로 강조 표시됨 (빨간색 테두리 등)")

    elif test_type == "boundary":
        results.append("# 최소값 입력 시 정상적으로 처리됨")
        results.append("# 최대값 입력 시 정상적으로 처리됨")
        results.append("# 범위 초과 값 입력 시 오류 메시지 표시되거나 자동 보정됨")

    elif test_type == "selection":
        results.append(f"# {component_name}에서 선택한 항목이 하이라이트됨")
        results.append("# 선택된 항목의 상세 정보가 관련 영역에 표시됨")
        results.append("# 다른 항목 선택 시 이전 선택이 해제됨")

    elif test_type == "close":
        results.append(f"# {component_name} 닫기 버튼 클릭 시 창/팝업이 닫힘")
        results.append("# ESC 키 입력 시에도 동일하게 닫힘")
        results.append("# 저장되지 않은 변경사항이 있는 경우 확인 팝업 표시됨")

    elif test_type == "shortcut":
        # 단축키 테스트 Expected Result
        shortcut = context.get("shortcut", "")
        if shortcut:
            results.append(f"# {shortcut} 단축키 입력 시 해당 기능이 정상 동작함")
        results.append("# 버튼 클릭과 동일한 동작이 수행됨")

    else:
        results.append(f"# {position_str}{component_name} 정상 동작 확인됨")
        if desc_results:
            results.extend(desc_results[:2])
        else:
            results.append("# 기대한 결과가 화면에 표시됨")

    return "\n".join(results)


# Depth4 테스트 조건/상태 매핑 (컴포넌트 타입 및 테스트 유형별)
DEPTH4_CONDITIONS = {
    # 버튼 관련 조건
    "button_functional": "활성화 상태",
    "button_disabled": "비활성화 상태",
    "button_hover": "마우스 오버 상태",
    "button_shortcut": "단축키 입력",
    # 입력 관련 조건
    "input_functional": "입력 가능 상태",
    "input_validation": "유효성 검증",
    "input_boundary": "경계값 입력",
    "input_empty": "빈 값 상태",
    # 목록 관련 조건
    "list_functional": "데이터 로딩 완료",
    "list_selection": "항목 선택",
    "list_empty": "데이터 없음",
    # 팝업 관련 조건
    "popup_functional": "팝업 표시됨",
    "popup_close": "닫기 동작",
    # 상태 관련 조건
    "undo": "작업내역 있음",
    "redo": "실행취소 내역 있음",
    "save": "변경사항 있음",
    "save_no_changes": "작업내역 없음",
    "minimize": "최소화 상태",
    "maximize": "최대화 상태",
    # 기본
    "default": "",
}


def extract_depth_structure(
    section: str,
    component_name: str,
    test_type: str = "",
    project_info: dict = None,
    component_type: str = ""
) -> Dict[str, str]:
    """Depth 구조 추출 (화면정의서 데이터 기반 - 하드코딩 없음)

    원칙: PPTX에서 추출된 데이터만 사용, 하드코딩된 키워드 매칭 금지

    Depth 구조:
    - Depth1: 프로젝트명/문서 제목 (project_info에서 추출)
    - Depth2: 섹션명 (PPTX 섹션 제목에서 번호 제거)
    - Depth3: 컴포넌트명
    - Depth4: 테스트 유형

    Args:
        section: 섹션 정보 (예: "01 공통 Layout 및 Tool 정리") - PPTX에서 추출된 원본
        component_name: 컴포넌트 이름 - PPTX에서 추출된 원본
        test_type: 테스트 유형 (functional, ui, hover 등)
        project_info: 프로젝트 정보 딕셔너리 - PPTX 헤더에서 추출
        component_type: 컴포넌트 타입 (button, input, list 등)

    Returns:
        depth1 ~ depth4 딕셔너리
    """
    if project_info is None:
        project_info = {}

    # === Depth1: 프로젝트명/문서 제목 (PPTX 헤더에서 추출) ===
    depth1 = ""
    if project_info.get("title"):
        depth1 = project_info.get("title")
    elif project_info.get("project_name"):
        depth1 = project_info.get("project_name")
    elif project_info.get("screen_id"):
        depth1 = project_info.get("screen_id")
    # project_info에 정보가 없으면 빈 문자열 유지 (하드코딩 금지)

    # === Depth2: 섹션명 (PPTX 섹션 제목에서 번호만 제거) ===
    depth2 = ""
    if section:
        # 앞의 번호 패턴만 제거 (예: "01 " → 제거), 나머지는 원본 유지
        clean_section = re.sub(r'^\d+[\.\s]*', '', section).strip()
        depth2 = clean_section if clean_section else section

    # === Depth3: 컴포넌트명 (PPTX에서 추출된 원본 그대로) ===
    depth3 = component_name.strip() if component_name else ""

    # === Depth4: 테스트 유형 (코드 로직으로 결정, 하드코딩 아님) ===
    depth4 = ""
    # 테스트 유형별 Depth4 라벨 (테스트 방법론 기반, 화면정의서 내용 아님)
    test_type_labels = {
        "ui": "표시 확인",
        "functional": "기능 확인",
        "hover": "Hover 확인",
        "validation": "유효성 확인",
        "boundary": "경계값 확인",
        "selection": "선택 확인",
        "close": "닫기 확인",
        "shortcut": "단축키 확인",
    }
    depth4 = test_type_labels.get(test_type, "")

    return {
        "depth1": depth1,
        "depth2": depth2,
        "depth3": depth3,
        "depth4": depth4
    }


def generate_testcases_for_component(
    component: dict,
    section: str,
    global_counter: int,
    id_prefix: str = "IT_OO",
    app_name: str = "OnePros",
    doc_name: str = "",
    version: str = "",
    project_info: dict = None
) -> List[TestCase]:
    """컴포넌트에 대한 테스트케이스 생성 (개선된 버전 - 수작업 TC 스타일)

    개선 사항:
    - TC ID: 순차 번호 방식 (전역 카운터 사용)
    - Title: 상세한 Title 형식 (`[Save] 버튼 클릭`, `저장 단축키 입력`)
    - Test Step: ">" 네비게이션 형식
    - Expected Result: 단일 "#" 접두사
    - Reference: 전체 문서 참조 형식
    - Depth 구조: 수작업 TC 스타일 (탭명/제품유형/기능그룹/테스트조건)
    - Pre-condition: 기본 TC는 비움, 특수 조건만 명시

    이미지 분석 개선:
    - visual_info를 활용한 정확한 위치 설명
    - 시각적 상태 변화 반영
    """

    if project_info is None:
        project_info = {}

    testcases = []
    comp_name = component.get("component", "")
    description = component.get("description", "")
    slide_number = component.get("slide_number", 1)

    # 이미지 분석 정보 추출 (있으면 사용)
    visual_info = component.get("visual_info", {})

    # 컴포넌트 타입 분류
    comp_type = classify_component_type(comp_name, description)

    # Depth 구조 추출 (개선된 형식 - project_info, comp_type 전달)
    depths_ui = extract_depth_structure(
        section=section,
        component_name=comp_name,
        test_type="ui",
        project_info=project_info,
        component_type=comp_type
    )

    # 네비게이션 경로 생성
    nav_path = _build_navigation_path(depths_ui["depth1"], depths_ui["depth2"], comp_name)

    # 상세한 Title 생성 (수작업 TC 스타일)
    detailed_title = generate_detailed_title(comp_name, description, "ui")

    # 타입별 사전 조건 (개선: 기본 TC는 빈 문자열)
    # 특수 컴포넌트(undo, redo, save 등)의 경우만 Pre-condition 설정
    base_pre_condition = _get_special_precondition(comp_name, comp_type)

    # Reference 형식 개선 (전체 문서 참조)
    if doc_name and version:
        reference = f"{doc_name} {version} 화면 정의서 {slide_number}P"
    elif doc_name:
        reference = f"{doc_name} 화면 정의서 {slide_number}P"
    else:
        reference = f"{app_name} 화면 정의서 {slide_number}P"

    counter = global_counter

    # 기본 TC 생성 (UI 표시 확인) - Part 2: 개선된 Test Step
    # 이미지 분석 정보 전달
    tc = TestCase(
        test_case_id=generate_test_id(id_prefix, counter),
        depth1=depths_ui["depth1"],
        depth2=depths_ui["depth2"],
        depth3=depths_ui["depth3"],
        depth4=depths_ui["depth4"],
        title=detailed_title,
        pre_condition=base_pre_condition,
        test_step=generate_test_step(comp_name, "ui", depths_ui, description, visual_info=visual_info),
        expected_result=generate_expected_result(comp_name, "ui", description, visual_info=visual_info),
        reference=reference
    )
    testcases.append(tc)
    counter += 1

    # 컴포넌트 타입에 따라 추가 TC 생성
    if comp_type == "button":
        # 버튼 기능 확인 TC (Depth4: 기능 확인)
        depths_func = extract_depth_structure(
            section=section,
            component_name=comp_name,
            test_type="functional",
            project_info=project_info,
            component_type=comp_type
        )
        func_title = generate_detailed_title(comp_name, description, "functional")
        # Part 2: 개선된 Test Step 사용 (visual_info 전달)
        tc_func = TestCase(
            test_case_id=generate_test_id(id_prefix, counter),
            depth1=depths_func["depth1"],
            depth2=depths_func["depth2"],
            depth3=depths_func["depth3"],
            depth4=depths_func["depth4"],
            title=func_title,
            pre_condition=base_pre_condition,
            test_step=generate_test_step(comp_name, "functional", depths_func, description, visual_info=visual_info),
            expected_result=generate_expected_result(comp_name, "functional", description, visual_info=visual_info),
            reference=reference
        )
        testcases.append(tc_func)
        counter += 1

    elif comp_type == "input":
        # 입력 기능 확인 TC (Depth4: 기능 확인)
        depths_func = extract_depth_structure(
            section=section,
            component_name=comp_name,
            test_type="functional",
            project_info=project_info,
            component_type=comp_type
        )
        func_title = generate_detailed_title(comp_name, description, "functional")
        # Part 2: 개선된 Test Step 사용 (visual_info 전달)
        tc_input = TestCase(
            test_case_id=generate_test_id(id_prefix, counter),
            depth1=depths_func["depth1"],
            depth2=depths_func["depth2"],
            depth3=depths_func["depth3"],
            depth4=depths_func["depth4"],
            title=func_title,
            pre_condition=base_pre_condition,
            test_step=generate_test_step(comp_name, "functional", depths_func, description, visual_info=visual_info),
            expected_result=generate_expected_result(comp_name, "functional", description, visual_info=visual_info),
            reference=reference
        )
        testcases.append(tc_input)
        counter += 1

    elif comp_type == "list":
        # 목록 선택 확인 TC (Depth4: 선택 확인)
        depths_select = extract_depth_structure(
            section=section,
            component_name=comp_name,
            test_type="selection",
            project_info=project_info,
            component_type=comp_type
        )
        select_title = generate_detailed_title(comp_name, description, "selection")
        # Part 2: 개선된 Test Step 사용 (visual_info 전달)
        tc_select = TestCase(
            test_case_id=generate_test_id(id_prefix, counter),
            depth1=depths_select["depth1"],
            depth2=depths_select["depth2"],
            depth3=depths_select["depth3"],
            depth4=depths_select["depth4"],
            title=select_title,
            pre_condition="",  # 기본 Pre-condition 비움
            test_step=generate_test_step(comp_name, "selection", depths_select, description, visual_info=visual_info),
            expected_result=generate_expected_result(comp_name, "selection", description, visual_info=visual_info),
            reference=reference
        )
        testcases.append(tc_select)
        counter += 1

    elif comp_type == "popup":
        # 팝업 닫기 확인 TC (Depth4: 닫기 확인)
        depths_close = extract_depth_structure(
            section=section,
            component_name=comp_name,
            test_type="close",
            project_info=project_info,
            component_type=comp_type
        )
        close_title = generate_detailed_title(comp_name, description, "close")
        # Part 2: 개선된 Test Step 사용 (visual_info 전달)
        tc_close = TestCase(
            test_case_id=generate_test_id(id_prefix, counter),
            depth1=depths_close["depth1"],
            depth2=depths_close["depth2"],
            depth3=depths_close["depth3"],
            depth4=depths_close["depth4"],
            title=close_title,
            pre_condition="팝업이 표시된 상태",
            test_step=generate_test_step(comp_name, "close", depths_close, description, visual_info=visual_info),
            expected_result=generate_expected_result(comp_name, "close", description, visual_info=visual_info),
            reference=reference
        )
        testcases.append(tc_close)
        counter += 1

    return testcases


# ===== Part 3: 단축키 TC 생성 함수 =====

def get_shortcut_for_component(component_name: str, description: str) -> Optional[str]:
    """컴포넌트 이름 또는 설명에서 단축키 정보를 추출

    Args:
        component_name: 컴포넌트 이름
        description: 설명 텍스트

    Returns:
        단축키 문자열 (예: "Ctrl+S") 또는 None
    """
    text = f"{component_name} {description}".lower()

    # 1. description에서 직접 단축키 추출 (Ctrl+X, F1 패턴)
    shortcut_match = re.search(r'(Ctrl\s*\+\s*\w+|Alt\s*\+\s*\w+|F\d+)', description, re.IGNORECASE)
    if shortcut_match:
        return shortcut_match.group(1).replace(" ", "")

    # 2. SHORTCUT_MAP에서 키워드 매칭
    for keyword, shortcut in SHORTCUT_MAP.items():
        if keyword in text:
            return shortcut

    return None


def generate_shortcut_testcase(
    component: dict,
    section: str,
    counter: int,
    id_prefix: str,
    reference: str,
    depths: Dict[str, str],
    nav_path: str
) -> Optional[TestCase]:
    """단축키 테스트케이스 생성

    버튼 TC와 함께 해당 기능의 단축키 TC를 자동 생성합니다.

    수작업 예시:
    - '저장 버튼 클릭' TC와 함께 '저장 단축키 입력 (Ctrl+S)' TC 생성
    - '환경설정 버튼 클릭' TC와 함께 '환경설정 단축키 입력 (F12)' TC 생성

    Args:
        component: 컴포넌트 정보
        section: 섹션명
        counter: TC 번호
        id_prefix: ID 접두사
        reference: 참조 문서
        depths: Depth 구조
        nav_path: 네비게이션 경로

    Returns:
        단축키 TestCase 또는 None (단축키가 없는 경우)
    """
    comp_name = component.get("component", "")
    description = component.get("description", "")

    # 단축키 정보 추출
    shortcut = get_shortcut_for_component(comp_name, description)
    if not shortcut:
        return None

    # 한글 키워드 찾기
    text_lower = f"{comp_name} {description}".lower()
    korean_name = None
    for keyword, title in TITLE_KEYWORD_MAP.items():
        if keyword in text_lower:
            korean_name = title
            break

    # Title 생성: "저장 단축키 입력 (Ctrl+S)"
    if korean_name:
        title = f"{korean_name} 단축키 입력 ({shortcut})"
    else:
        # 버튼 이름에서 접미사 제거
        btn_name = re.sub(r'(Button|Btn|버튼)\s*$', '', comp_name, flags=re.IGNORECASE).strip()
        title = f"[{btn_name}] 단축키 입력 ({shortcut})"

    # Test Step 생성
    test_step = f"1. {nav_path}\n2. 단축키 [{shortcut}] 입력"

    # Expected Result 생성
    expected_result = f"# 단축키 동작 정상\n- [{shortcut}] 입력 시 해당 기능 정상 실행됨\n- 버튼 클릭과 동일한 동작 수행"

    return TestCase(
        test_case_id=generate_test_id(id_prefix, counter),
        depth1=depths["depth1"],
        depth2=depths["depth2"],
        depth3=depths["depth3"],
        depth4="단축키 확인",
        title=title,
        pre_condition="",  # 기본 Pre-condition 비움
        test_step=test_step,
        expected_result=expected_result,
        reference=reference
    )


def generate_condition_variants(
    base_tc: TestCase,
    component: dict,
    counter_start: int,
    id_prefix: str
) -> List[TestCase]:
    """조건별 TC 분리 생성

    특정 컴포넌트의 경우 조건(작업내역 있음/없음 등)에 따라
    TC를 복제하여 조건별로 분리 생성합니다.

    수작업 예시:
    - 저장 팝업 테스트를 "작업내역 없음" / "작업내역 있음" 두 조건으로 분리
    - Depth4에 조건 명시
    - Pre-condition에 해당 조건 반영

    Args:
        base_tc: 원본 테스트케이스
        component: 컴포넌트 정보
        counter_start: 시작 TC 번호
        id_prefix: ID 접두사

    Returns:
        조건별로 분리된 TestCase 목록 (조건 분리 불필요시 빈 리스트)
    """
    comp_name = component.get("component", "")
    description = component.get("description", "")
    text_lower = f"{comp_name} {description}".lower()

    # 조건 분리가 필요한지 확인
    conditions = None
    for keyword, condition_list in CONDITION_PATTERNS.items():
        if keyword in text_lower:
            conditions = condition_list
            break

    if not conditions:
        return []

    # 조건별 TC 생성
    variant_testcases = []
    counter = counter_start

    for condition in conditions:
        # TC 복제 및 조건 반영
        variant_tc = TestCase(
            test_case_id=generate_test_id(id_prefix, counter),
            depth1=base_tc.depth1,
            depth2=base_tc.depth2,
            depth3=base_tc.depth3,
            depth4=condition,  # Depth4에 조건 명시
            title=f"{base_tc.title} ({condition})",
            pre_condition=condition,  # Pre-condition에 조건 반영
            test_step=base_tc.test_step,
            expected_result=_generate_condition_expected_result(base_tc.expected_result, condition),
            reference=base_tc.reference,
            requirement_id=base_tc.requirement_id,
            importance=base_tc.importance,
            writer=base_tc.writer
        )
        variant_testcases.append(variant_tc)
        counter += 1

    return variant_testcases


def _generate_condition_expected_result(base_expected: str, condition: str) -> str:
    """조건에 따른 Expected Result 생성

    Args:
        base_expected: 기본 Expected Result
        condition: 적용할 조건

    Returns:
        조건이 반영된 Expected Result
    """
    # 조건별 기대 결과 분기
    if condition == "작업내역 없음":
        if "저장" in base_expected or "save" in base_expected.lower():
            return "# 저장할 내용 없음 알림\n- '저장할 변경사항이 없습니다' 메시지 표시됨\n- 또는 저장 버튼 비활성화 상태"
        elif "닫기" in base_expected or "close" in base_expected.lower():
            return "# 프로그램 바로 종료\n- 저장 확인 팝업 없이 바로 종료됨"
        else:
            return base_expected + f"\n- 조건: {condition}"

    elif condition == "작업내역 있음":
        if "저장" in base_expected or "save" in base_expected.lower():
            return "# 저장 기능 정상 동작\n- 변경사항이 정상적으로 저장됨\n- 저장 완료 메시지 또는 상태 표시"
        elif "닫기" in base_expected or "close" in base_expected.lower():
            return "# 저장 확인 팝업 표시\n- '저장하시겠습니까?' 확인 팝업 표시됨\n- 예/아니오/취소 선택 가능"
        else:
            return base_expected + f"\n- 조건: {condition}"

    elif condition == "단일 항목 선택":
        return "# 단일 항목 삭제 동작\n- 선택한 1개 항목 삭제 확인 팝업 표시\n- 확인 시 해당 항목 삭제됨"

    elif condition == "다중 항목 선택":
        return "# 다중 항목 삭제 동작\n- 선택한 N개 항목 삭제 확인 팝업 표시\n- 확인 시 선택된 모든 항목 삭제됨"

    else:
        return base_expected + f"\n- 조건: {condition}"


# ===== 예외/에러 테스트케이스 패턴 =====

EXCEPTION_PATTERNS = {
    # 입력 관련 예외
    "input": [
        {
            "type": "empty",
            "title_suffix": "빈값 입력",
            "pre_condition": "입력 필드가 비어있는 상태",
            "test_step": "1. 필드를 비운 상태로 저장/확인 시도",
            "expected_result": "# 필수 입력 오류 메시지 표시됨"
        },
        {
            "type": "special_char",
            "title_suffix": "특수문자 입력",
            "pre_condition": "입력 필드 활성화 상태",
            "test_step": "1. 특수문자(!@#$%^&*) 입력\n2. 저장/확인 시도",
            "expected_result": "# 유효하지 않은 문자 오류 표시 또는 필터링됨"
        },
        {
            "type": "max_length",
            "title_suffix": "최대 길이 초과",
            "pre_condition": "입력 필드 활성화 상태",
            "test_step": "1. 허용 길이 초과 텍스트 입력\n2. 저장/확인 시도",
            "expected_result": "# 길이 제한 오류 또는 자동 잘림 처리됨"
        }
    ],
    # 데이터 관련 예외
    "list": [
        {
            "type": "no_data",
            "title_suffix": "데이터 없음",
            "pre_condition": "조회 결과가 없는 조건 설정",
            "test_step": "1. 결과가 없는 조건으로 조회",
            "expected_result": "# '데이터가 없습니다' 메시지 표시됨"
        },
        {
            "type": "deleted_data",
            "title_suffix": "삭제된 데이터 조회",
            "pre_condition": "이미 삭제된 데이터의 ID/키 보유",
            "test_step": "1. 삭제된 데이터 ID로 상세 조회 시도",
            "expected_result": "# '존재하지 않는 데이터' 오류 표시됨"
        }
    ],
    # 버튼/기능 관련 예외
    "button": [
        {
            "type": "disabled_click",
            "title_suffix": "비활성 버튼 클릭",
            "pre_condition": "버튼이 비활성화(disabled) 상태",
            "test_step": "1. 비활성화된 버튼 클릭 시도",
            "expected_result": "# 버튼 클릭 불가, 반응 없음"
        },
        {
            "type": "double_click",
            "title_suffix": "중복 클릭",
            "pre_condition": "버튼 활성화 상태",
            "test_step": "1. 버튼 빠르게 2회 이상 연속 클릭",
            "expected_result": "# 중복 실행 방지됨 또는 1회만 실행됨"
        }
    ],
    # 네트워크/시스템 예외
    "system": [
        {
            "type": "timeout",
            "title_suffix": "응답 지연",
            "pre_condition": "네트워크 지연 상황 시뮬레이션",
            "test_step": "1. 서버 응답 지연 상황에서 기능 실행",
            "expected_result": "# 로딩 표시 후 타임아웃 메시지 표시됨"
        },
        {
            "type": "connection_lost",
            "title_suffix": "연결 끊김",
            "pre_condition": "네트워크 연결 차단",
            "test_step": "1. 네트워크 연결 끊긴 상태에서 기능 실행",
            "expected_result": "# 연결 오류 메시지 표시됨"
        }
    ]
}


def generate_exception_testcases(
    component: dict,
    section: str,
    global_counter: int,
    id_prefix: str = "IT_OO",
    doc_name: str = "",
    version: str = ""
) -> List[TestCase]:
    """예외/에러 테스트케이스 생성

    컴포넌트 타입에 따라 적절한 예외 케이스 생성.

    Args:
        component: 컴포넌트 정보
        section: 섹션명
        global_counter: 전역 카운터
        id_prefix: ID 접두사
        doc_name: 문서명
        version: 버전

    Returns:
        예외 테스트케이스 목록
    """
    testcases = []
    comp_name = component.get("component", "")
    description = component.get("description", "")
    slide_number = component.get("slide_number", 1)

    # 컴포넌트 타입 분류
    comp_type = classify_component_type(comp_name, description)

    # Depth 구조 추출
    depths = extract_depth_structure(section, comp_name)

    # Reference 형식
    if doc_name and version:
        reference = f"{doc_name} {version} 화면 정의서 {slide_number}P"
    else:
        reference = f"화면 정의서 {slide_number}P"

    # 컴포넌트 타입에 해당하는 예외 패턴 적용
    exception_list = EXCEPTION_PATTERNS.get(comp_type, [])

    counter = global_counter
    for pattern in exception_list:
        tc = TestCase(
            test_case_id=generate_test_id(id_prefix, counter),
            depth1=depths["depth1"],
            depth2=depths["depth2"],
            depth3="예외 테스트",
            depth4=pattern["type"],
            title=f"{comp_name} {pattern['title_suffix']}",
            pre_condition=pattern["pre_condition"],
            test_step=pattern["test_step"].format(component=comp_name),
            expected_result=pattern["expected_result"],
            reference=reference
        )
        testcases.append(tc)
        counter += 1

    return testcases


def generate_testcases(
    extracted_data: dict,
    id_prefix: str = "IT_OO",
    include_exceptions: bool = False,
    include_shortcuts: bool = True,
    include_conditions: bool = True
) -> List[TestCase]:
    """추출된 데이터로 전체 테스트케이스 생성 (개선된 버전)

    개선 사항:
    - 전역 순차 카운터 사용 (IT_OP_001, IT_OP_002, ...)
    - 프로젝트 정보 전달 강화 (doc_name, version)
    - 예외 테스트케이스 생성 옵션 추가
    - Part 3: 단축키 TC 자동 생성 옵션 추가
    - Part 3: 조건별 TC 분리 옵션 추가

    Args:
        extracted_data: 추출된 PPTX 데이터
        id_prefix: 테스트케이스 ID 접두사
        include_exceptions: 예외 테스트케이스 포함 여부
        include_shortcuts: 단축키 테스트케이스 포함 여부 (기본: True)
        include_conditions: 조건별 TC 분리 포함 여부 (기본: True)

    Returns:
        테스트케이스 목록
    """

    all_testcases = []

    # 프로젝트 정보에서 앱 이름, 문서명, 버전 추출
    project_info = extracted_data.get("project_info", {})
    app_name = project_info.get("project_name", "OnePros")
    doc_name = project_info.get("title", app_name)
    version = project_info.get("version", "")

    if not app_name:
        app_name = "OnePros"

    # 전역 순차 카운터 (1부터 시작)
    global_counter = 1

    for component in extracted_data.get("all_components", []):
        section = component.get("section", "")
        comp_name = component.get("component", "")
        description = component.get("description", "")
        slide_number = component.get("slide_number", 1)

        # 컴포넌트 타입 분류
        comp_type = classify_component_type(comp_name, description)

        # Depth 구조 추출 (개선된 버전 - project_info, comp_type 전달)
        depths = extract_depth_structure(
            section=section,
            component_name=comp_name,
            test_type="ui",
            project_info=project_info,
            component_type=comp_type
        )

        # 네비게이션 경로 생성
        nav_path = _build_navigation_path(depths["depth1"], depths["depth2"], comp_name)

        # Reference 형식
        if doc_name and version:
            reference = f"{doc_name} {version} 화면 정의서 {slide_number}P"
        elif doc_name:
            reference = f"{doc_name} 화면 정의서 {slide_number}P"
        else:
            reference = f"{app_name} 화면 정의서 {slide_number}P"

        # 기본 테스트케이스 생성 (project_info 전달)
        tc_list = generate_testcases_for_component(
            component=component,
            section=section,
            global_counter=global_counter,
            id_prefix=id_prefix,
            app_name=app_name,
            doc_name=doc_name,
            version=version,
            project_info=project_info
        )

        all_testcases.extend(tc_list)
        global_counter += len(tc_list)

        # Part 3: 단축키 TC 생성 (버튼 타입인 경우)
        if include_shortcuts and comp_type == "button":
            shortcut_tc = generate_shortcut_testcase(
                component=component,
                section=section,
                counter=global_counter,
                id_prefix=id_prefix,
                reference=reference,
                depths=depths,
                nav_path=nav_path
            )
            if shortcut_tc:
                all_testcases.append(shortcut_tc)
                global_counter += 1

        # Part 3: 조건별 TC 분리 (해당 컴포넌트인 경우)
        if include_conditions and tc_list:
            # 마지막 기능 TC를 기준으로 조건별 분리
            base_tc = tc_list[-1]
            condition_tc_list = generate_condition_variants(
                base_tc=base_tc,
                component=component,
                counter_start=global_counter,
                id_prefix=id_prefix
            )
            if condition_tc_list:
                all_testcases.extend(condition_tc_list)
                global_counter += len(condition_tc_list)

        # 예외 테스트케이스 생성 (옵션)
        if include_exceptions:
            exception_tc_list = generate_exception_testcases(
                component=component,
                section=section,
                global_counter=global_counter,
                id_prefix=id_prefix,
                doc_name=doc_name,
                version=version
            )
            all_testcases.extend(exception_tc_list)
            global_counter += len(exception_tc_list)

    return all_testcases


def testcases_to_dict(testcases: List[TestCase]) -> List[dict]:
    """테스트케이스 리스트를 딕셔너리 리스트로 변환"""
    return [asdict(tc) for tc in testcases]


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_testcase.py <extracted_json> [output_json] [id_prefix]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    id_prefix = sys.argv[3] if len(sys.argv) > 3 else "IT_OO"

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        extracted_data = json.load(f)

    testcases = generate_testcases(extracted_data, id_prefix)
    result = {
        "project_info": extracted_data.get("project_info", {}),
        "total_testcases": len(testcases),
        "testcases": testcases_to_dict(testcases)
    }

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Generated {len(testcases)} test cases. Output saved to: {output_path}")
    else:
        print(output_json)

    return result


if __name__ == "__main__":
    main()
