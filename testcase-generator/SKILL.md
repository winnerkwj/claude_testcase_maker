# 테스트케이스 생성 스킬

<command-name>testcase</command-name>

화면정의서(PPTX)를 분석하여 테스트케이스를 자동 생성합니다.

---

## ⚠️ 실수 방지 체크리스트 (반드시 확인!)

### 🚫 절대 금지

| 금지 항목 | 이유 |
|----------|------|
| `run_all.py` 호출 | 레거시 스크립트, 규칙 기반 TC 생성 |
| `generate_testcase.py` 호출 | 레거시 스크립트, 템플릿 기반 |
| 메인 컨텍스트에서 TC 직접 작성 | 컨텍스트 낭비, 에이전트에 위임 |
| pptx_data.json 내용 직접 읽기 | 컨텍스트 낭비, 에이전트가 읽음 |

### ⚠️ 필드명 규칙 (중요!)

**write_excel.py가 인식하는 필드명** (청크 에이전트가 사용해야 할 이름):

| 필드 | 올바른 키 | 잘못된 키 (사용 금지) |
|------|----------|---------------------|
| 테스트 절차 | `test_step` | `steps` |
| 기대 결과 | `expected_result` | `expected` |
| 사전 조건 | `pre_condition` | `precondition` |

**참고**: `merge_tc_chunks.py`가 잘못된 키를 자동 변환하지만, 에이전트 프롬프트에서 올바른 키 사용을 권장

### ✅ 필수 확인

1. **청크 에이전트가 TC 작성**: Claude가 pptx_data.json을 분석하고 **사고하여** TC 작성
2. **🖼️ 이미지 분석 필수**: 에이전트가 `output/images/` 폴더의 이미지를 Read로 분석
3. **JSON 키 형식**: 청크 파일에서 `testcases` 키 사용 (NOT `test_cases`)
4. **메인 역할**: 오케스트레이션만 (스크립트 실행, 에이전트 디스패치, 결과 수집)

### 📋 메인 컨텍스트 최소화

메인 컨텍스트에서 하는 일:
- ✅ 스크립트 실행 (Bash)
- ✅ 에이전트 디스패치 (Task)
- ✅ 결과 요약 출력

메인 컨텍스트에서 하면 안 되는 일:
- ❌ pptx_data.json 내용 Read로 읽기
- ❌ chunk_plan.json 내용 Read로 읽기 (청크 수만 확인)
- ❌ TC 내용 직접 작성
- ❌ 각 청크 결과 상세 확인

---

## 핵심 변경: 청크 기반 병렬 처리

**기존 방식**: 단일 에이전트가 전체 문서 처리 (컨텍스트 초과 위험)
**새로운 방식**: 문서를 청크로 분할하여 병렬 에이전트로 처리 (안정적)

### 청크 기반 처리 이점

- **컨텍스트 초과 방지**: 15페이지 단위로 분할하여 처리
- **병렬 처리**: 최대 3개 에이전트 동시 실행으로 속도 향상
- **실패 복구 용이**: 청크 단위 재시도 가능
- **대용량 문서 지원**: 100+ 페이지 문서도 안정적 처리

### 핵심 원칙

1. **전체 문서 파악 우선**: PPTX 전체 구조를 먼저 이해
2. **페이지 순서대로 TC 작성**: 화면정의서 페이지 번호 순서 유지
3. **Claude가 판단하여 TC 작성**: 규칙 기반이 아닌 이해 기반
4. **크로스 레퍼런스 자동 추가**: 기능 설명 부족 시 관련 페이지 참조
5. **Reference = 페이지 번호만**: `"5P"` 형식
6. **레퍼런스 하드코딩 금지**: 사용자 요청 시에만 수동 추가

### 청크 분할 기준

| 설정 | 값 | 설명 |
|------|-----|------|
| MAX_PAGES_PER_CHUNK | 15 | 청크당 최대 페이지 수 |
| MAX_COMPONENTS_PER_CHUNK | 80 | 청크당 최대 컴포넌트 수 |
| MAX_PARALLEL_AGENTS | 3 | 동시 실행 에이전트 수 |

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

## 워크플로우 (청크 기반 병렬 처리)

대용량 문서(15페이지 초과)는 자동으로 청크 분할 처리합니다.

### 워크플로우 다이어그램

```
[메인 컨텍스트 - 오케스트레이터]
     │
     ├── Step 1: Phase 1 실행 (스크립트)
     │
     ├── Step 2: 청크 계획 수립 (plan_chunks.py)
     │
     ├── Step 3: 병렬 에이전트 디스패치
     │     ├── Agent-1: Chunk 1 (1~15P) → tc_chunk_1.json
     │     ├── Agent-2: Chunk 2 (16~30P) → tc_chunk_2.json
     │     └── Agent-3: Chunk 3 (31~45P) → tc_chunk_3.json
     │
     ├── Step 4: 결과 병합 (merge_tc_chunks.py)
     │
     └── Step 5: Excel 출력 + 검증/통계 통합
```

### Step 1: [메인] Phase 1 실행
```bash
cd "{scripts_dir}"
py extract_images.py "{pptx_path}" --output "{output_dir}" --quiet
py extract_pptx.py "{pptx_path}" "{output_dir}/pptx_data.json"
```

### Step 2: [메인] 청크 계획 수립
```bash
py plan_chunks.py "{output_dir}/pptx_data.json" --max-pages 15
```

출력: `chunk_plan.json`
```json
{
  "total_chunks": 3,
  "chunks": [
    {"id": 1, "slides": [1,2,...,15], "section": "01 공통 Layout"},
    {"id": 2, "slides": [16,...,30], "section": "02 Worklist"},
    {"id": 3, "slides": [31,...,45], "section": "03 Viewer"}
  ]
}
```

### Step 3: [메인] 병렬 에이전트 디스패치
15페이지 이하 문서: 단일 에이전트로 처리
15페이지 초과 문서: Task 도구로 청크별 에이전트 **병렬 실행**

**중요**: Task 도구 호출 시 한 번의 메시지에 여러 Task 호출을 포함하여 병렬 실행

### Step 4: [메인] 결과 병합
```bash
py merge_tc_chunks.py "{output_dir}" --prefix {prefix}
```
- 모든 `tc_chunk_*.json` 파일 병합
- TC ID 순차 재할당
- 페이지 순서 정렬

### Step 5: [메인] Excel 출력 + 검증/통계
```bash
py write_excel.py "{output_dir}/tc_data.json" "{output_dir}/{project}_TC.xlsx"
py validate_and_stats.py "{output_dir}/tc_data.json"
```

---

## 청크 에이전트 프롬프트 템플릿

### 단일 에이전트 (15페이지 이하)

```
화면정의서 PPTX에서 테스트케이스를 생성해주세요.

PPTX 파일: {pptx_path}
출력 폴더: {output_dir}
TC ID 접두사: {prefix}
스크립트 폴더: {scripts_dir}
이미지 폴더: {output_dir}/images/
이미지 매니페스트: {output_dir}/image_manifest.json

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

3. **🖼️ 이미지 분석** (Phase 2.5) - 필수!
   - {output_dir}/image_manifest.json에서 슬라이드별 이미지 목록 확인
   - Read 도구로 {output_dir}/images/slide_*_*.png 이미지 분석
   - UI 컴포넌트 위치, 레이아웃, 색상 정보 파악
   - TC 작성 시 이미지에서 파악한 정보 반영

4. **TC 작성** (Phase 3)
   - 페이지 순서대로 TC 작성
   - TC ID: {prefix}_001, {prefix}_002, ...
   - Reference: 1P, 2P, ... (크로스 레퍼런스: "1P (참조: [11-1])")
   - **이미지 분석 결과 반영**: 정확한 위치, 시각적 변화 명시
   - {output_dir}/tc_data.json에 저장

5. **Excel 출력** (Phase 4)
   py write_excel.py "{output_dir}/tc_data.json" "{output_dir}/{project_name}_TestCases.xlsx"

### 반환할 요약:
- 프로젝트명, 버전
- 총 TC 수
- 페이지별 TC 분포
- 크로스 레퍼런스 현황
- 분석한 이미지 수
- 출력 파일 경로
```

### 청크 에이전트 (병렬 처리용)

```
화면정의서의 일부 페이지에 대한 테스트케이스를 생성해주세요.

청크 ID: {chunk_id}
담당 슬라이드: {slide_list}
섹션: {section_name}
출력 파일: {output_dir}/tc_chunk_{chunk_id}.json
TC ID 접두사: {prefix}
이미지 폴더: {output_dir}/images/
이미지 매니페스트: {output_dir}/image_manifest.json

### 슬라이드 데이터
{filtered_pptx_data}

### 🖼️ 이미지 분석 (필수)

**반드시 담당 슬라이드의 이미지를 분석하여 TC에 반영하세요.**

1. **image_manifest.json 확인**
   - 담당 슬라이드 번호에 해당하는 이미지 목록 확인
   - 예: slide_5_image_1.png, slide_5_image_2.png

2. **이미지 읽기 (Read 도구 사용)**
   - `{output_dir}/images/slide_{번호}_*.png` 파일을 Read 도구로 읽기
   - Claude는 이미지를 직접 분석할 수 있음

3. **이미지에서 파악할 정보**
   - UI 컴포넌트 위치 (좌측상단, 우측하단, 중앙 등)
   - 버튼/아이콘 모양 및 배치
   - 화면 레이아웃 구조 (헤더, 사이드바, 메인 영역)
   - 색상 정보 (배경색, 강조색)
   - 텍스트 라벨 확인

4. **TC에 반영할 내용**
   - Test Step에 정확한 위치 명시: "화면 우측 상단의 [X] 버튼 클릭"
   - Expected Result에 시각적 변화 명시: "버튼 배경색이 회색에서 파란색으로 변경됨"
   - 레이아웃 기반 테스트: "사이드바가 접히고 메인 영역이 확장됨"

### TC 작성 규칙
- TC ID: CHUNK{chunk_id}_001, CHUNK{chunk_id}_002, ... (병합 시 재할당됨)
- Reference: 슬라이드 번호 그대로 (예: 5P, 16P)
- 기존 Depth/Title/Step/Expected 규칙 준수

### TC 작성 판단 기준
- 표시 확인: 모든 UI 컴포넌트에 기본 생성
- 기능 확인: 버튼, 탭, 입력 등 동작 가능한 요소
- 단축키 확인: Description에 "단축키", "Hint" 포함 시
- Hover 확인: "Mouse Enter", "Hover", "툴팁" 언급 시
- 비활성화 확인: "비활성화", "disabled" 조건 언급 시
- 팝업 확인: "[번호]" 형식 팝업 참조 시

### ⚠️ raw_text 기반 컴포넌트 처리

컴포넌트 중 `source: "raw_text"`인 항목은 테이블이 아닌 자유 형식 텍스트에서 추출된 것입니다.
- **description 필드에 상세 내용**이 있으므로 이를 기반으로 TC 작성
- 주로 기능 설명, 동작 방식, 워크플로우 내용이 포함됨
- raw_text 기반 컴포넌트도 **반드시 TC 작성 대상**에 포함

예시:
```json
{
  "no": 1,
  "component": "[길이 측정 하기]",
  "description": "1) 화면 영역에서 왼쪽 마우스 클릭 시 해당 Point를 시작 Point로 설정...",
  "source": "raw_text"
}
```
→ "길이 측정" 기능에 대한 TC 작성 (표시 확인, 기능 확인 등)

### 크로스 레퍼런스 판단 기준
- Description에 [번호] 또는 [번호-번호] 형식 참조 시
- "p.XX 참고", "XX페이지 참조" 문구 발견 시
- 동일 기능이 다른 페이지에서 상세 설명될 때

### 출력 형식 (tc_chunk_{chunk_id}.json)

**⚠️ 중요**:
- JSON 키는 반드시 `testcases` 사용 (NOT `test_cases`)
- 필드명은 `test_step`, `expected_result`, `pre_condition` 사용

```json
{
  "chunk_id": {chunk_id},
  "slide_range": [{start}, {end}],
  "section": "{section_name}",
  "testcases": [
    {
      "test_case_id": "CHUNK{chunk_id}_001",
      "depth1": "...",
      "depth2": "...",
      "depth3": "...",
      "depth4": "...",
      "title": "...",
      "pre_condition": "사전 조건 (필요시)",
      "test_step": "1. 첫 번째 단계\n2. 두 번째 단계",
      "expected_result": "#1 첫 번째 기대결과 #2 두 번째 기대결과",
      "requirement_id": "",
      "reference": "{slide_number}P",
      "importance": "",
      "writer": ""
    }
  ]
}
```

**필드명 매핑** (merge_tc_chunks.py가 자동 변환):
| 입력 (허용) | 출력 (Excel용) |
|------------|---------------|
| `steps` | → `test_step` |
| `expected` | → `expected_result` |
| `precondition` | → `pre_condition` |

### 반환할 요약
- 청크 ID
- 처리한 슬라이드 범위
- 생성된 TC 수
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
│   ├── plan_chunks.py          # 청크 분할 계획 생성 (Step 2)
│   ├── merge_tc_chunks.py      # TC 청크 병합 (Step 4)
│   ├── write_excel.py          # Excel 출력 (Step 5)
│   ├── validate_and_stats.py   # 검증 + 통계 통합 (Step 5)
│   ├── run_all.py              # 기존 통합 실행 (레거시)
│   ├── merge_analysis.py       # 분석 결과 병합 (레거시)
│   └── generate_testcase.py    # TC 생성 (레거시)
├── output/
│   ├── images/                 # 추출된 이미지 (슬라이드별)
│   ├── image_manifest.json     # 이미지 메타데이터
│   ├── pptx_data.json          # PPTX 텍스트/컴포넌트 데이터
│   ├── chunk_plan.json         # 청크 분할 계획
│   ├── tc_chunk_1.json         # 청크별 TC (병렬 처리용)
│   ├── tc_chunk_2.json
│   ├── tc_chunk_3.json
│   └── tc_data.json            # 최종 병합된 TC 데이터
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

## 실행 워크플로우 상세 (청크 기반)

### 문서 크기별 처리 방식

| 문서 크기 | 처리 방식 | 에이전트 수 |
|----------|----------|------------|
| 15페이지 이하 | 단일 에이전트 | 1 |
| 16~30페이지 | 2청크 병렬 | 2 |
| 31~45페이지 | 3청크 병렬 | 3 |
| 46페이지 이상 | 3청크 + 순차 | 3 (반복) |

### 메인 컨텍스트 역할 (오케스트레이터)

```
1. 파일 확인 및 Phase 1 실행
   - PPTX 파일 존재 확인
   - 옵션 파싱 (--prefix)
   - extract_images.py, extract_pptx.py 실행

2. 청크 계획 수립
   - plan_chunks.py 실행
   - chunk_plan.json 확인
   - total_chunks에 따라 처리 방식 결정

3. 에이전트 디스패치
   - 15페이지 이하: 단일 에이전트로 전체 처리
   - 15페이지 초과: 청크별 에이전트 병렬 실행
   - Task 도구 호출 시 병렬 실행 위해 한 메시지에 여러 Task

4. 결과 수집 및 병합
   - 모든 에이전트 완료 대기
   - merge_tc_chunks.py 실행
   - tc_data.json 생성

5. 최종 출력
   - write_excel.py로 Excel 생성
   - validate_and_stats.py로 검증 + 통계
   - 요약 출력
```

### 청크 에이전트 역할

각 청크 에이전트가 담당 슬라이드에 대해:
- 슬라이드 데이터 분석
- TC 작성 (CHUNK{id}_ 접두사 사용)
- tc_chunk_{id}.json 저장
- 요약 반환

## 결과 출력 (청크 기반)

### 소형 문서 (15페이지 이하)

```
[TC 생성] 단일 에이전트 처리 중...

============================================================
  테스트케이스 생성 완료
============================================================
프로젝트: OnePros (Ver 1.0)
총 TC: 42개
페이지별: 1P(32), 2P(10)
크로스 레퍼런스: 5건
출력: output/OnePros_TestCases.xlsx
============================================================
```

### 대용량 문서 (15페이지 초과)

```
[TC 생성] 청크 기반 병렬 처리 중...

청크 분할 완료: 3개 청크
  - Chunk 1: 1~15P (15페이지, 45컴포넌트)
  - Chunk 2: 16~30P (15페이지, 52컴포넌트)
  - Chunk 3: 31~42P (12페이지, 38컴포넌트)

에이전트 디스패치: 3개 병렬 실행

[Chunk 1] 완료: 45개 TC
[Chunk 2] 완료: 52개 TC
[Chunk 3] 완료: 38개 TC

============================================================
  테스트케이스 생성 완료
============================================================
프로젝트: OnePros (Ver 1.0)
총 TC: 135개 (3청크 병합)
페이지별: 1P(32), 2P(10), ..., 42P(8)
크로스 레퍼런스: 12건
출력: output/OnePros_TestCases.xlsx
처리 방식: 청크 병렬 (3 에이전트)
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

## 자동 실행 체이닝 (청크 기반)

TC 생성 완료 후 자동으로 다음 단계 실행:

```
/testcase 실행
    ↓
[메인] Phase 1: 이미지/텍스트 추출
    ↓
[메인] Step 2: 청크 계획 수립 (plan_chunks.py)
    ↓
15페이지 이하? ─Yes→ 단일 에이전트
    │No
    ↓
[메인] Step 3: 청크 에이전트 병렬 디스패치
    ↓
[에이전트들] 청크별 TC 작성 (병렬)
    ↓
[메인] Step 4: 결과 병합 (merge_tc_chunks.py)
    ↓
[메인] Step 5: Excel 출력 (write_excel.py)
    ↓
[메인] 검증 + 통계 (validate_and_stats.py)
    ↓
검증 통과 시 → 완료 요약 출력
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
# Phase 1: 이미지 추출만 실행
py extract_images.py "파일.pptx" --output "output" --quiet

# Phase 1: 텍스트/컴포넌트 추출만 실행
py extract_pptx.py "파일.pptx" "output/pptx_data.json"

# Step 2: 청크 계획 확인
py plan_chunks.py "output/pptx_data.json" --max-pages 15

# Step 4: TC 청크 병합
py merge_tc_chunks.py "output" --prefix IT_OP

# Step 5: Excel 출력만 실행
py write_excel.py "output/tc_data.json" "output/test.xlsx"

# Step 5: 검증 + 통계
py validate_and_stats.py "output/tc_data.json"

# 검증만
py validate_and_stats.py "output/tc_data.json" --validate-only

# 통계만
py validate_and_stats.py "output/tc_data.json" --stats-only
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
