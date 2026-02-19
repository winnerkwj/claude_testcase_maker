# 테스트케이스 자동 생성 프로젝트

## 개요
화면정의서(PPTX)를 분석하여 테스트케이스를 자동 생성하는 도구

## 빠른 시작
```bash
/testcase "{입력파일}.pptx" --prefix IT_{PREFIX}
```

## 주요 명령어

| 명령어 | 단축 | 설명 |
|--------|------|------|
| `/testcase <파일>` | `/tc` | PPTX → TC Excel 자동 생성 |
| `/testcase <파일> --prefix IT_XX` | - | ID 접두사 지정 |
| `/extract-images <파일>` | `/ei` | PPTX에서 이미지 추출 |
| `/validate-tc [파일]` | `/vtc` | TC 품질 검증 |
| `/tc-stats [파일]` | `/stats` | TC 통계 및 분포 분석 |

## 출력 경로

**모든 TC 산출물은 프로젝트 루트의 output 폴더에 저장**:
```
{PROJECT_ROOT}/output
```

설정값은 `testcase-generator/config.py`에서 관리하며, 환경변수 `TC_OUTPUT_DIR`로 오버라이드 가능.

## 프로젝트 구조
```
testcase-generator/
├── config.py                   # 🆕 중앙 설정 파일 (경로, 상수)
├── tc_config.yaml              # 🆕 설정 문서 (Claude용)
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
├── assets/template.xlsx        # 템플릿
├── notes/                      # 학습 기록
│   ├── issues.md               # 이슈 및 해결책
│   ├── patterns.md             # 패턴/안티패턴
│   └── improvements.md         # 개선 아이디어
├── SKILL.md                    # 메인 스킬 정의
├── SKILL-extract-images.md     # 이미지 추출 스킬
├── SKILL-validate-tc.md        # TC 검증 스킬
└── SKILL-tc-stats.md           # TC 통계 스킬

output/                         # 출력 폴더 (프로젝트 루트에 위치)
├── images/                     # 추출된 이미지
├── image_manifest.json         # 이미지 메타데이터
├── pptx_data.json              # PPTX 텍스트/컴포넌트 데이터
├── chunk_plan.json             # 청크 분할 계획
├── tc_chunk_*.json             # 청크별 TC (병렬 처리용)
└── tc_data.json                # 최종 병합된 TC 데이터
```

## TC ID 형식
```
IT_{PREFIX}_{NUM}
예: IT_XX_001, IT_XX_002, IT_XX_003
```
- 기본 접두사: `IT_XX` (환경변수 `TC_PREFIX`로 오버라이드 가능)
- 문서 전체에서 연속 번호 사용
- 페이지별로 초기화하지 않음

## Depth 구조 (시나리오 기반)

| Depth | 역할 | 예시 |
|-------|------|------|
| Depth 1 | 대분류 | Main Layout, Worklist |
| Depth 2 | 중분류/섹션 | 공통 Layout 및 Tool, 환자 관리 |
| Depth 3 | 기능 영역 | 공통레이아웃, Common Tool |
| Depth 4 | 조건/상태 (선택) | 작업내역 없음, 작업내역 있음, "" |

## Depth 4 작성 규칙
**조건/상태 기반** (테스트 유형 아님):
- `작업내역 없음` / `작업내역 있음`: 저장 관련 테스트
- `환자 미선택` / `환자 선택됨`: 환자 관련 테스트
- `""` (빈 문자열): 특별한 조건 없을 때

**❌ 금지**: "표시 확인", "기능 확인", "Hover 확인" (컴포넌트 나열식)

## Excel 출력 구조

### 기본 컬럼 (A~N)
No, Test Case ID, Depth 1~4, Title, Pre-condition, Test Step, Expected Result, 요구사항 ID, Reference, 중요도, Writer

### 테스트 회차 (O~AC)
1차/2차/3차 테스트 각각:
- Result (드롭다운: Pass/Fail/N/T/Block)
- Severity (드롭다운: Critical/Major/Minor/Trivial)
- Comments, Issue #, Tester

### 상단 요약
- 프로젝트명, Version
- Total TC, Pass, Fail, N/T 카운트 (자동 계산)

## 필수 패키지
```bash
pip install python-pptx openpyxl
```

---

## 자동 실행 규칙 (청크 기반 병렬 처리)

Claude는 다음 상황에서 적절한 스킬을 자동 실행합니다.
**중요**: 대용량 문서(15페이지 초과)는 청크 분할 후 병렬 에이전트로 처리합니다.

| 상황 | 자동 실행 | 설명 |
|------|----------|------|
| PPTX 파일 언급 + "TC" 또는 "테스트케이스" | `/testcase` | TC 자동 생성 (청크 기반) |
| PPTX 파일 언급 + "이미지" | `/extract-images` | 이미지 추출 |
| TC 생성 완료 직후 | `validate_and_stats.py` | 자동 검증 + 통계 |
| "검증", "확인", "체크" + Excel/TC 언급 | `/validate-tc` | TC 품질 검증 |
| "통계", "요약", "분포" + TC 언급 | `/tc-stats` | 통계 요약 |
| 오류 발생 시 | 문제 해결 가이드 참조 | 자동 대응 안내 |

### 청크 기반 병렬 처리 워크플로우

```
사용자: "{화면정의서}.pptx로 TC 만들어줘"
→ /testcase 자동 실행

[메인 컨텍스트 - 오케스트레이터]
  ├── Step 1: Phase 1 실행 (이미지/텍스트 추출)
  ├── Step 2: 청크 계획 수립 (plan_chunks.py)
  ├── Step 3: 병렬 에이전트 디스패치
  │     ├── Agent-1: Chunk 1 (1~15P) → tc_chunk_1.json
  │     ├── Agent-2: Chunk 2 (16~30P) → tc_chunk_2.json
  │     └── Agent-3: Chunk 3 (31~45P) → tc_chunk_3.json
  ├── Step 4: 결과 병합 (merge_tc_chunks.py)
  └── Step 5: Excel 출력 + 검증/통계 통합
```

### 청크 기반 처리 이점
- **컨텍스트 초과 방지**: 15페이지 단위로 분할하여 처리
- **병렬 처리**: 최대 3개 에이전트 동시 실행으로 속도 향상
- **실패 복구 용이**: 청크 단위 재시도 가능
- **대용량 문서 지원**: 100+ 페이지 문서도 안정적 처리

### 청크 분할 기준

설정값은 `testcase-generator/config.py`에서 관리 (환경변수로 오버라이드 가능):

| 설정 | 기본값 | 환경변수 |
|------|--------|----------|
| MAX_PAGES_PER_CHUNK | 15 | `TC_MAX_PAGES_PER_CHUNK` |
| MAX_COMPONENTS_PER_CHUNK | 80 | `TC_MAX_COMPONENTS_PER_CHUNK` |
| MAX_PARALLEL_AGENTS | 10 | `TC_MAX_PARALLEL_AGENTS` |
| DEFAULT_TC_PREFIX | IT_XX | `TC_PREFIX` |

### 에이전트 모델 설정

**TC 작성 에이전트는 반드시 Opus 모델 사용**:
```
Task 도구: model: "opus"
```

### 문서 크기별 처리 방식

| 문서 크기 | 처리 방식 | 에이전트 수 |
|----------|----------|------------|
| 15페이지 이하 | 단일 에이전트 | 1 |
| 16~30페이지 | 2청크 병렬 | 2 |
| 31~45페이지 | 3청크 병렬 | 3 |
| 46~150페이지 | N청크 병렬 | 최대 10 (청크 수만큼) |

### 자연어 트리거 예시
```
사용자: "{화면정의서}.pptx로 TC 만들어줘"
→ /testcase 자동 실행 (청크 기반 병렬 처리)

사용자: "이 PPTX에서 이미지 추출해줘"
→ /extract-images 자동 실행

사용자: "생성된 Excel 검증해줘"
→ /validate-tc 자동 실행
```

---

## TC 품질 기준 (시나리오 기반)

### 🔴 시나리오 기반 TC 작성 (핵심!)

**❌ 컴포넌트 나열식 (금지)**:
```
- Save 버튼 표시 확인
- Save 버튼 기능 확인
- Save 버튼 Hover 확인
```

**✅ 시나리오 기반 (권장)**:
```
- 저장 확인 팝업창 (닫기 버튼 클릭 시)
- 저장 확인 팝업창[Save] 버튼
- 저장 확인 팝업창[Don't Save] 버튼
- 저장 확인 팝업창[Cancel] 버튼
- 저장 단축키 입력 (Ctrl+S)
```

### Title 형식 (시나리오 기반)

| 패턴 | 예시 |
|------|------|
| 팝업 트리거 | `저장 확인 팝업창` |
| 팝업 내 버튼 | `저장 확인 팝업창[Save] 버튼` |
| 단축키 동작 | `저장 단축키 입력` |
| 기능 동작 | `Top View 전환`, `프로젝트 추가` |

### Pre-condition 규칙 (선택적)

| 상황 | Pre-condition |
|------|---------------|
| 일반 기능 | `""` (빈 문자열) |
| 팝업 내 테스트 | `저장 확인 팝업창이 표시된 상태` |
| 특정 상태 필요 | `환자선택 > Case 정상 로드` |

**❌ 금지**: 모든 TC에 일괄적으로 Pre-condition 채우기

### Test Step 형식 (구체적 동작)

**필수 규칙:**
- 모든 TC 최소 2단계, 팝업 내 버튼은 3단계 필수
- Step 1은 반드시 진입 동작: "{화면/탭명} 화면 진입"
- 위치 서술자 필수: "좌측 Common Tool 영역의 Save 버튼 클릭"
- 단일 스텝 TC 금지 (목표: 0%)

```
1. Alignment 탭 화면 진입
2. 우측 상단 닫기 버튼 클릭
3. 팝업창 Save 버튼 클릭
```

### Expected Result 형식

```
# 현재 진행중인 상태가 프로젝트에 저장됨
# 저장된 프로젝트 로드시 저장 당시화면 그대로 로드됨
```

- 단축키 포함 가능: `# Top view로 전환됨 (단축키: Numpad 8)`

---

## 불완전한 화면정의서 처리 규칙

화면정의서가 완벽하지 않은 경우의 처리 방법:

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **있는 내용 반드시 반영** | 화면정의서에 있는 정보는 절대 생략 금지 |
| **없는 내용 공란 처리** | 불명확하면 추정하지 말고 공란으로 |
| **공란 셀 시각화** | 노란색 배경 + 코멘트로 수동 작성 필요 부분 표시 |

### 공란 처리 기준

| 상황 | 처리 방법 | 예시 |
|------|----------|------|
| 정보 완전 부재 | 해당 필드 공란 | Pre-condition 정보 없음 → 공란 |
| 정보 불명확 | 해당 필드 공란 | 단축키 추정 불가 → Expected에서 단축키 생략 |
| 확인 필요 | 해당 필드 공란 | 버튼 동작 불명확 → Expected 공란 |

### 공란 가능 필드

- `pre_condition`: 사전 조건 불명확 시
- `test_step`: 테스트 절차 불명확 시
- `expected_result`: 동작 설명 없을 시 (단, Title은 필수)
- `requirement_id`: 항상 공란 허용
- `importance`: 항상 공란 허용

### Excel 공란 표시

- **노란색 배경** (`#FFFF00`): 공란 필드에 자동 적용
- **코멘트**: 마우스 올리면 공란 이유 표시
  - 형식: `[원본] {Description 텍스트}\n[사유] {공란 이유}`

### ⚠️ 절대 금지

| 금지 | 이유 |
|------|------|
| 화면정의서에 있는 내용 생략 | 있는 정보는 반드시 TC에 반영 |
| 추정으로 내용 채우기 | 확실하지 않으면 공란 처리 |
| "모르겠음" 텍스트 작성 | 공란으로 두고 사용자가 수동 작성 |

---

## 자주 발생하는 실수 및 해결책

| 실수 | 원인 | 해결책 |
|------|------|--------|
| **레거시 스크립트 호출** | run_all.py 사용 | 🚫 사용 금지, 청크 에이전트 방식 사용 |
| **JSON 키 불일치** | test_cases vs testcases | 에이전트에게 `testcases` 키 사용 명시 |
| **필드명 불일치** | steps vs test_step 등 | merge_tc_chunks.py가 자동 변환 (수정 완료) |
| **메인 컨텍스트 낭비** | pptx_data.json 직접 읽기 | 에이전트에게 위임, 메인은 스크립트만 실행 |
| TC ID 중복 | 청크 병합 오류 | merge_tc_chunks.py 재실행 |
| Depth 누락 | PPTX 구조 오파싱 | 그룹핑 레벨 확인 |
| 컬럼 형식 오류 | 템플릿 버전 불일치 | template.xlsx 버전 확인 |
| 한글 깨짐 | UTF-8 인코딩 누락 | encoding='utf-8' 확인 |
| Excel 열기 오류 | 파일 잠금 | 기존 Excel 파일 닫기 |
| 에이전트 컨텍스트 초과 | 청크 크기 과다 | --max-pages 값 감소 |
| 청크 병합 순서 오류 | Reference 형식 불일치 | Reference에 페이지 번호 확인 |
| openpyxl 불법 문자 오류 | TC 데이터에 제어 문자 포함 | write_excel.py에서 자동 제거 (수정 완료) |
| Excel에 Test Step 없음 | 필드명 불일치 | merge_tc_chunks.py 재실행 |
| **이미지 분석 누락** | 에이전트 프롬프트 누락 | 에이전트에게 이미지 분석 명시적 지시 |
| TC에 위치 정보 없음 | 이미지 미분석 | output/images/ 이미지 Read 후 TC 재작성 |
| **컴포넌트 나열식 TC** | 시나리오 기반 미준수 | 시나리오 흐름으로 TC 그룹화 |
| **기존 TC 패턴 재사용** | 이전 분석 결과 참조 | 매번 pptx_data.json과 이미지 새로 분석 |
| **depth4 빈 문자열 오탐** | 검증 함수가 빈 문자열을 누락으로 판정 | depth4=""는 정상 (수정 완료) |
| **진입 동작 검출율 낮음** | 키워드가 "진입"만 포함 | "프로그램 실행", "화면에서" 등 확장 (수정 완료) |

---

## 검증 체크리스트

TC 생성 완료 후 필수 확인:
- [ ] TC ID 연속성 (001, 002, 003...)
- [ ] Depth 1~4 모두 채워짐
- [ ] Expected Result에 `#` 형식 사용
- [ ] Reference가 `숫자P` 형식 (예: 5P, 5P (참조: 3P))
- [ ] 페이지 순서대로 TC 작성됨
- [ ] 크로스 레퍼런스 적절히 추가됨
- [ ] 한글 정상 표시
- [ ] 드롭다운 목록 정상 작동 (Pass/Fail/N/T/Block)
- [ ] 템플릿 서식 유지 (셀 너비, 색상)
- [ ] Test Step 최소 2단계 (단일 스텝 TC 0%)
- [ ] 위치 서술자 포함율 70% 이상
- [ ] 진입 동작 포함율 70% 이상

---

## 금지 사항

### 🚫 레거시 스크립트 사용 금지
- **`run_all.py` 호출 금지**: 규칙 기반 TC 생성, Claude 사고 없음
- **`generate_testcase.py` 호출 금지**: 템플릿 기반 TC 생성
- ✅ 대신: 청크 에이전트가 pptx_data.json을 읽고 **직접 사고하여 TC 작성**

### 🚫 하드코딩 금지
TC 내용은 반드시 화면정의서(PPTX) 데이터만 사용
- ❌ "Tool 탭 화면 진입" (탭명 추정)
- ❌ 컴포넌트별 위치 추정 (최소화=우측상단)
- ❌ 키워드 매칭으로 탭명/제품유형 추출
- ✅ PPTX 섹션 제목, 컴포넌트명, Description 그대로 사용

### 🚫 기타 금지
- Excel 출력 시 `openpyxl` 외 다른 라이브러리 사용 금지
- 원본 PPTX 파일 수정 금지
- output 폴더 외 경로에 파일 생성 금지
- 사용자 확인 없이 기존 Excel 파일 덮어쓰기 금지
- 외부 API 호출 금지 (로컬 처리만)

---

## 컨텍스트 절약 가이드라인

### 메인 컨텍스트 역할 (오케스트레이션만)

**메인에서 하는 일:**
```
✅ Phase 1 스크립트 실행 (Bash)
✅ 청크 계획 스크립트 실행 (Bash) - 청크 수만 확인
✅ 에이전트 디스패치 (Task) - 3개씩 병렬
✅ 병합/Excel/검증 스크립트 실행 (Bash)
✅ 최종 결과 요약 출력
```

**메인에서 하면 안 되는 일:**
```
❌ pptx_data.json 내용 Read로 직접 읽기 (컨텍스트 낭비)
❌ chunk_plan.json 전체 내용 Read로 읽기 (청크 수만 필요)
❌ TC 내용 직접 작성 (에이전트 역할)
❌ 각 청크 결과 JSON 상세 확인 (병합 후 검증으로 충분)
```

### 청크 에이전트 역할

**에이전트가 하는 일:**
```
✅ pptx_data.json 읽고 담당 슬라이드 필터링
✅ 🖼️ output/images/ 폴더에서 담당 슬라이드 이미지 분석 (필수!)
✅ 각 컴포넌트 분석하여 TC 직접 작성 (Claude 사고)
✅ 이미지에서 파악한 위치/레이아웃 정보를 TC에 반영
✅ tc_chunk_{id}.json에 저장
✅ 요약만 반환 (TC 수, 파일 경로, 분석한 이미지 수)
```

**이미지 분석으로 파악할 정보:**
- UI 컴포넌트 위치 (좌측상단, 우측하단, 중앙 등)
- 버튼/아이콘 모양 및 배치
- 화면 레이아웃 구조 (헤더, 사이드바, 메인 영역)
- 색상 정보 (배경색, 강조색)

### JSON 키 형식 통일

청크 파일 출력 시 **반드시 `testcases` 키 사용**:
```json
{
  "chunk_id": 1,
  "testcases": [...]  // ⚠️ NOT "test_cases"
}
```

### TC 필드명 규칙

**write_excel.py가 인식하는 필드명**:

| 필드 | Excel용 키 | 청크 에이전트 출력 (허용) |
|------|-----------|------------------------|
| 테스트 절차 | `test_step` | `steps` → 자동 변환 |
| 기대 결과 | `expected_result` | `expected` → 자동 변환 |
| 사전 조건 | `pre_condition` | `precondition` → 자동 변환 |

**참고**: `merge_tc_chunks.py`가 청크 병합 시 필드명을 자동 변환

---

## 디버깅 명령어

개별 단계 실행으로 문제 구간 파악:
```bash
# Phase 1: 이미지 추출만 실행
py extract_images.py "파일.pptx" --output "output" --quiet

# Phase 1: 텍스트/컴포넌트 추출만 실행
py extract_pptx.py "파일.pptx" "output/pptx_data.json"

# Step 2: 청크 계획 확인
py plan_chunks.py "output/pptx_data.json" --max-pages 15

# Step 4: TC 청크 병합
py merge_tc_chunks.py "output" --prefix IT_{PREFIX}

# Step 5: Excel 출력만 실행
py write_excel.py "output/tc_data.json" "output/test.xlsx"

# Step 5: 검증 + 통계 (통합)
py validate_and_stats.py "output/tc_data.json"

# 검증만
py validate_and_stats.py "output/tc_data.json" --validate-only

# 통계만
py validate_and_stats.py "output/tc_data.json" --stats-only
```
