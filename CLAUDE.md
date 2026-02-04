# 테스트케이스 자동 생성 프로젝트

## 개요
화면정의서(PPTX)를 분석하여 테스트케이스를 자동 생성하는 도구

## 빠른 시작
```bash
/testcase "예시파일/One v1.0 화면정의서_예시파일.pptx"
```

## 주요 명령어

| 명령어 | 단축 | 설명 |
|--------|------|------|
| `/testcase <파일>` | `/tc` | PPTX → TC Excel 자동 생성 |
| `/testcase <파일> --prefix IT_XX` | - | ID 접두사 지정 |
| `/extract-images <파일>` | `/ei` | PPTX에서 이미지 추출 |
| `/validate-tc [파일]` | `/vtc` | TC 품질 검증 |
| `/tc-stats [파일]` | `/stats` | TC 통계 및 분포 분석 |

## 프로젝트 구조
```
testcase-generator/
├── scripts/
│   ├── extract_images.py       # 이미지 추출 (Phase 1)
│   ├── extract_pptx.py         # PPTX 텍스트/컴포넌트 추출 (Phase 1)
│   ├── write_excel.py          # Excel 출력 (Phase 4)
│   ├── run_all.py              # 기존 통합 실행 (레거시)
│   ├── merge_analysis.py       # 분석 결과 병합 (레거시)
│   └── generate_testcase.py    # TC 생성 (레거시)
├── assets/template.xlsx        # 템플릿
├── output/                     # 출력 폴더
│   ├── images/                 # 추출된 이미지
│   ├── image_manifest.json     # 이미지 메타데이터
│   ├── pptx_data.json          # PPTX 텍스트/컴포넌트 데이터
│   └── tc_data.json            # Claude가 작성한 TC 데이터
├── notes/                      # 학습 기록
│   ├── issues.md               # 이슈 및 해결책
│   ├── patterns.md             # 패턴/안티패턴
│   └── improvements.md         # 개선 아이디어
├── SKILL.md                    # 메인 스킬 정의
├── SKILL-extract-images.md     # 이미지 추출 스킬
├── SKILL-validate-tc.md        # TC 검증 스킬
└── SKILL-tc-stats.md           # TC 통계 스킬
```

## TC ID 형식
```
IT_[PREFIX]_[NUM]
예: IT_OP_001, IT_OP_002, IT_OP_003
```
- 문서 전체에서 연속 번호 사용
- 페이지별로 초기화하지 않음

## Depth 구조

| Depth | 역할 | 예시 |
|-------|------|------|
| Depth 1 | 대분류 | Main Layout, 기능 영역 |
| Depth 2 | 중분류 | 공통 Layout 및 Tool |
| Depth 3 | 소분류 | Title, Save Button |
| Depth 4 | 테스트 항목 | 표시 확인, 기능 확인 |

## 테스트 유형 (Depth 4)
- 표시 확인: UI 표시 테스트
- 기능 확인: 기능 동작 테스트
- Hover 확인: 마우스오버/툴팁
- 유효성 확인: 입력 검증
- 경계값 확인: 최소/최대값
- 선택 확인: 목록 항목 선택
- 닫기 확인: 팝업 닫기

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

## 자동 실행 규칙 (에이전트 위임 방식)

Claude는 다음 상황에서 적절한 스킬을 자동 실행합니다.
**중요**: `/testcase` 실행 시 메인 컨텍스트 절약을 위해 Task 도구로 에이전트에게 위임합니다.

| 상황 | 자동 실행 | 설명 |
|------|----------|------|
| PPTX 파일 언급 + "TC" 또는 "테스트케이스" | `/testcase` | TC 자동 생성 (에이전트 위임) |
| PPTX 파일 언급 + "이미지" | `/extract-images` | 이미지 추출 |
| TC 생성 완료 직후 | `/validate-tc` | 자동 검증 실행 |
| "검증", "확인", "체크" + Excel/TC 언급 | `/validate-tc` | TC 품질 검증 |
| "통계", "요약", "분포" + TC 언급 | `/tc-stats` | 통계 요약 |
| 오류 발생 시 | 문제 해결 가이드 참조 | 자동 대응 안내 |

### 에이전트 위임 워크플로우
```
사용자: "One v1.0 화면정의서.pptx로 TC 만들어줘"
→ /testcase 자동 실행

[메인 컨텍스트]
  1. 파일 확인
  2. Task 도구로 general-purpose 에이전트 위임

[에이전트 내부]
  → Phase 1: 이미지 추출
  → Phase 2: 문서 구조 파악
  → Phase 3: 페이지별 TC 작성
  → Phase 4: Excel 출력
  → 요약 반환

[메인 컨텍스트]
  3. 에이전트 결과 요약 출력
  → /validate-tc 자동 실행
  → /tc-stats 출력
```

### 에이전트 위임 이점
- **메인 컨텍스트 절약**: TC 작성 상세 과정이 에이전트 내부에서만 처리
- **요약만 표시**: 결과 요약만 사용자에게 표시
- **독립적 실행**: Phase 1~4 전체를 에이전트가 자율적으로 수행

### 자연어 트리거 예시
```
사용자: "One v1.0 화면정의서.pptx로 TC 만들어줘"
→ /testcase 자동 실행 (에이전트 위임)

사용자: "이 PPTX에서 이미지 추출해줘"
→ /extract-images 자동 실행

사용자: "생성된 Excel 검증해줘"
→ /validate-tc 자동 실행
```

---

## 자주 발생하는 실수 및 해결책

| 실수 | 원인 | 해결책 |
|------|------|--------|
| TC ID 중복 | 순번 초기화 안됨 | 슬라이드별 순번 리셋 확인 |
| Depth 누락 | PPTX 구조 오파싱 | 그룹핑 레벨 확인 |
| 컬럼 형식 오류 | 템플릿 버전 불일치 | template.xlsx 버전 확인 |
| 한글 깨짐 | UTF-8 인코딩 누락 | encoding='utf-8' 확인 |
| Excel 열기 오류 | 파일 잠금 | 기존 Excel 파일 닫기 |
| 이미지 분석 누락 | JSON 경로 오류 | --with-analysis 경로 확인 |

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

---

## 금지 사항

- **하드코딩 금지**: TC 내용은 반드시 화면정의서(PPTX) 데이터만 사용
  - ❌ "Tool 탭 화면 진입" (탭명 추정)
  - ❌ 컴포넌트별 위치 추정 (최소화=우측상단)
  - ❌ 키워드 매칭으로 탭명/제품유형 추출
  - ✅ PPTX 섹션 제목, 컴포넌트명, Description 그대로 사용
- Excel 출력 시 `openpyxl` 외 다른 라이브러리 사용 금지
- 원본 PPTX 파일 수정 금지
- output 폴더 외 경로에 파일 생성 금지
- 사용자 확인 없이 기존 Excel 파일 덮어쓰기 금지
- 외부 API 호출 금지 (로컬 처리만)

---

## 디버깅 명령어

개별 단계 실행으로 문제 구간 파악:
```bash
# 이미지 추출만 실행 (Phase 1)
py extract_images.py "파일.pptx" --output "output" --quiet

# 텍스트/컴포넌트 추출만 실행 (Phase 1)
py extract_pptx.py "파일.pptx" "output/pptx_data.json"

# Excel 출력만 실행 (Phase 4)
py write_excel.py "output/tc_data.json" "output/test.xlsx"
```
