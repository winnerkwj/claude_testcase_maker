# 테스트케이스 생성 스킬

<command-name>testcase</command-name>

화면정의서(PPTX)를 분석하여 테스트케이스를 자동 생성합니다.

## 핵심 변경: 에이전트 위임 방식

**기존 방식**: 메인 컨텍스트에서 Claude가 직접 분석 (컨텍스트 소모 큼)
**새로운 방식**: Task 도구로 에이전트에게 위임 (메인 컨텍스트 절약)

### 에이전트 위임 이점

- **메인 컨텍스트 절약**: TC 작성 상세 과정이 에이전트 내부에서만 처리
- **요약만 반환**: 결과 요약만 사용자에게 표시
- **독립적 실행**: Phase 1~4 전체를 에이전트가 자율적으로 수행

### 핵심 원칙

1. **전체 문서 파악 우선**: PPTX 전체 구조를 먼저 이해
2. **페이지 순서대로 TC 작성**: 화면정의서 페이지 번호 순서 유지
3. **Claude가 판단하여 TC 작성**: 규칙 기반이 아닌 이해 기반
4. **크로스 레퍼런스 자동 추가**: 기능 설명 부족 시 관련 페이지 참조
5. **Reference = 페이지 번호만**: `"5P"` 형식
6. **레퍼런스 하드코딩 금지**: 사용자 요청 시에만 수동 추가

### 하드코딩 금지

**모든 TC 내용은 화면정의서(PPTX)에서 추출된 데이터만 사용합니다.**

| 허용 | 금지 |
|------|------|
| PPTX 섹션 제목 그대로 사용 | "Tool 탭", "Alignment 탭" 등 추정 |
| PPTX Description 그대로 사용 | 컴포넌트별 위치 추정 (최소화=우측상단) |
| 테스트 유형 라벨 (표시 확인 등) | 키워드 매칭으로 탭명 추출 |

### Depth 구조 (화면정의서 기반)

| Depth | 소스 | 예시 |
|-------|------|------|
| Depth1 | PPTX 헤더의 제목/프로젝트명 | "Main Layout" |
| Depth2 | PPTX 섹션 제목 (번호 제거) | "공통 Layout 및 Tool 정리" |
| Depth3 | PPTX 컴포넌트명 | "Save", "최소화" |
| Depth4 | 테스트 유형 (코드 로직) | "표시 확인", "기능 확인" |

## 트리거

- `/testcase`
- `/tc`

## 사용법

```
/testcase <PPTX_파일_경로> [--prefix IT_XX]
```

## 워크플로우 (에이전트 위임)

메인 컨텍스트 절약을 위해 Task 도구로 에이전트에게 위임합니다.

### Step 1: [메인] 파일 확인
- PPTX 파일 존재 여부 확인
- 옵션 파싱 (--prefix 등)
- 사용자에게 "에이전트에게 위임 중..." 메시지 출력

### Step 2: [에이전트] TC 생성
Task 도구로 `general-purpose` 에이전트에게 전체 TC 생성 위임:
- Phase 1~4 전체 수행
- tc_data.json 생성
- Excel 출력
- 요약 반환

### Step 3: [메인] 결과 출력
에이전트 반환값에서 요약만 사용자에게 출력

---

## 에이전트 프롬프트 템플릿

```
화면정의서 PPTX에서 테스트케이스를 생성해주세요.

PPTX 파일: {pptx_path}
출력 폴더: {output_dir}
TC ID 접두사: {prefix}
스크립트 폴더: {scripts_dir}

### 수행할 작업:

1. **PPTX 데이터 추출** (Phase 1)
   cd "{scripts_dir}"
   py extract_images.py "{pptx_path}" --output "{output_dir}" --quiet
   py extract_pptx.py "{pptx_path}" "{output_dir}/pptx_data.json"

2. **문서 구조 파악** (Phase 2)
   - {output_dir}/pptx_data.json 읽기
   - project_info에서 프로젝트명, 버전 추출
   - all_components에서 컴포넌트 목록 파악
   - Description 내 [번호] 참조로 크로스 레퍼런스 매핑

3. **TC 작성** (Phase 3)
   - 페이지 순서대로 TC 작성
   - TC ID: {prefix}_001, {prefix}_002, ...
   - Reference: 1P, 2P, ... (크로스 레퍼런스: "1P (참조: [11-1])")
   - {output_dir}/tc_data.json에 저장

4. **Excel 출력** (Phase 4)
   py write_excel.py "{output_dir}/tc_data.json" "{output_dir}/{project_name}_TestCases.xlsx"

### TC 작성 판단 기준:
- 표시 확인: 모든 UI 컴포넌트에 기본 생성
- 기능 확인: 버튼, 탭, 입력 등 동작 가능한 요소
- 단축키 확인: Description에 "단축키", "Hint" 포함 시
- Hover 확인: "Mouse Enter", "Hover", "툴팁" 언급 시
- 비활성화 확인: "비활성화", "disabled" 조건 언급 시
- 팝업 확인: "[번호]" 형식 팝업 참조 시

### 크로스 레퍼런스 판단 기준:
- Description에 [번호] 또는 [번호-번호] 형식 참조 시
- "p.XX 참고", "XX페이지 참조" 문구 발견 시
- 동일 기능이 다른 페이지에서 상세 설명될 때

### 반환할 요약:
- 프로젝트명, 버전
- 총 TC 수
- 페이지별 TC 분포
- 크로스 레퍼런스 현황
- 출력 파일 경로
```

---

## Phase 상세 (에이전트 내부 실행)

### Phase 1: PPTX 데이터 추출 (스크립트 사용)

```bash
cd "{scripts_dir}"

# 1-1. 이미지 추출 (슬라이드 내 이미지/아이콘)
py extract_images.py "{pptx_path}" --output "{output_dir}" --quiet

# 1-2. 텍스트 데이터 추출 (컴포넌트 정보)
py extract_pptx.py "{pptx_path}" "{output_dir}/pptx_data.json"
```

**출력 파일:**
- `output/images/` - 슬라이드 내 이미지
- `output/image_manifest.json` - 이미지 메타데이터
- `output/pptx_data.json` - PPTX 텍스트/컴포넌트 정보

### Phase 2: 전체 문서 구조 파악 (Claude)

Claude가 `pptx_data.json`을 분석하여:
- 프로젝트 정보 확인 (프로젝트명, 버전, 문서번호)
- 총 페이지 수 및 섹션 구분
- 컴포넌트 목록 파악 (No, Component, Description)
- 관련 페이지 간 연관성 매핑 (크로스 레퍼런스 준비)

### Phase 3: 페이지별 TC 작성 (Claude)

페이지 순서대로 Claude가 직접 TC 작성:

1. 해당 페이지의 컴포넌트 목록 확인
2. Description 기반 기능 이해
3. 테스트 시나리오 판단 (표시/기능/단축키/Hover 등)
4. TC 작성 (Depth, Title, Step, Expected Result)
5. `[번호]` 형식 참조 발견 시 → 크로스 레퍼런스 추가
6. `output/tc_data.json`에 저장

### Phase 4: Excel 출력 (스크립트 사용)

```bash
py write_excel.py "{output_dir}/tc_data.json" "{output_dir}/{project_name}_TestCases.xlsx"
```

## TC 형식 (수작업 TC 스타일)

### TC ID
```
IT_[PREFIX]_[순번]
예: IT_OP_001, IT_OP_002
```
- 순번은 문서 전체에서 연속 (001, 002, 003...)
- 페이지별로 초기화하지 않음

### Depth 구조 (4단계 활용)

| Depth | 역할 | 예시 |
|-------|------|------|
| Depth1 | 기능 탭명 | Alignment, Design, Tool |
| Depth2 | 제품 유형 | Single Crown, Bridge, 공통 |
| Depth3 | 기능 그룹 | 공통 Layout 및 Tool 정리 |
| Depth4 | 테스트 조건/상태 | 표시 확인, 작업내역 있음, 단축키 확인 |

### Title 형식
```
[Save] 버튼 클릭
저장 단축키 입력 (Ctrl+S)
[최소화] 표시 확인
```
- 버튼명 명시: `[컴포넌트명]`
- 동작 방식 구분: 버튼 클릭 vs 단축키 입력

### Pre-condition
- **기본 TC**: 비움 (Pre-condition 없음)
- **특수 조건만 명시**:
  - `팝업이 표시된 상태`
  - `작업내역 있음`
  - `화면이 최소화된 상태`

### Test Step 형식
```
1. Alignment 탭 화면 진입
2. 화면 우측 상단 (타이틀바 영역) 최소화 버튼 클릭
```
- **위치 명시**: 좌측 상단, 우측 상단, 가운데 등 (이미지 분석 기반)
- **레이아웃 영역**: 타이틀바, 툴바, 사이드바 등
- **단계별 구체적 동작**
- **후속 동작 포함**: 팝업 버튼 클릭 등

### Expected Result 형식
```
# 화면이 최소화되며, 프로그램 종료 안 됨
# 버튼 Hover 시 배경색 변경됨 (밝은 회색 → 진한 회색)
# 프로그램이 작업 표시줄에 표시되며, 백그라운드에서 상태 유지됨
```
- **여러 `#` 결과문장** (bullet 대신)
- **시각적 상태 변화 설명**: 색상, 스타일 변화
- **부정 조건 명시**: "종료 안 됨", "저장되지 않고"

### Reference 형식 (핵심 변경)

**기본 형식**: 페이지 번호만
```
5P
```

**크로스 레퍼런스 형식**: 기능 설명 부족 시 관련 페이지 참조
```
5P (참조: 3P, 8P)
```

**예시:**
| 상황 | Reference |
|------|-----------|
| 단순 페이지 참조 | `5P` |
| 관련 팝업이 다른 페이지에 | `5P (참조: 13P)` |
| 여러 페이지 연관 | `5P (참조: 3P, 8P)` |

**크로스 레퍼런스 추가 기준:**
- 현재 페이지에서 설명이 불충분할 때
- "상세 내용은 XX 참조" 같은 문구가 있을 때
- 동일 기능이 다른 페이지에서 더 상세히 설명될 때

## Claude TC 작성 가이드라인

### TC 작성 시 Claude의 판단 기준

1. **페이지 내용 이해**
   - 화면 구성 요소 파악
   - 기능 동작 방식 이해
   - 사용자 시나리오 추론

2. **TC 항목 결정**
   - 표시 확인: UI 요소가 올바르게 표시되는지
   - 기능 확인: 버튼/입력 등이 정상 동작하는지
   - Hover 확인: 마우스오버 효과
   - 유효성 확인: 입력값 검증

3. **크로스 레퍼런스 판단**
   - 현재 페이지 설명이 불충분한 경우
   - 동일 컴포넌트가 다른 페이지에 있는 경우
   - 관련 기능이 다른 페이지에서 상세 설명된 경우

### TC 작성 예시

**페이지 5 분석 결과:**
| 필드 | 값 |
|------|-----|
| TC ID | IT_OP_001 |
| Reference | 5P |
| Depth1 | Main Layout |
| Depth2 | 공통 Tool |
| Depth3 | Save 버튼 |
| Depth4 | 기능 확인 |
| Title | [Save] 버튼 클릭 |
| Pre-condition | |
| Test Step | 1. 메인 화면 진입<br>2. Save 버튼 클릭 |
| Expected Result | # 작업 내용이 저장됨 |

**크로스 레퍼런스 예시 (페이지 5, 관련 페이지 13):**
| 필드 | 값 |
|------|-----|
| Reference | 5P (참조: 13P) |
| Note | 저장 확인 팝업 상세 내용은 13P 참조 |

### 자동 고려 항목

Claude가 TC 작성 시 자동으로 고려하는 항목:

**단축키 (해당 기능에 단축키가 있는 경우):**
| 기능 | 단축키 |
|------|--------|
| 저장 | Ctrl+S |
| 닫기 | Alt+F4 |
| 환경설정 | F12 |
| 도움말 | F1 |
| 실행취소 | Ctrl+Z |
| 다시실행 | Ctrl+Y |
| 새로고침 | F5 |

**조건별 분리 (필요 시):**
| 기능 | 조건 분리 |
|------|----------|
| 저장/닫기 | `작업내역 없음` / `작업내역 있음` |
| 삭제 | `단일 항목 선택` / `다중 항목 선택` |

## 파일 구조

```
testcase-generator/
├── scripts/
│   ├── extract_images.py       # 이미지 추출 (Phase 1)
│   ├── extract_pptx.py         # PPTX 텍스트/컴포넌트 추출 (Phase 1)
│   ├── write_excel.py          # Excel 출력 (Phase 4)
│   ├── run_all.py              # 기존 통합 실행 (레거시)
│   ├── merge_analysis.py       # 분석 결과 병합 (레거시)
│   └── generate_testcase.py    # TC 생성 (레거시)
├── output/
│   ├── images/                 # 추출된 이미지 (슬라이드별)
│   ├── image_manifest.json     # 이미지 메타데이터
│   ├── pptx_data.json          # PPTX 텍스트/컴포넌트 데이터
│   └── tc_data.json            # Claude가 작성한 TC 데이터
└── SKILL.md
```

## 보안 기능

| 항목 | 구현 |
|------|------|
| 외부 API 호출 없음 | Claude Code 내장 기능 사용 |
| 로컬 파일만 처리 | 네트워크 통신 없음 |
| 임시 파일 정리 | --cleanup 옵션 |
| 버전 관리 제외 | .gitignore 자동 생성 |
| 사용자 경고 | 실행 시 보안 알림 |

## 실행 워크플로우 상세 (에이전트 위임)

### 메인 컨텍스트 역할 (간소화)

```
1. 파일 확인
   - PPTX 파일 존재 확인
   - 옵션 파싱

2. 에이전트 위임
   - Task 도구로 general-purpose 에이전트 호출
   - 프롬프트 템플릿에 경로/옵션 채워서 전달

3. 결과 출력
   - 에이전트 반환값 요약 출력
```

### 에이전트 역할 (전체 TC 생성)

에이전트가 Phase 1~4 전체를 자율적으로 수행:
- `pptx_data.json` 생성
- 문서 구조 파악
- TC 작성 및 `tc_data.json` 저장
- Excel 출력
- 요약 반환

## 결과 출력 (간소화)

```
[TC 생성] 에이전트에게 위임 중...

============================================================
  테스트케이스 생성 완료
============================================================
프로젝트: OnePros (Ver 1.0)
총 TC: 42개
- 1P: 32개 TC
- 2P: 10개 TC
크로스 레퍼런스: 5건
출력: output/OnePros_TestCases.xlsx
============================================================
```

## TC 데이터 JSON 형식

Claude가 생성하는 TC 데이터 형식 (실제 테스트 결과 기반):

```json
{
  "project_info": {
    "project_name": "OnePros",
    "version": "Ver 1.0",
    "title": "Single Crown 화면정의서",
    "document_structure": {
      "total_pages": 2,
      "sections": ["공통 Layout 및 Tool 정리"],
      "cross_references": {
        "1P": ["11-1 저장 확인 팝업"],
        "2P": ["17-1 치식 하이라이트"]
      }
    }
  },
  "total_testcases": 42,
  "testcases": [
    {
      "test_case_id": "IT_OP_001",
      "depth1": "공통 Layout",
      "depth2": "공통 Layout 및 Tool 정리",
      "depth3": "Title",
      "depth4": "표시 확인",
      "title": "[Title] 표시 확인",
      "pre_condition": "",
      "test_step": "1. OnePros 프로그램 실행\n2. 메인 화면 상단 Title 영역 확인",
      "expected_result": "# OnePros 이름이 표시됨",
      "requirement_id": "",
      "reference": "1P",
      "importance": "",
      "writer": ""
    },
    {
      "test_case_id": "IT_OP_020",
      "depth1": "공통 Layout",
      "depth2": "공통 Layout 및 Tool 정리",
      "depth3": "닫기 버튼",
      "depth4": "기능 확인",
      "title": "[닫기] 버튼 클릭",
      "pre_condition": "",
      "test_step": "1. OnePros 프로그램 실행\n2. 닫기 버튼 클릭",
      "expected_result": "# OnePros 프로그램 창 닫기 시도됨\n# 저장 유무 관계없이 프로젝트 저장 확인 팝업창이 표시됨",
      "requirement_id": "",
      "reference": "1P (참조: [11-1] 팝업)",
      "importance": "",
      "writer": ""
    }
  ]
}
```

---

## 자동 실행 체이닝 (에이전트 위임)

TC 생성 완료 후 자동으로 다음 단계 실행:

```
/testcase 실행
    ↓
[메인] 파일 확인 + 옵션 파싱
    ↓
[메인] Task 도구로 에이전트 위임
    ↓
[에이전트] Phase 1~4 전체 수행
    ↓
[메인] 에이전트 결과 요약 출력
    ↓
/validate-tc 자동 실행 (검증)
    ↓
검증 통과 시 → /tc-stats 자동 출력
검증 실패 시 → 문제 해결 가이드 자동 참조
```

---

## 트리거 키워드 매핑

| 사용자 표현 | 자동 실행 스킬 |
|------------|---------------|
| "TC 만들어줘", "테스트케이스 생성" | /testcase |
| "이미지 추출", "이미지 분석" | /extract-images |
| "검증해줘", "확인해줘", "체크" | /validate-tc |
| "통계", "요약", "몇 개?" | /tc-stats |

---

## 문제 해결 가이드

### 오류 발생 시 대응

| 오류 메시지 | 원인 | 해결 |
|------------|------|------|
| `FileNotFoundError` | PPTX 경로 오류 | 절대 경로로 재지정 |
| `KeyError: 'slides'` | PPTX 형식 오류 | 파일 손상 확인 |
| `UnicodeDecodeError` | 인코딩 문제 | UTF-8로 재저장 |
| `PermissionError` | 파일 잠금 | 기존 Excel 닫기 |
| `openpyxl.utils.exceptions` | 템플릿 손상 | template.xlsx 복원 |
| `JSONDecodeError` | TC JSON 오류 | JSON 형식 검증 |
| 이미지 분석 실패 | 이미지 손상 | 해당 슬라이드 건너뛰기 |

### 디버깅 명령어

```bash
# 이미지 추출만 실행
py extract_images.py "파일.pptx" --output "output" --quiet

# 텍스트/컴포넌트 추출만 실행
py extract_pptx.py "파일.pptx" "output/pptx_data.json"

# Excel 출력만 실행
py write_excel.py "output/tc_data.json" "output/test.xlsx"
```

---

## 검증 워크플로우 (/validate-tc)

생성 완료 후 자동 검증 항목:

1. **TC 총 개수 출력**
2. **Depth 누락 항목 리스트**
3. **중복 TC ID 검출**
4. **페이지 순서 확인** (새 항목)
5. **Reference 형식 확인** (새 항목)
6. **형식 오류 하이라이트**
   - Expected Result가 `#`으로 시작하지 않음
   - Reference가 `숫자P` 형식이 아님
   - Pre-condition 형식 불일치

### 검증 결과 예시
```
============================================================
  TC 검증 결과
============================================================
총 TC: 42개
✓ TC ID 연속성: 정상 (IT_OP_001 ~ IT_OP_042)
✓ Depth 완전성: 정상
✓ 페이지 순서: 정상 (1P → 2P 순서 유지)
✓ Reference 형식: 정상 (5건 크로스 레퍼런스 포함)
✓ Expected Result 형식: 정상 (모두 # 시작)
------------------------------------------------------------
```

---

## 통계 워크플로우 (/tc-stats)

### 출력 정보

1. **전체 요약**
   - 총 TC 수
   - 페이지별 TC 분포
   - 테스트 유형별 분포

2. **페이지별 분포**
```
페이지별 TC 분포:
- 1P: 32개 TC (Title, Patient info, 탭 버튼, 최소화/최대화/닫기, Save, 환경설정, 정보)
- 2P: 10개 TC (Back, Next, Dental chart, Task tool, Object list)
```

3. **테스트 유형별 분포**
```
테스트 유형별 분포:
- 표시 확인: 20개 (48%)
- 기능 확인: 14개 (33%)
- 단축키 확인: 4개 (10%)
- Hover 확인: 1개 (2%)
- 기타: 3개 (7%)
```

4. **크로스 레퍼런스 현황**
```
크로스 레퍼런스: 5건
- 1P 닫기 → [11-1] 저장 확인 팝업 (Save/Don't Save/Cancel)
- 2P Dental chart → [17-1] 치식 하이라이트
```
