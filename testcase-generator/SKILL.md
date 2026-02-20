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

### 🚫 기존 TC 데이터 재사용 금지

**매번 화면정의서와 이미지를 새로 분석해서 TC 작성**

| 금지 | 이유 |
|------|------|
| 기존 tc_data.json 참조 | 이전 분석 결과에 의존하면 안 됨 |
| 이전 TC 형식/패턴 복사 | 새 문서에 맞지 않을 수 있음 |
| 기존 TC를 "템플릿"으로 사용 | 화면정의서 내용이 다를 수 있음 |

**원칙**: 에이전트는 "이 화면정의서를 처음 보는 것처럼" TC를 작성해야 함

### 🗑️ 기존 청크 파일 삭제 필수 (Step 3 전)

**에이전트 디스패치 전에 반드시 기존 청크 파일 삭제!**

```bash
# Step 3 실행 전 필수 명령
rm -f "{output_dir}/tc_chunk_*.json"
```

| 문제 | 원인 | 해결책 |
|------|------|--------|
| 에이전트가 "기존 파일 있음"으로 건너뜀 | tc_chunk_*.json 잔존 | 디스패치 전 삭제 |
| 이미지 분석 없이 기존 TC 재사용 | 에이전트 판단 오류 | 파일 삭제 + 프롬프트 명시 |
| 이전 실행 결과와 혼합 | 파일 타임스탬프 불일치 | 매번 새로 생성 |

**워크플로우 체크리스트**:
```
✅ Step 1: Phase 1 실행 (이미지/텍스트 추출)
✅ Step 2: 청크 계획 수립
✅ Step 2.5: 기존 tc_chunk_*.json 파일 삭제  ← 필수!
✅ Step 2.7a: 사전 분석 스크립트 (pre_analyze.py)
✅ Step 2.7b: TC 플래닝 에이전트 (이미지 분석 → tc_plan.json)  ← NEW!
✅ Step 3: 청크 에이전트 디스패치 (tc_plan 기반)
✅ Step 4: 결과 병합
✅ Step 5: Excel 출력
✅ Step 5.5: 검증 에이전트 (이미지 vs TC 비교)  ← NEW!
✅ Step 6: validate_and_stats.py
```

### 📋 불완전한 화면정의서 처리 규칙

화면정의서가 완벽하지 않은 경우의 처리 방법:

#### 공란 처리 기준

| 상황 | 처리 방법 | 예시 |
|------|----------|------|
| **정보 완전 부재** | 해당 필드 공란 | Pre-condition 정보 없음 → 공란 |
| **정보 불명확** | 해당 필드 공란 | 단축키 추정 불가 → Expected에서 단축키 생략 |
| **확인 필요** | 해당 필드 공란 | 버튼 동작 불명확 → Expected 공란, 수동 작성 필요 |

#### ⚠️ 절대 금지 사항

| 금지 | 이유 |
|------|------|
| 화면정의서에 있는 내용 생략 | 있는 정보는 반드시 TC에 반영 |
| 추정으로 내용 채우기 | 확실하지 않으면 공란 처리 |
| "모르겠음" 텍스트 작성 | 공란으로 두고 사용자가 수동 작성 |

#### 올바른 처리 예시

**상황 1: Description이 비어있는 컴포넌트**
```
Component: "Export 버튼"
Description: (없음)

→ TC 생성:
  - Title: "[Export] 버튼 표시 확인" ✅ (컴포넌트명은 있으므로 TC 생성)
  - Expected Result: (공란) ← 동작 설명 없으므로 공란
  - _blank_reasons에 공란 이유 기록
```

**상황 2: 단축키 정보가 불확실한 경우**
```
Description: "저장 기능 (단축키 미정)"

→ TC 생성:
  - Expected Result: "# 현재 작업이 저장됨" ✅
  - (단축키 정보 생략 - 추정하지 않음)
```

**상황 3: 화면정의서에 상세 설명이 있는 경우**
```
Description: "버튼 클릭 시 환자 정보 팝업 표시.
             팝업에는 이름, 생년월일, 성별 정보 포함"

→ TC 생성:
  - Expected Result: "# 환자 정보 팝업 표시됨
                     # 팝업에 이름, 생년월일, 성별 정보 포함됨" ✅
  - (화면정의서 내용 전부 반영 - 생략 금지!)
```

#### 공란 셀 시각화

- **노란색 배경**: 공란 필드에 자동 적용 (눈에 띄게)
- **코멘트 추가**: 공란 이유를 Excel 코멘트로 표시 (어느 부분에 뭐 때문에 못 썼는지)

### ✅ 필수 확인

1. **청크 에이전트가 TC 작성**: Claude가 pptx_data.json을 분석하고 **사고하여** TC 작성
2. **🖼️ 이미지 분석 필수**: 에이전트가 `output/images/` 폴더의 이미지를 Read로 분석
3. **JSON 키 형식**: 청크 파일에서 `testcases` 키 사용 (NOT `test_cases`)
4. **메인 역할**: 오케스트레이션만 (스크립트 실행, 에이전트 디스패치, 결과 수집)
5. **🗑️ 기존 청크 파일 삭제**: Step 3 전에 `rm -f tc_chunk_*.json` 실행

### 🖼️ 이미지 분석 검증 체크리스트

에이전트가 이미지 분석을 제대로 했는지 확인하는 방법:

| 확인 항목 | 정상 | 비정상 |
|----------|------|--------|
| 에이전트 반환에 "분석한 이미지 목록" 포함 | ✅ | ❌ |
| TC에 위치 정보 포함 (좌측상단, 우측하단 등) | ✅ | ❌ |
| TC에 시각적 변화 명시 (색상 변경, 하이라이트 등) | ✅ | ❌ |
| tc_chunk_*.json에 `images_analyzed` 필드 있음 | ✅ | ❌ |

**비정상인 경우**:
1. 기존 tc_chunk_*.json 삭제
2. 에이전트 프롬프트에 이미지 분석 필수 명시
3. 에이전트 재실행

### 📋 메인 컨텍스트 최소화

메인 컨텍스트에서 하는 일:
- ✅ 스크립트 실행 (Bash)
- ✅ 에이전트 디스패치 (Task)
- ✅ 결과 요약 출력

메인 컨텍스트에서 하면 안 되는 일:
- ❌ pptx_data.json 내용 Read로 읽기
- ❌ chunk_plan.json 내용 Read로 읽기 (청크 수만 확인)
- ❌ tc_plan.json 내용 Read로 읽기 (경로만 에이전트에 전달!)
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

### 출력 경로

**모든 TC 산출물은 프로젝트 루트의 output 폴더에 저장** (설정: `tc_config.yaml`):
```
{PROJECT_ROOT}/output
```

| 파일 | 경로 |
|------|------|
| 이미지 | `{PROJECT_ROOT}/output/images/` |
| PPTX 데이터 | `{PROJECT_ROOT}/output/pptx_data.json` |
| 청크 계획 | `{PROJECT_ROOT}/output/chunk_plan.json` |
| 사전 분석 | `{PROJECT_ROOT}/output/pre_analysis_raw.json` |
| TC 계획 | `{PROJECT_ROOT}/output/tc_plan.json` |
| 청크별 TC | `{PROJECT_ROOT}/output/tc_chunk_*.json` |
| 병합 TC | `{PROJECT_ROOT}/output/tc_data.json` |
| 검증 리포트 | `{PROJECT_ROOT}/output/verification_report.json` |
| Excel 결과 | `{PROJECT_ROOT}/output/{프로젝트명}_TC.xlsx` |

**환경변수로 오버라이드 가능**: `TC_OUTPUT_DIR`

### 청크 분할 기준

설정값은 `testcase-generator/config.py`에서 관리하며, 환경변수로 오버라이드 가능:

| 설정 | 기본값 | 환경변수 | 설명 |
|------|--------|----------|------|
| MAX_PAGES_PER_CHUNK | 15 | `TC_MAX_PAGES_PER_CHUNK` | 청크당 최대 페이지 수 |
| MAX_COMPONENTS_PER_CHUNK | 80 | `TC_MAX_COMPONENTS_PER_CHUNK` | 청크당 최대 컴포넌트 수 |
| MAX_PARALLEL_AGENTS | 10 | `TC_MAX_PARALLEL_AGENTS` | 동시 실행 에이전트 수 |
| MIN_CHUNKS | 3 | `TC_MIN_CHUNKS` | 최소 청크 수 (항상 병렬) |
| DEFAULT_TC_PREFIX | IT_XX | `TC_PREFIX` | TC ID 기본 접두사 |
| PRE_ANALYSIS_ENABLED | true | `TC_PRE_ANALYSIS_ENABLED` | TC 플래닝 활성화 |
| VERIFICATION_ENABLED | true | `TC_VERIFICATION_ENABLED` | 검증 에이전트 활성화 |
| PRE_ANALYSIS_IMAGE_LIMIT | 15 | `TC_PRE_ANALYSIS_IMAGE_LIMIT` | 단일 플래닝 에이전트 최대 슬라이드 |

### 에이전트 모델 설정

**TC 작성 에이전트는 반드시 Opus 모델 사용** (품질 보장):

```
Task 도구 호출 시:
  model: "opus"
  subagent_type: "general-purpose"
```

| 모델 | 용도 |
|------|------|
| opus | TC 작성 에이전트 (품질 중요) |
| sonnet | 단순 스크립트 실행, 파일 처리 |
| haiku | 빠른 검증, 간단한 작업 |

### 하드코딩 금지

**모든 TC 내용은 화면정의서(PPTX)에서 추출된 데이터만 사용합니다.**

| 허용 | 금지 |
|------|------|
| PPTX 섹션 제목 그대로 사용 | "Tool 탭", "Alignment 탭" 등 추정 |
| PPTX Description 그대로 사용 | 컴포넌트별 위치 추정 (최소화=우측상단) |
| 테스트 유형 라벨 (표시 확인 등) | 키워드 매칭으로 탭명 추출 |

### Depth 구조 (시나리오 기반)

| Depth | 소스 | 예시 |
|-------|------|------|
| Depth1 | PPTX 헤더의 제목/프로젝트명 | "Main Layout" |
| Depth2 | PPTX 섹션 제목 (번호 제거) | "공통 Layout 및 Tool 정리" |
| Depth3 | 기능 영역/그룹 | "공통레이아웃", "Common Tool" |
| Depth4 | 조건/상태 (선택적) | "작업내역 없음", "작업내역 있음", "" |

## 트리거

- `/testcase`
- `/tc`

## 사용법

```
/testcase <PPTX_파일_경로> [--prefix IT_XX]
```

## 워크플로우 (청크 기반 병렬 처리)

모든 문서를 자동으로 최소 3청크로 분할하여 병렬 처리합니다.

### 워크플로우 다이어그램

```
[메인 컨텍스트 - 오케스트레이터]
     │
     ├── Step 1: Phase 1 실행 (스크립트)
     │
     ├── Step 2: 청크 계획 수립 (plan_chunks.py)
     │
     ├── Step 2.5: 기존 청크 파일 삭제 ← 🔴 필수!
     │     rm -f "{output_dir}/tc_chunk_*.json"
     │
     ├── Step 2.7a: 사전 분석 (pre_analyze.py) → pre_analysis_raw.json
     │
     ├── Step 2.7b: TC 플래닝 에이전트 (opus) ← 🆕 핵심!
     │     └── 모든 fullpage 이미지 상세 분석 → tc_plan.json
     │
     ├── Step 3: 청크 에이전트 병렬 디스패치 (tc_plan 기반)
     │     ├── Agent-1: Chunk 1 (1~15P) → tc_chunk_1.json
     │     ├── Agent-2: Chunk 2 (16~30P) → tc_chunk_2.json
     │     └── Agent-3: Chunk 3 (31~45P) → tc_chunk_3.json
     │
     ├── Step 4: 결과 병합 (merge_tc_chunks.py)
     │
     ├── Step 5: Excel 출력 (write_excel.py) → 1차 Excel
     │
     ├── Step 5.5: 검증 에이전트 (opus) ← 🆕
     │     └── tc_plan vs tc_data 비교, 누락 TC 보완
     │     └── 보완 TC 있으면 → 병합/Excel 재생성
     │
     └── Step 6: validate_and_stats.py (형식 검증 + 통계)
```

### Step 1: [메인] Phase 1 실행
```bash
cd "{scripts_dir}"
py extract_images.py "{pptx_path}" --output "{output_dir}" --quiet
py extract_pptx.py "{pptx_path}" "{output_dir}/pptx_data.json"
```

### Step 2: [메인] 청크 계획 수립
```bash
py plan_chunks.py "{output_dir}/pptx_data.json" --max-pages 15 --min-chunks 3
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

### Step 2.7a: [메인] 사전 분석 스크립트 실행
```bash
cd "{scripts_dir}"
py pre_analyze.py "{output_dir}/pptx_data.json" \
  --manifest "{output_dir}/image_manifest.json" \
  --chunk-plan "{output_dir}/chunk_plan.json" \
  --output "{output_dir}/pre_analysis_raw.json"
```

출력: `pre_analysis_raw.json` (텍스트 기반 구조 정보 - 크로스 레퍼런스, 섹션 구조, 이미지 인벤토리 등)

### Step 2.7b: [메인] TC 플래닝 에이전트 디스패치

**목적**: 이미지를 상세 분석하여 **"어떤 TC를 작성할지" 구체적 계획** 수립

**실행**: Task 도구 (opus 모델)
- 문서 ≤15P: 단일 에이전트가 모든 fullpage 분석
- 문서 >15P: 청크별 병렬 플래닝 에이전트 (각각 담당 슬라이드 이미지만 분석)

**입력**: pre_analysis_raw.json + pptx_data.json + 모든 fullpage 이미지
**출력**: `{output_dir}/tc_plan.json`

**tc_plan.json은 메인에서 읽지 않음**: 청크 에이전트에 tc_plan.json 경로만 전달, 에이전트가 직접 Read하여 담당 슬라이드 계획 확인 (메인 컨텍스트 20k+ tokens 절약)

**폴백**: 에이전트 실패 시 경고 출력, Step 3은 tc_plan 없이 기존 방식으로 진행

### Step 3: [메인] 병렬 에이전트 디스패치 (tc_plan 기반)
모든 문서: plan_chunks.py 결과(최소 3청크)에 따라 Task 도구로 **항상 병렬 실행**

**tc_plan.json이 있는 경우**: 청크 에이전트 프롬프트에 tc_plan.json **경로만** 전달, 에이전트가 직접 Read
**tc_plan.json이 없는 경우**: 기존처럼 독립적으로 TC 작성 (하위 호환)

⚠️ **메인에서 tc_plan.json Read 금지** (20k+ tokens 컨텍스트 낭비 방지)

**중요**: Task 도구 호출 시 한 번의 메시지에 여러 Task 호출을 포함하여 병렬 실행

### Step 4: [메인] 결과 병합
```bash
py merge_tc_chunks.py "{output_dir}" --prefix {prefix}
```
- 모든 `tc_chunk_*.json` 파일 병합
- TC ID 순차 재할당
- 페이지 순서 정렬

### Step 5: [메인] Excel 출력 (1차)
```bash
py write_excel.py "{output_dir}/tc_data.json" "{output_dir}/{project}_TC.xlsx"
```

### Step 5.5: [메인] 검증 에이전트 디스패치

**목적**: tc_plan.json의 계획 대비 실제 TC 커버리지 확인 + 빠진 내용 보완

**실행**: Task 도구 (opus 모델, 단일 에이전트)

**입력**: tc_plan.json + tc_data.json + fullpage 이미지
**출력**: `{output_dir}/verification_report.json`

**보완 TC 처리**:
- supplementary_tc가 있으면 → tc_data.json에 추가 → merge_tc_chunks.py 재실행 → Excel 재생성
- 없으면 → 검증 통과, 기존 Excel 유지

**폴백**: 에이전트 실패 시 기존 Excel 유지, 검증 건너뜀

### Step 6: [메인] 형식 검증 + 통계
```bash
py validate_and_stats.py "{output_dir}/tc_data.json"
```

---

## TC 플래닝 에이전트 프롬프트 템플릿 (Step 2.7b)

### 단일 에이전트 (≤15 슬라이드)

```
화면정의서의 모든 슬라이드를 분석하여 TC 작성 계획을 수립해주세요.

⚠️ 당신의 역할: TC를 직접 작성하지 않고, **어떤 TC를 작성해야 하는지 계획**만 수립합니다.

### 입력 데이터
- 사전 분석 결과: {output_dir}/pre_analysis_raw.json
- PPTX 데이터: {output_dir}/pptx_data.json
- 이미지 폴더: {output_dir}/images/

### 🔴 이미지 상세 분석 (핵심!)

모든 슬라이드의 fullpage 이미지를 Read 도구로 열어서 **꼼꼼히** 분석하세요.

**이미지 내 텍스트 정독 (필수!)**:
fullpage 캡처 이미지에 보이는 **모든 텍스트를 꼼꼼히 읽고 이해**해야 합니다.
pptx_data.json의 Description에는 없지만 이미지에만 보이는 텍스트가 많습니다.

| 읽어야 할 텍스트 | TC 반영 방법 |
|-----------------|-------------|
| 버튼 라벨 (Save, Cancel, OK) | Title에 정확한 버튼명 사용 |
| 메뉴/탭 항목 | Depth3, Step 진입 동작에 반영 |
| 팝업 메시지 | Expected Result에 정확한 메시지 기술 |
| 테이블 헤더/내용 | 입력 필드별 TC, 표시 확인 TC |
| 드롭다운 항목 | 각 선택 항목별 TC 계획 |
| 상태 텍스트 | 상태별 조건 분기 TC |
| 툴팁/힌트 (Ctrl+S, F12) | 단축키 TC 계획 |
| 에러/경고 메시지 | 경고 팝업 TC |
| 입력 필드 placeholder | 입력 관련 TC |
| 번호 마커 (빨간 원 ①②③) | Description과 매칭하여 참조 |

**원칙**: 이미지에서 읽은 텍스트를 기반으로 TC 계획을 수립해야 합니다.

### 수행 작업

1. **슬라이드별 상세 이미지 분석**
   - 각 fullpage 이미지를 Read 도구로 열어서 꼼꼼히 확인
   - UI 컴포넌트별 위치, 크기, 상태, 상호작용 파악
   - 팝업/다이얼로그의 내부 구조 분석 (버튼, 입력 필드, 선택 항목)
   - 시각적 상태 변화 파악 (활성/비활성, 선택/미선택)

2. **슬라이드별 TC 계획 수립**
   - 각 슬라이드에서 작성해야 할 TC 목록 (Title 초안 포함)
   - TC별: depth4, position_hint, pre_condition, expected_keywords
   - 조건 분기 시 양쪽 TC 모두 계획
   - 팝업 내 버튼별 TC, 단축키 TC 등 누락 없이

3. **전체 구조 확정**
   - Depth1/2/3 통일 (모든 슬라이드에 걸쳐 일관성)
   - 위치 서술자 통일 (같은 영역은 같은 표현)
   - 크로스 레퍼런스 매핑

### 출력: {output_dir}/tc_plan.json

아래 JSON 형식으로 Write 도구로 저장하세요:

```json
{
  "version": "1.0",
  "project_info": { "project_name": "...", "version": "..." },
  "global_context": {
    "layout_map": {
      "global_description": "전체 레이아웃 요약",
      "regions": {
        "region_id": { "name": "영역명", "components": ["컴포넌트1", "컴포넌트2"] }
      }
    },
    "depth_structure": {
      "assignments": {
        "슬라이드번호": { "depth1": "...", "depth2": "...", "depth3": "..." }
      }
    },
    "position_conventions": {
      "컴포넌트명": "위치 서술자"
    },
    "cross_references": [
      { "source_slide": 1, "ref_id": "[11-1]", "description": "..." }
    ]
  },
  "slide_plans": {
    "슬라이드번호": {
      "slide_title": "슬라이드 제목",
      "image_analysis_summary": "이미지 분석 요약",
      "planned_tc": [
        {
          "tc_outline_id": "PLAN_1_001",
          "depth4": "",
          "title": "TC 제목 초안",
          "test_scenario": "테스트 시나리오 개요",
          "position_hint": "위치 힌트",
          "pre_condition": "",
          "expected_keywords": ["기대 결과 키워드"],
          "step_outline": "1. 진입\n2. 동작" (선택)
        }
      ],
      "images_analyzed": ["slide_01_fullpage.png"]
    }
  },
  "chunk_assignments": {
    "청크ID": {
      "slides": [1,2,3],
      "planned_tc_count": 51,
      "key_scenarios": ["시나리오1", "시나리오2"]
    }
  }
}
```

### 반환 요약 (필수 포함)
- 분석한 슬라이드 수
- 분석한 이미지 수
- 계획된 TC 총 수
- 슬라이드별 TC 수
- tc_plan.json 파일 경로
```

### 병렬 에이전트 (>15 슬라이드)

문서가 15 슬라이드를 초과하는 경우 청크별 병렬 플래닝 에이전트를 디스패치합니다.

**1차**: 첫 번째 에이전트가 전체 레이아웃 + 첫 청크 이미지 분석 → global_context 확정
**2차**: 나머지 청크 에이전트가 global_context를 받아서 담당 슬라이드 계획 수립

또는 모든 에이전트를 병렬 실행 후 결과를 메인에서 수동 병합:
- 각 에이전트의 slide_plans를 합침
- depth_structure는 에이전트 결과 비교하여 통일

---

## 검증 에이전트 프롬프트 템플릿 (Step 5.5)

```
생성된 테스트케이스의 품질을 검증하고 누락된 내용을 보완해주세요.

### 입력 데이터
- TC 계획: {output_dir}/tc_plan.json
- 실제 TC: {output_dir}/tc_data.json
- 이미지 폴더: {output_dir}/images/

### 수행 작업

1. **계획 대비 커버리지 확인**
   - tc_plan.json의 planned_tc vs tc_data.json의 실제 TC 매핑
   - 계획된 TC 중 빠진 것 확인
   - 계획에 없지만 추가된 TC 확인

2. **이미지 재확인** (선택적 - 주요 슬라이드만)
   - fullpage 이미지를 다시 보고 계획과 TC 모두에서 빠진 UI 요소 확인

3. **일관성 검증**
   - Depth 값이 tc_plan.json 규칙대로 사용되었는지
   - 위치 서술자가 통일되었는지

4. **보완 TC 생성**
   - 빠진 내용에 대해 추가 TC JSON 작성
   - TC 형식은 기존 tc_data.json의 TC와 동일

### 출력: {output_dir}/verification_report.json

아래 JSON 형식으로 Write 도구로 저장하세요:

```json
{
  "planned_tc_count": 82,
  "actual_tc_count": 82,
  "coverage": {
    "planned_covered": 80,
    "planned_missing": [
      { "tc_outline_id": "PLAN_1_015", "reason": "..." }
    ],
    "extra_found_in_image": [
      { "slide": 3, "element": "...", "severity": "필수|권장" }
    ]
  },
  "consistency": {
    "depth_issues": [],
    "position_issues": []
  },
  "supplementary_tc": [
    {
      "test_case_id": "SUPPLEMENT_001",
      "depth1": "...",
      "depth2": "...",
      "depth3": "...",
      "depth4": "...",
      "title": "...",
      "pre_condition": "...",
      "test_step": "1. ...\n2. ...",
      "expected_result": "# ...",
      "requirement_id": "",
      "reference": "5P",
      "importance": "",
      "writer": ""
    }
  ]
}
```

### 반환 요약 (필수 포함)
- 계획 TC 수 vs 실제 TC 수
- 누락된 TC 수
- 보완 TC 수
- 일관성 이슈 수
- verification_report.json 파일 경로
```

---

## 청크 에이전트 프롬프트 템플릿

### 청크 에이전트 프롬프트 (병렬 처리용)

```
화면정의서의 일부 페이지에 대한 테스트케이스를 생성해주세요.

⚠️ 중요 (반드시 준수):
1. 기존 tc_chunk_{chunk_id}.json 파일이 있어도 무시하고 새로 생성하세요.
2. 반드시 이미지를 Read 도구로 분석하여 TC에 반영하세요.
3. 기존 TC 패턴을 복사하지 말고, 화면정의서를 처음 보는 것처럼 분석하세요.

청크 ID: {chunk_id}
담당 슬라이드: {slide_list}
섹션: {section_name}
출력 파일: {output_dir}/tc_chunk_{chunk_id}.json
TC ID 접두사: {prefix}
이미지 폴더: {output_dir}/images/
이미지 매니페스트: {output_dir}/image_manifest.json

### TC 작성 계획 (tc_plan.json 직접 읽기)

⚠️ tc_plan.json을 Read 도구로 직접 읽어서 담당 슬라이드의 계획을 확인하세요.
TC 계획 파일: {output_dir}/tc_plan.json

1. tc_plan.json을 Read 도구로 열기
2. global_context에서 Depth 구조, 위치 규칙, 크로스 레퍼런스 확인
3. slide_plans에서 담당 슬라이드({slide_list})의 planned_tc 확인
4. chunk_assignments에서 인접 청크 정보 확인
5. 계획의 모든 TC를 빠짐없이 작성
6. 계획에 없는 TC를 추가로 발견하면 작성해도 됨

(tc_plan.json이 없는 경우: 기존처럼 pptx_data.json과 이미지를 분석하여 독립적으로 TC 작성)

### 🖼️ 이미지 분석 (필수)

**반드시 담당 슬라이드의 이미지를 분석하여 TC에 반영하세요.**

1. **Fullpage 이미지 최우선 분석** ⭐
   - `{output_dir}/images/slide_{번호}_fullpage.png` 파일을 Read 도구로 읽기
   - 슬라이드 전체 캡처이므로 **도형, 화살표, 표, 레이아웃** 모두 포함
   - image_manifest.json의 `fullpage_images` 배열에서 담당 슬라이드 확인
   - fullpage가 없으면 개별 이미지만 분석

2. **개별 이미지 보조 분석**
   - `{output_dir}/images/slide_{번호}_image_*.png` 파일을 Read 도구로 읽기
   - image_manifest.json의 `images` 배열에서 담당 슬라이드 확인
   - fullpage 이미지의 상세 보충용 (고해상도 개별 UI 요소)

3. **이미지에서 파악할 정보**
   - UI 컴포넌트 위치 (좌측상단, 우측하단, 중앙 등)
   - 버튼/아이콘 모양 및 배치
   - 화면 레이아웃 구조 (헤더, 사이드바, 메인 영역)
   - 색상 정보 (배경색, 강조색)
   - 텍스트 라벨 확인
   - 도형/화살표로 표현된 흐름/관계 (fullpage에서만 확인 가능)

4. **TC에 반영할 내용**
   - Test Step에 정확한 위치 명시: "화면 우측 상단의 [X] 버튼 클릭"
   - Expected Result에 시각적 변화 명시: "버튼 배경색이 회색에서 파란색으로 변경됨"
   - 레이아웃 기반 테스트: "사이드바가 접히고 메인 영역이 확장됨"

### TC 작성 규칙
- TC ID: CHUNK{chunk_id}_001, CHUNK{chunk_id}_002, ... (병합 시 재할당됨)
- Reference: 슬라이드 번호 그대로 (예: 5P, 16P)
- 기존 Depth/Title/Step/Expected 규칙 준수

### 🔴 Test Step 품질 규칙 (필수!)

**단일 스텝 TC 금지. 모든 TC는 최소 2단계 이상.**

1. **Step 1은 반드시 진입 동작**: "{화면/탭명} 화면 진입"
2. **위치 서술자 필수**: 이미지에서 파악한 위치를 Step에 명시
   - "좌측 Common Tool 영역의 Save 버튼 클릭"
   - "우측 상단 닫기(X) 버튼 클릭"
3. **팝업 내 버튼은 3단계 필수**: 진입 → 팝업 트리거 → 버튼 클릭

❌ "1. 팝업에서 Save 클릭"
✅ "1. Alignment 탭 화면 진입\n2. 우측 상단 닫기 버튼 클릭\n3. 팝업창 Save 버튼 클릭"

### 🚫 불완전한 화면정의서 처리

**원칙**: 화면정의서에 있는 내용은 반드시 반영, 없는 내용은 공란 처리

1. **있는 정보 → 반드시 TC에 반영**
   - 컴포넌트명, Description, 참조 페이지 등
   - 화면정의서에 적힌 내용을 생략하지 말 것

2. **없거나 불명확한 정보 → 공란 처리**
   - 추정하여 채우지 말 것
   - 해당 필드를 빈 문자열("")로 설정
   - 사용자가 나중에 수동으로 작성

3. **공란 가능 필드**
   - `pre_condition`: 사전 조건 불명확 시
   - `expected_result`: 동작 설명 없을 시 (단, Title은 필수)
   - `requirement_id`: 항상 공란 허용
   - `importance`: 항상 공란 허용

### 공란 처리 시 이유 기록 (_blank_reasons)

공란으로 둘 필드가 있으면 `_blank_reasons`에 이유 기록:
```json
{
  "test_case_id": "CHUNK1_001",
  "expected_result": "",
  "_blank_reasons": {
    "expected_result": "[원본] 팝업 표시\n[사유] 팝업 내용/버튼 상세 없음"
  }
}
```

**공란 이유 기록 형식** (원본 텍스트 포함):

| 상황 | 코멘트 기록 형식 |
|------|-----------------|
| Description은 있지만 Expected 작성 불가 | `"[원본] {Description 텍스트}\n[사유] 동작 상세 불명확"` |
| 컴포넌트명만 있고 설명 없음 | `"[원본] 컴포넌트명만 있음\n[사유] Description 없음"` |
| 참조 페이지 정보가 불완전 | `"[원본] 참조: [XX-X]\n[사유] 해당 페이지 정보 없음"` |

**예시 1: Description 있지만 불완전**
```
화면정의서 Description: "팝업 표시"

→ TC JSON:
{
  "expected_result": "",
  "_blank_reasons": {
    "expected_result": "[원본] 팝업 표시\n[사유] 팝업 내용/버튼 상세 없음"
  }
}
```

**예시 2: 기능 설명은 있지만 테스트 절차 불명확**
```
화면정의서 Description: "데이터 동기화 수행"

→ TC JSON:
{
  "test_step": "",
  "_blank_reasons": {
    "test_step": "[원본] 데이터 동기화 수행\n[사유] 동기화 트리거 방법 불명확"
  }
}
```

### ⭐ TC 품질 규칙 (시나리오 기반)

#### 🔴 시나리오 기반 TC 작성 (핵심!)

**❌ 컴포넌트 나열식 (금지)**:
```
- {버튼} 표시 확인
- {버튼} 기능 확인
- {버튼} Hover 확인
```

**✅ 시나리오 기반 (권장)**:
```
- {팝업명} (트리거 동작 결과)
- {팝업명}[{버튼1}] 버튼
- {팝업명}[{버튼2}] 버튼
- {기능} 단축키 입력
```

#### 🔴 시나리오 그룹화 패턴

하나의 기능에 대해 연관된 TC를 시나리오 흐름으로 그룹:

```
[기능: 팝업이 있는 기능]
├── {팝업명} (트리거 동작)
├── {팝업명}[{버튼1}] 버튼
├── {팝업명}[{버튼2}] 버튼
└── {기능} 단축키 입력 (단축키 있는 경우)

[기능: 선택 기능]
├── {항목} 선택
├── {항목} 선택 후 {후속동작}
└── {항목} 미선택 시 {제한사항}
```

**원칙**: 화면정의서에 나온 기능 흐름대로 TC 그룹화

#### 🔴 Depth4 작성 규칙

**Depth4 = 화면정의서에서 파악한 조건/상태**:

| 유형 | 예시 |
|------|------|
| 데이터 유무 | `{데이터}없음` / `{데이터}있음` |
| 선택 상태 | `{항목}미선택` / `{항목}선택됨` |
| 활성 상태 | `비활성화 상태` / `활성화 상태` |
| 조건 없음 | `""` (빈 문자열) |

**❌ 금지**: "표시 확인", "기능 확인", "Hover 확인" (테스트 유형으로 분류)

#### 🔴 Title 작성 규칙

**시나리오/동작 기반으로 작성**:

| 패턴 | 형식 |
|------|------|
| 팝업 트리거 | `{팝업명}` |
| 팝업 내 버튼 | `{팝업명}[{버튼명}] 버튼` |
| 단축키 동작 | `{기능} 단축키 입력` |
| 기능 동작 | `{동작 결과}` |
| 상태 변경 | `{상태 변경 결과}` |

**❌ 금지**: `[{버튼}] 표시 확인`, `[{버튼}] 기능 확인`

#### 🔴 Pre-condition 작성 규칙

**특별한 조건이 있을 때만 작성, 없으면 빈 문자열**:

| 상황 | Pre-condition |
|------|---------------|
| 일반 기능 | `""` (빈 문자열) |
| 팝업 내 테스트 | `{팝업명}이 표시된 상태` |
| 특정 상태 필요 | 화면정의서에 명시된 사전 조건 |
| 이전 단계 필요 | `{단계명} 진입 상태` |

**❌ 금지**: 모든 TC에 일괄적으로 Pre-condition 채우기

#### 🔴 Test Step 작성 규칙 (상세)

**모든 TC의 Test Step은 최소 2단계 이상. 단일 스텝 TC 금지.**

##### 필수 구조: 진입 → 동작 → (후속동작)

| 순서 | 역할 | 형식 | 예시 |
|------|------|------|------|
| Step 1 | 진입 | `{화면/탭명} 화면 진입` | `Alignment 탭 화면 진입` |
| Step 2 | 동작 | `{위치}의 {대상} {동작}` | `우측 상단 닫기(X) 버튼 클릭` |
| Step 3+ | 후속 | 팝업/결과 내 동작 | `팝업창 Save 버튼 클릭` |

##### TC 유형별 최소 단계 수

| TC 유형 | 최소 | 패턴 |
|---------|------|------|
| 버튼/기능 클릭 | 2 | 진입 → 클릭 |
| 팝업 트리거 | 2 | 진입 → 트리거 동작 |
| 팝업 내 버튼 | 3 | 진입 → 팝업 트리거 → 버튼 클릭 |
| 단축키 | 2 | 진입 → 단축키 입력 |
| Hover | 2 | 진입 → 마우스 올림 |
| UI 표시 확인 | 2 | 진입 → 확인 |

##### 위치 서술자 필수

이미지 분석에서 파악한 UI 위치를 반드시 포함:
- 방향: 좌측, 우측, 상단, 하단, 중앙
- 영역명: 좌측 Common Tool 영역, 하단 Dental chart 영역
- 확인 불가 시 영역명만 사용

##### Good/Bad 비교

| 상황 | ❌ Bad | ✅ Good |
|------|-------|--------|
| 팝업 버튼 | `1. 팝업에서 Save 클릭` | `1. X 탭 화면 진입`<br>`2. 우측 상단 닫기 버튼 클릭`<br>`3. 팝업창 Save 버튼 클릭` |
| 단축키 | `1. Ctrl+S 입력` | `1. X 탭 화면 진입`<br>`2. Ctrl+S 단축키 입력` |
| 버튼 | `1. Save 버튼 클릭` | `1. X 탭 화면 진입`<br>`2. 좌측 Common Tool 영역의 Save 버튼 클릭` |
| Hover | `1. 버튼에 마우스 올림` | `1. X 탭 화면 진입`<br>`2. 좌측 Common Tool 영역의 Save 버튼에 마우스 올림` |

#### 🔴 Expected Result 작성 규칙

**화면정의서 Description 기반으로 기술**:

- 여러 결과는 각각 `#`으로 시작
- 단축키 정보 포함 (화면정의서에 있는 경우): `# {결과} (단축키: {키})`
- 부정 조건도 명시: `# {동작}되지 않음`

### TC 작성 판단 기준 (시나리오 기반)

**시나리오 단위로 TC 그룹 생성**:

| 시나리오 | TC 구성 |
|----------|---------|
| 팝업 기능 | 팝업 표시 + 각 버튼별 TC |
| 조건부 기능 | 조건별 분리 (조건A / 조건B) |
| 단축키 | 버튼 동작 TC와 별도로 단축키 TC 추가 |
| 선택 기능 | 각 선택 항목별 TC |
| 입력 필드 | 정상 입력 + 유효성 검증 |

#### 🔴 조건 분기 시 양쪽 TC 필수!

**조건이 있으면 반대 조건도 TC 작성**:

| 조건 A | 조건 B (반드시 포함) |
|--------|---------------------|
| {항목} 미선택 → 버튼 비활성화 | {항목} 선택 → 버튼 활성화 |
| {데이터} 없음 | {데이터} 있음 |
| 단일 선택 | 다중 선택 (지원 시) |

**❌ 금지**: 한쪽 조건만 TC 작성하고 반대 조건 누락

#### 🔴 화면정의서 기능 누락 금지!

**화면정의서에 있는 모든 기능/항목을 TC로 작성**:

```
팝업에 3개 선택 항목이 있으면:
✅ 항목1 선택 TC
✅ 항목2 선택 TC
✅ 항목3 선택 TC  ← 하나라도 누락 금지!
```

**원칙**: 화면정의서 Description에 언급된 모든 기능/버튼/선택항목을 TC로 커버

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

### 반환할 요약 (필수 포함 항목)
- 청크 ID
- 처리한 슬라이드 범위
- 생성된 TC 수
- **분석한 이미지 목록** (파일명) ← 🔴 필수!
- **이미지에서 파악한 주요 UI 정보** ← 🔴 필수!
- 출력 파일 경로

**⚠️ 이미지 분석 결과가 없으면 에이전트 재실행 필요!**
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
예: IT_{PREFIX}_001, IT_{PREFIX}_002
```
- 순번은 문서 전체에서 연속 (001, 002, 003...)
- 페이지별로 초기화하지 않음

### Depth 구조 (4단계 - 시나리오 기반)

| Depth | 역할 | 예시 |
|-------|------|------|
| Depth1 | 대분류 | Main Layout, Worklist |
| Depth2 | 중분류/섹션 | 공통 Layout 및 Tool, 환자 관리 |
| Depth3 | 기능 영역 | 공통레이아웃, Common Tool |
| Depth4 | 조건/상태 (선택) | 작업내역 없음, 작업내역 있음, "" |

### Title 형식 (시나리오 기반)
```
저장 확인 팝업창
저장 확인 팝업창[Save] 버튼
저장 단축키 입력
Top View 전환
프로젝트 추가
```
- **팝업 트리거**: `{팝업명} 팝업창`
- **팝업 내 버튼**: `{팝업명}[{버튼명}] 버튼`
- **단축키 동작**: `{기능} 단축키 입력`
- **기능 동작**: `{동작 결과}` (Top View 전환, 프로젝트 추가 등)

### Pre-condition (선택적)
- **기본**: 빈 문자열 `""`
- **필요 시에만 명시**:
  - `저장 확인 팝업창이 표시된 상태`
  - `환자선택 > Case 정상 로드`
  - `Order 팝업이 표시된 상태`

### Test Step 형식 (구체적 동작)
```
1. Alignment 탭 화면 진입
2. 우측 상단 닫기 버튼 클릭
3. 팝업창 Save 버튼 클릭
```
- **화면/탭 진입**부터 시작
- **위치 명시**: 우측 상단, 좌측 툴바 등
- **후속 동작 포함**: 팝업 버튼 클릭까지

### Expected Result 형식 (구체적 결과)
```
# 현재 진행중인 상태가 프로젝트에 저장됨
# 저장된 프로젝트 로드시 저장 당시화면 그대로 로드됨
```
- **여러 `#` 결과문장**
- **구체적 결과 기술**: 저장됨, 종료됨, 표시됨 등
- **부정 조건도 명시**: "저장되지 않고", "종료 안 됨"

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

**예시 1: 버튼 클릭 TC (2단계, 위치 서술자 포함)**
| 필드 | 값 |
|------|-----|
| TC ID | IT_{PREFIX}_001 |
| Reference | 5P |
| Depth1 | Main Layout |
| Depth2 | 공통 Layout 및 Tool 정리 |
| Depth3 | Common Tool |
| Depth4 | "" |
| Title | Save 버튼 |
| Pre-condition | |
| Test Step | 1. 공통 Layout 화면 진입<br>2. 좌측 Common Tool 영역의 Save 버튼 클릭 |
| Expected Result | # 현재 작업 내용이 프로젝트에 저장됨<br># 저장 완료 후 화면 상태 유지됨 |

**예시 2: 팝업 내 버튼 TC (3단계 필수)**
| 필드 | 값 |
|------|-----|
| TC ID | IT_{PREFIX}_015 |
| Reference | 5P (참조: 13P) |
| Depth1 | Main Layout |
| Depth2 | 공통 Layout 및 Tool 정리 |
| Depth3 | 닫기 버튼 |
| Depth4 | 작업내역 있음 |
| Title | 저장 확인 팝업창[Save] 버튼 |
| Pre-condition | 저장 확인 팝업창이 표시된 상태 |
| Test Step | 1. 공통 Layout 화면 진입<br>2. 우측 상단 닫기(X) 버튼 클릭<br>3. 저장 확인 팝업창에서 Save 버튼 클릭 |
| Expected Result | # 현재 진행중인 상태가 프로젝트에 저장됨<br># 저장된 프로젝트 로드시 저장 당시화면 그대로 로드됨 |

**예시 3: 단축키 TC (2단계 필수)**
| 필드 | 값 |
|------|-----|
| TC ID | IT_{PREFIX}_018 |
| Reference | 5P |
| Depth1 | Main Layout |
| Depth2 | 공통 Layout 및 Tool 정리 |
| Depth3 | Common Tool |
| Depth4 | "" |
| Title | 저장 단축키 입력 |
| Pre-condition | |
| Test Step | 1. 공통 Layout 화면 진입<br>2. Ctrl+S 단축키 입력 |
| Expected Result | # 현재 작업 내용이 프로젝트에 저장됨 (단축키: Ctrl+S) |

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
│   ├── pre_analyze.py          # 🆕 TC 플래닝 사전 분석 (Step 2.7a)
│   ├── merge_tc_chunks.py      # TC 청크 병합 (Step 4)
│   ├── write_excel.py          # Excel 출력 (Step 5)
│   ├── validate_and_stats.py   # 검증 + 통계 통합 (Step 6)
│   ├── run_all.py              # 기존 통합 실행 (레거시)
│   ├── merge_analysis.py       # 분석 결과 병합 (레거시)
│   └── generate_testcase.py    # TC 생성 (레거시)
├── output/
│   ├── images/                 # 추출된 이미지 (슬라이드별)
│   ├── image_manifest.json     # 이미지 메타데이터
│   ├── pptx_data.json          # PPTX 텍스트/컴포넌트 데이터
│   ├── chunk_plan.json         # 청크 분할 계획
│   ├── pre_analysis_raw.json   # 🆕 사전 분석 결과
│   ├── tc_plan.json            # 🆕 TC 작성 계획
│   ├── tc_chunk_*.json         # 청크별 TC (병렬 처리용)
│   ├── tc_data.json            # 최종 병합된 TC 데이터
│   └── verification_report.json# 🆕 검증 리포트
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
| 모든 문서 | 청크 병렬 | 최소 3 (자동 분할) |
| 46페이지 이상 | N청크 병렬 | 최대 10 |

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

2.5. 기존 청크 파일 삭제

2.7a. 사전 분석 (스크립트)
   - pre_analyze.py 실행 → pre_analysis_raw.json (즉시 완료)

2.7b. TC 플래닝 에이전트 (opus)
   - pre_analysis_raw.json + pptx_data.json + fullpage 이미지 분석
   - 출력: tc_plan.json
   - ❌ 메인에서 tc_plan.json Read 금지 (컨텍스트 낭비)

3. 청크 에이전트 디스패치 (tc_plan 기반)
   - 청크 에이전트 프롬프트에 tc_plan.json **경로만** 전달
   - 에이전트가 직접 tc_plan.json을 Read하여 담당 슬라이드 계획 확인
   - 모든 청크를 Task 도구로 병렬 실행
   - Task 도구 호출 시 병렬 실행 위해 한 메시지에 여러 Task

4. 결과 수집 및 병합
   - 모든 에이전트 완료 대기
   - merge_tc_chunks.py 실행
   - tc_data.json 생성

5. 1차 Excel 출력
   - write_excel.py로 Excel 생성

5.5. 검증 에이전트 (opus)
   - tc_plan.json + tc_data.json + fullpage 이미지 재확인
   - 출력: verification_report.json
   - 보완 TC 있으면 → tc_data.json에 추가 → Excel 재생성
   - 없으면 → 기존 Excel 유지

6. 형식 검증 + 통계
   - validate_and_stats.py 실행
   - 요약 출력
```

### 청크 에이전트 역할

각 청크 에이전트가 담당 슬라이드에 대해:
- 슬라이드 데이터 분석
- TC 작성 (CHUNK{id}_ 접두사 사용)
- tc_chunk_{id}.json 저장
- 요약 반환

## 결과 출력 (청크 기반)

### 결과 출력 예시

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
프로젝트: {프로젝트명} (Ver 1.0)
총 TC: 135개 (3청크 병합)
페이지별: 1P(32), 2P(10), ..., 42P(8)
크로스 레퍼런스: 12건
출력: output/{프로젝트명}_TestCases.xlsx
처리 방식: 청크 병렬 (3 에이전트)
============================================================
```

## TC 데이터 JSON 형식

Claude가 생성하는 TC 데이터 형식 (실제 테스트 결과 기반):

```json
{
  "project_info": {
    "project_name": "{프로젝트명}",
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
      "test_case_id": "IT_{PREFIX}_001",
      "depth1": "공통 Layout",
      "depth2": "공통 Layout 및 Tool 정리",
      "depth3": "Title",
      "depth4": "표시 확인",
      "title": "[Title] 표시 확인",
      "pre_condition": "",
      "test_step": "1. {프로젝트명} 프로그램 실행\n2. 메인 화면 상단 Title 영역 확인",
      "expected_result": "# {프로젝트명} 이름이 표시됨",
      "requirement_id": "",
      "reference": "1P",
      "importance": "",
      "writer": ""
    },
    {
      "test_case_id": "IT_{PREFIX}_020",
      "depth1": "공통 Layout",
      "depth2": "공통 Layout 및 Tool 정리",
      "depth3": "닫기 버튼",
      "depth4": "기능 확인",
      "title": "[닫기] 버튼 클릭",
      "pre_condition": "",
      "test_step": "1. {프로젝트명} 프로그램 실행\n2. 닫기 버튼 클릭",
      "expected_result": "# {프로젝트명} 프로그램 창 닫기 시도됨\n# 저장 유무 관계없이 프로젝트 저장 확인 팝업창이 표시됨",
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
[메인] Step 1: Phase 1 - 이미지/텍스트 추출
    ↓
[메인] Step 2: 청크 계획 수립 (plan_chunks.py, 최소 3청크)
    ↓
[메인] Step 2.5: 기존 tc_chunk 파일 삭제
    ↓
[메인] Step 2.7a: 사전 분석 (pre_analyze.py)
    ↓
[에이전트] Step 2.7b: TC 플래닝 (이미지 상세 분석 → tc_plan.json)
    ↓
[에이전트들] Step 3: 청크별 TC 작성 (tc_plan 기반, 병렬)
    ↓
[메인] Step 4: 결과 병합 (merge_tc_chunks.py)
    ↓
[메인] Step 5: 1차 Excel 출력 (write_excel.py)
    ↓
[에이전트] Step 5.5: 검증 (tc_plan vs tc_data 비교, 보완 TC 생성)
    ↓
보완 TC 있으면 → tc_data에 추가 → Excel 재생성
보완 TC 없으면 → 기존 Excel 유지
    ↓
[메인] Step 6: 형식 검증 + 통계 (validate_and_stats.py)
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
| 에이전트가 기존 파일 재사용 | tc_chunk_*.json 잔존 | 기존 파일 삭제 후 재실행 |
| TC에 위치 정보 없음 | 이미지 분석 미수행 | 에이전트 프롬프트에 이미지 분석 필수 명시 |
| 에이전트 반환에 이미지 목록 없음 | 이미지 분석 건너뜀 | 기존 파일 삭제 + 재실행 |
| pre_analyze.py 실패 | 데이터 형식 오류 | 경고, Step 3 기존 방식 진행 (tc_plan 없이) |
| TC 플래닝 에이전트 실패 | 컨텍스트 초과 등 | 경고, Step 3 기존 방식 진행 |
| tc_plan.json 없음 | 플래닝 단계 실패/비활성 | 청크 에이전트가 기존처럼 독립 동작 (하위 호환) |
| 검증 에이전트 실패 | 에이전트 오류 | 기존 Excel 유지, 검증 건너뜀 |
| 보완 TC 없음 | 검증 통과 | 기존 Excel 유지 |

### 디버깅 명령어

```bash
# Phase 1: 이미지 추출만 실행
py extract_images.py "파일.pptx" --output "output" --quiet

# Phase 1: 텍스트/컴포넌트 추출만 실행
py extract_pptx.py "파일.pptx" "output/pptx_data.json"

# Step 2: 청크 계획 확인
py plan_chunks.py "output/pptx_data.json" --max-pages 15

# Step 2.7a: 사전 분석
py pre_analyze.py "output/pptx_data.json"

# Step 4: TC 청크 병합
py merge_tc_chunks.py "output" --prefix IT_{PREFIX}

# Step 5: Excel 출력만 실행
py write_excel.py "output/tc_data.json" "output/test.xlsx"

# Step 6: 검증 + 통계
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
✓ TC ID 연속성: 정상 (IT_{PREFIX}_001 ~ IT_{PREFIX}_042)
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
