# Reference 매핑 스킬

<command-name>map-reference</command-name>

수동 작성된 TC Excel에 화면정의서(PPTX) 페이지 Reference를 자동 매핑합니다.

## 트리거

- `/map-reference`
- `/mr`

## 자동 트리거 키워드

다음 키워드가 포함되면 자동 실행:
- TC Excel + "Reference" + PPTX
- "참조 매핑"
- "Reference 매핑"
- "레퍼런스 채우기"
- "재 맵핑", "리맵핑"

## 사용법

```
/map-reference "<TC_Excel>" "<화면정의서.pptx>" [--prefix IT_XX] [--overwrite]
```

### 인자

| 인자 | 필수 | 설명 |
|------|------|------|
| TC_Excel | O | 기존 TC Excel 파일 경로 |
| PPTX | O | 화면정의서 PPTX 파일 경로 |
| `--prefix` | X | TC ID 접두사 (기본: 자동 감지) |
| `--overwrite` | X | 기존 Reference 값도 재매핑 |
| `--dry-run` | X | Excel 저장 없이 결과만 출력 |

## 워크플로우

```
[메인 컨텍스트 - 오케스트레이터]
  ├── Step 1: Phase 1 실행 (이미지/텍스트 추출)
  │     ├── py extract_images.py "{PPTX}" --output "{output_dir}" --quiet
  │     └── py extract_pptx.py "{PPTX}" "{output_dir}/pptx_data.json"
  ├── Step 2: TC Excel 읽기
  │     └── py read_tc_excel.py "{TC_Excel}" --output "{output_dir}/tc_input.json" [--overwrite]
  ├── Step 3: 슬라이드 인덱스 생성
  │     └── py build_slide_index.py "{output_dir}/pptx_data.json" --output "{output_dir}/slide_index.json"
  ├── Step 3.5: 기존 ref_chunk_*.json 삭제
  │     └── rm -f "{output_dir}/ref_chunk_*.json"
  ├── Step 3.7: 🆕 공통 기능 매핑 테이블 생성 (에이전트)
  │     └── Agent → {output_dir}/common_function_map.json
  ├── Step 4: 매핑 에이전트 병렬 디스패치 (공통 테이블 공유!)
  │     ├── Agent-1: TC 1~40 → ref_chunk_1.json
  │     ├── Agent-2: TC 41~80 → ref_chunk_2.json
  │     └── Agent-N: TC ... → ref_chunk_N.json
  ├── Step 5: 매핑 결과 병합
  │     └── py merge_ref_chunks.py "{output_dir}" --output "{output_dir}/ref_mapping.json"
  ├── Step 5.5: 검증 에이전트 (저신뢰 TC 이미지 기반 보완)
  │     ├── 저신뢰(<0.85) TC 추출 → 검증 청크 분할
  │     ├── Agent-V1~VN: 이미지+공통테이블로 검증 → verify_result_*.json
  │     └── corrections 반영 → ref_mapping.json 업데이트
  ├── Step 5.7: 🆕 뭉침 재분배 (부모 페이지 → 하위 상세 페이지)
  │     └── py remap_lumped.py → ref_mapping_v2.json (키워드 매칭으로 재분배)
  ├── Step 6: Excel 업데이트
  │     └── py update_tc_excel.py "{TC_Excel}" "{output_dir}/ref_mapping.json" [--output ...]
  ├── Step 7: 🆕 화면정의서 경로 컬럼 추가 (선택)
  │     └── py add_pptx_depth.py → Excel AB열에 슬라이드 breadcrumb 경로
  └── Step 8: 🆕 화면정의서 하이라이트 (선택)
        └── py highlight_pptx.py → TC 반영 Description 텍스트 옥색 형광펜
```

## Step별 상세

### Step 1: Phase 1 (이미지/텍스트 추출)

기존 output 폴더에 pptx_data.json이 이미 있고 **같은 PPTX 파일에서 추출된 것이면** 이 단계를 건너뛸 수 있음.

```bash
cd "{PROJECT_ROOT}/testcase-generator/scripts"
py extract_images.py "{PPTX}" --output "{output_dir}" --quiet
py extract_pptx.py "{PPTX}" "{output_dir}/pptx_data.json"
```

### Step 2: TC Excel 읽기

```bash
cd "{PROJECT_ROOT}/testcase-generator/scripts"
py read_tc_excel.py "{TC_Excel}" --output "{output_dir}/tc_input.json" [--overwrite]
```

출력에서 `total_tcs`와 `tcs_needing_mapping` 확인.

### Step 3: 슬라이드 인덱스 생성

```bash
cd "{PROJECT_ROOT}/testcase-generator/scripts"
py build_slide_index.py "{output_dir}/pptx_data.json" --output "{output_dir}/slide_index.json"
```

### Step 3.5: 기존 청크 파일 삭제

```bash
rm -f "{output_dir}/ref_chunk_*.json"
rm -f "{output_dir}/verify_chunk_*.json"
rm -f "{output_dir}/verify_result_*.json"
```

### Step 3.7: 🆕 공통 기능 매핑 테이블 생성

**핵심 개선**: 에이전트 간 지식 공유를 위해 공통 기능 → 슬라이드 매핑 테이블을 사전 생성.

**에이전트 1개 디스패치** (Opus, foreground):
- `slide_index.json` 읽기
- 핵심 슬라이드 이미지 10~20장 Read하여 내용 확인
- 공통 기능 → 슬라이드 매핑 테이블 생성
- `{output_dir}/common_function_map.json`에 저장

#### 공통 기능 테이블 에이전트 프롬프트

```
너는 화면정의서 슬라이드 분석 에이전트다.

## 임무
슬라이드 인덱스와 주요 슬라이드 이미지를 분석하여
"공통 기능 → 슬라이드 번호" 매핑 테이블을 생성하라.

## 입력 파일
1. slide_index.json: {output_dir}/slide_index.json
2. 슬라이드 이미지: {output_dir}/images/slide_{번호}_fullpage.png

## 작업 절차

1. slide_index.json을 Read하여 전체 슬라이드 구조 파악
2. 주요 슬라이드 이미지 Read (section 시작 페이지 위주):
   - 공통 기능/공통 툴 섹션 (보통 초반~중반)
   - 각 Step의 UI 페이지 (해당 Step 첫 슬라이드)
3. 다음 카테고리별 슬라이드 번호를 정리:

### 필수 매핑 카테고리

- Image Control > 3D (Rotate, Panning, Zooming, Navigation Cube)
- Image Control > MPR (Panning, Zooming, Slice 이동 - Step별 다를 수 있음)
- Save Case (Step별 다를 수 있음)
- Manual (User Manual)
- Reset Current View
- Visibility (On/Off, 투명도)
- 3D Coloring > Preset (Step별 다를 수 있음)
- 3D Coloring > Custom Tuning (Step별 다를 수 있음)
- View Tools > Capture (Step별 다를 수 있음)
- MPR Toolbar (Show/Hide, Cross Section, Measure, Reset View)
- 각 Step 진입/UI 페이지
- Step별 전용 기능 슬라이드

## 출력
파일: {output_dir}/common_function_map.json

```json
{
  "common_function_map": {
    "Image Control > 3D": {
      "description": "3D 영상 조정",
      "default_slide": "24P",
      "step_overrides": { "StepName": "슬라이드" },
      "notes": "특이사항"
    },
    ...
  },
  "step_entry_slides": {
    "Worklist": "82P", "Data Edit": "101P", ...
  },
  "step_specific_slides": {
    "StepName": { "기능": "슬라이드" }
  },
  "key_common_slides": {
    "24P": "설명", "38P": "설명", ...
  }
}
```

## 주의사항
- 이미지의 breadcrumb(상단 경로)을 핵심적으로 확인
- Step별로 다른 슬라이드를 사용하는 경우 step_overrides에 명시
- 확실하지 않은 매핑은 notes에 "확인필요" 표기
```

### Step 4: 매핑 에이전트 디스패치

**TC 분할 기준**: `config.py`의 `REF_MAP_TCS_PER_CHUNK` (기본 40개)

tc_input.json에서 `needs_mapping: true`인 TC만 추출하여 에이전트에 분배.
`--overwrite` 모드일 경우 전체 TC를 대상으로 함.

**에이전트 수 계산**:
```
매핑 필요 TC 수 / REF_MAP_TCS_PER_CHUNK (올림)
최대: REF_MAP_MAX_AGENTS (기본 5)
```

**반드시 Opus 모델 사용**: `model: "opus"`

#### 에이전트 프롬프트 템플릿

```
너는 TC Reference 매핑 에이전트다.

## 임무
주어진 TC 목록의 내용(Title, Depth, Test Step, Expected Result)을 분석하여
가장 관련성 높은 화면정의서 슬라이드 페이지 번호를 찾아 Reference로 매핑하라.

## 입력 파일
1. 🆕 공통 기능 매핑 테이블: {output_dir}/common_function_map.json (반드시 먼저 Read!)
2. slide_index.json: {output_dir}/slide_index.json (전체 읽기)
3. pptx_data.json: {output_dir}/pptx_data.json (후보 슬라이드만 선택적 읽기)
4. 슬라이드 이미지: {output_dir}/images/ (확신 낮을 때 시각적 확인)

## 담당 TC 목록
{tc_list_json}

## 매핑 절차 (TC별)

### 🆕 1단계: 공통 기능 테이블 조회 (우선!)
- TC의 depth2(기능 카테고리)가 공통 기능 테이블에 있는지 확인
- 있으면: default_slide 또는 step_overrides[depth1]로 즉시 매핑 가능
- 없으면: 2단계로 진행

### 2단계: 슬라이드 인덱스 키워드 검색
- TC의 Title, Depth1~4, Test Step에서 기능 키워드를 추출
- slide_index.json의 keyword_index로 후보 슬라이드 3~5개 선정
- section_map도 참고하여 Depth1/2와 일치하는 섹션 우선

### 3단계: 후보 상세 확인
- pptx_data.json에서 후보 슬라이드의 components만 Read
- 컴포넌트명, Description과 TC 내용을 의미 비교

### 4단계: 이미지 확인 (필요시)
- 확신이 낮으면 슬라이드 이미지를 Read하여 시각적 확인
- 이미지 상단 breadcrumb(경로)으로 정확한 위치 판단

### 5단계: 최종 결정
- reference = "{페이지번호}P" (예: "5P", "5P (참조: 3P)")

## 참조(Reference) 형식 규칙
- 기본: "{숫자}P" (예: "42P")
- 크로스 레퍼런스: "{주슬라이드}P (참조: {관련슬라이드}P)"
  - 공통 기능이지만 Step 전용 페이지도 있을 때
  - 예: Data Edit의 3D Rotate → "24P (참조: 101P)"

## Confidence 기준

| 범위 | 의미 |
|------|------|
| 0.95 | 확실 (공통 테이블 + 이미지 확인) |
| 0.90 | 높음 (공통 테이블 일치) |
| 0.85 | 양호 (키워드 다수 일치) |
| 0.70~0.84 | 보통 (섹션 일치, 추가 확인 필요) |
| <0.50 | 낮음 → reference를 빈 문자열로 |

confidence < 0.50이면 reference를 빈 문자열("")로 설정하라.

## 출력
파일: {output_dir}/ref_chunk_{chunk_id}.json

```json
{
  "chunk_id": {chunk_id},
  "mappings": [
    {
      "test_case_id": "IT_OP_001",
      "row_index": 7,
      "reference": "5P",
      "confidence": 0.95,
      "reasoning": "Title 'Save 버튼'이 공통 기능 테이블 Save Case=37P와 일치"
    }
  ]
}
```

## 주의사항
- 🆕 공통 기능 매핑 테이블을 반드시 먼저 참조! (1단계 우선)
- reference 형식은 반드시 "{숫자}P" (예: "5P", "12P")
- 크로스 레퍼런스가 있으면 "5P (참조: 3P)" 형식
- 한 TC에 여러 슬라이드가 관련되면 주 슬라이드를 reference로
- confidence < 0.50이면 빈 문자열로 두어라 (추정 금지)
- JSON 파일을 Write 도구로 저장하라

### 🚨 최구체 페이지 매핑 원칙 (뭉침 방지)

**부모 UI 페이지가 아닌 가장 구체적인 하위 페이지에 매핑하라!**

| ❌ 잘못된 매핑 | ✅ 올바른 매핑 |
|--------------|--------------|
| Crown UI (106P) | Crown > Manipulator(1) (107P) |
| Crown UI (106P) | Crown > Tooth Segment(1) (111P) |
| 공통 툴 > 2D Tools (50P) | 공통 툴 > 2D Tools > Measure Tools(1) (51P) |
| 공통 기능 > 3D 영상 조정 (13P) | 공통 기능 > 2D 영상 조정 > Implant(1) (18P) |
| Worklist > Patient Registration(5) (74P) | Worklist > Case List(2) (78P) |

**판단 기준**: TC의 Description/Step에 하위 페이지 Description의 키워드가 포함되면,
부모 UI 페이지 대신 해당 하위 페이지에 매핑해야 한다.

**흔한 뭉침 패턴**:
- Step UI 개요 페이지에 모든 TC 집중 → 하위 기능별 페이지로 분산 필요
- 공통 기능/공통 툴의 대분류 페이지에 집중 → 소분류 페이지로 분산 필요
- (n/N) 시리즈 중 첫 페이지에만 집중 → 후속 페이지에도 분산 필요
```

### Step 5: 매핑 결과 병합

```bash
cd "{PROJECT_ROOT}/testcase-generator/scripts"
py merge_ref_chunks.py "{output_dir}" --output "{output_dir}/ref_mapping.json"
```

### Step 5.5: 🆕 검증 에이전트 (저신뢰 TC 이미지 기반 보완)

**목적**: 1차 매핑에서 저신뢰(<0.85)인 TC를 이미지로 재확인하여 보완.

**절차**:
1. ref_mapping.json에서 confidence < 0.85인 TC 추출
2. 저신뢰 TC가 있으면 검증 에이전트 디스패치 (최대 5개)
3. 각 에이전트는 `common_function_map.json` + 슬라이드 이미지로 검증
4. corrections를 ref_mapping.json에 반영
5. 검증 통과한 TC의 confidence를 0.90으로 상향

**저신뢰 TC가 없으면 이 단계를 건너뜀.**

#### 검증 에이전트 프롬프트 템플릿

```
너는 TC Reference 매핑 검증 에이전트다.

## 임무
저신뢰 TC의 Reference 매핑이 정확한지 검증하고, 틀리면 수정하라.

## 입력 파일
1. 검증 대상: {output_dir}/verify_chunk_{id}.json
2. 공통 기능 매핑 테이블: {output_dir}/common_function_map.json
3. 슬라이드 이미지: {output_dir}/images/slide_{번호}_fullpage.png

## 검증 절차 (TC별)
1. 공통 기능 매핑 테이블에서 올바른 슬라이드 조회
2. 현재 매핑과 비교
3. 불일치 시 슬라이드 이미지 Read하여 확인
4. confirmed 또는 corrected 판정

## 출력
파일: {output_dir}/verify_result_{id}.json
{corrections 배열}
```

### Step 5.7: 🆕 뭉침 재분배 (부모 페이지 → 하위 상세 페이지)

**목적**: 1차 매핑에서 부모/UI 페이지에 TC가 과도하게 집중된 경우,
하위 상세 페이지의 Description과 키워드 매칭하여 재분배.

**절차**:
1. 슬라이드별 TC 수 집계 → 20개 이상 집중된 슬라이드 탐색
2. 미참조 하위 페이지의 Description 키워드 추출
3. 집중 슬라이드의 각 TC 키워드를 미참조 하위 페이지와 매칭
4. 유의미하게 더 적합한 하위 페이지 발견 시 재매핑
5. ref_mapping_v2.json으로 저장

**실행**:
```bash
cd "{output_dir}"
py remap_lumped.py
```

**판단 기준**:
- TC 키워드와 하위 페이지 키워드의 겹침 점수가 현재 매핑보다 0.05 이상 높으면 이동
- 같은 대 섹션 내에서만 이동 (Cross-section 이동 방지)
- STOPWORDS 제외한 의미 있는 키워드만 사용

### Step 6: Excel 업데이트

```bash
cd "{PROJECT_ROOT}/testcase-generator/scripts"
py update_tc_excel.py "{TC_Excel}" "{output_dir}/ref_mapping.json" [--output "Updated_TC.xlsx"] [--dry-run]
```

### Step 7: 🆕 화면정의서 경로 컬럼 추가 (선택)

TC의 Reference 슬라이드 번호 기반으로 화면정의서 breadcrumb 경로를 Excel에 추가.
참조 페이지도 줄바꿈으로 포함.

```bash
cd "{output_dir}"
py add_pptx_depth.py
```

**출력**: Excel AB열에 `공통 툴 > Visualization Tools > Align Tools` 형태

### Step 8: 🆕 화면정의서 하이라이트 (선택)

TC에 실제 반영된 PPTX Description 텍스트만 옥색 형광펜으로 표시.
TC 키워드와 Description 키워드를 매칭하여 정밀 하이라이트.

```bash
cd "{output_dir}"
py highlight_pptx.py
```

**출력**: `{화면정의서}_Highlighted.pptx` (원본 미수정)

## 메인 컨텍스트 역할 (오케스트레이션만)

**메인에서 하는 일:**
```
✅ Phase 1 스크립트 실행 (Bash)
✅ read_tc_excel.py 실행 (Bash) - total/needing_mapping 수만 확인
✅ build_slide_index.py 실행 (Bash)
✅ 기존 청크 파일 삭제 (Bash)
✅ 공통 기능 테이블 에이전트 디스패치 (Task, foreground)
✅ 매핑 에이전트 디스패치 (Task) - TC 목록 + common_function_map 경로 전달
✅ merge_ref_chunks.py 실행 (Bash)
✅ 저신뢰 TC 추출 → 검증 에이전트 디스패치 (Task)
✅ 검증 결과 반영 → ref_mapping.json 업데이트 (Bash)
✅ 🆕 remap_lumped.py 실행 → 뭉침 재분배 (Bash)
✅ update_tc_excel.py 실행 (Bash)
✅ 🆕 add_pptx_depth.py 실행 → 화면정의서 경로 컬럼 (선택, Bash)
✅ 🆕 highlight_pptx.py 실행 → PPTX 하이라이트 (선택, Bash)
✅ 최종 결과 요약 출력
```

**메인에서 하면 안 되는 일:**
```
❌ pptx_data.json 직접 Read (에이전트가 읽음)
❌ slide_index.json 전체 Read (에이전트가 읽음)
❌ tc_input.json 전체 Read (TC 수만 필요)
❌ TC 내용 직접 매핑 (에이전트 역할)
❌ common_function_map.json 직접 Read (에이전트가 읽음)
```

## 결과 출력

```
============================================================
  Reference 매핑 완료
============================================================
TC Excel:    {TC_Excel}
화면정의서:   {PPTX}
------------------------------------------------------------
총 TC:       1132개
매핑 완료:    1088개 (96.1%)
매핑 실패:    44개 (빈칸 유지)
저신뢰:       0개 (검증 후)
평균 신뢰도:  89.7%
------------------------------------------------------------
출력 파일:    {output_path}
백업 파일:    {backup_path}
============================================================
```

## 요구사항

- `python-pptx`: PPTX 파싱
- `openpyxl`: Excel 읽기/쓰기

## 디버깅 명령어

```bash
# TC Excel 읽기만 실행
py read_tc_excel.py "TC.xlsx" --output "output/tc_input.json"

# 슬라이드 인덱스만 생성
py build_slide_index.py "output/pptx_data.json" --output "output/slide_index.json"

# 매핑 결과 병합만 실행
py merge_ref_chunks.py "output" --output "output/ref_mapping.json"

# 뭉침 재분배만 실행
cd output && py remap_lumped.py

# Excel 업데이트 (dry-run)
py update_tc_excel.py "TC.xlsx" "output/ref_mapping.json" --dry-run

# Excel 업데이트 (실제 적용)
py update_tc_excel.py "TC.xlsx" "output/ref_mapping.json" --output "Updated_TC.xlsx"

# 화면정의서 경로 컬럼 추가
cd output && py add_pptx_depth.py

# 화면정의서 하이라이트
cd output && py highlight_pptx.py
```

## 자주 발생하는 문제 및 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| 부모 UI 페이지에 TC 100+개 집중 | 에이전트가 상세 하위 페이지 무시 | Step 5.7 뭉침 재분배 실행 |
| 미참조 슬라이드 50+개 존재 | 하위 페이지로 분산 안 됨 | remap_lumped.py로 키워드 매칭 재분배 |
| 에이전트 10개 동시 실행 시 Rate Limit | Opus 동시 호출 제한 | 최대 5개 에이전트로 제한 |
| 텍스트 하이라이트 안 보임 | `<a:highlight>` XML 순서 오류 | highlight 요소를 latin/ea 앞에 삽입 |
| 화면정의서 경로에 참조 페이지 누락 | 주 슬라이드만 처리 | add_pptx_depth.py에서 참조 페이지도 줄바꿈 포함 |
