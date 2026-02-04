# 테스트케이스 작성 패턴 가이드

화면정의서 컴포넌트별 테스트케이스 작성 패턴을 정의합니다.

## 1. 컴포넌트 유형별 패턴

### 1.1 버튼 (Button)

#### 기능 테스트
```
Title: [컴포넌트명] 클릭 기능 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 버튼 클릭
Expected Result:
  # [Description에 명시된 동작]
```

#### UI 상태 테스트
```
Title: [컴포넌트명] UI 상태 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 버튼 영역 확인
Expected Result:
  # 버튼이 정상적으로 표시됨
  - 버튼 텍스트/아이콘 확인
  - 활성화/비활성화 상태 확인
```

#### Hover 상태 테스트
```
Title: [컴포넌트명] Hover 상태 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 버튼에 마우스 오버
Expected Result:
  # Hover 시 시각적 피드백 확인
  - 툴팁 표시 확인 (Hint: [Hint 정보])
  - 커서 변경 확인
```

#### 단축키 테스트 (단축키가 있는 경우)
```
Title: [컴포넌트명] 단축키 동작 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. [단축키] 입력
Expected Result:
  # [버튼 클릭과 동일한 동작 수행]
```

### 1.2 입력 필드 (Input Field)

#### 기능 테스트
```
Title: [컴포넌트명] 입력 기능 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 필드에 값 입력
  3. 입력 확정 (Enter 또는 포커스 이동)
Expected Result:
  # 입력값이 정상적으로 반영됨
```

#### 유효성 검사 테스트
```
Title: [컴포넌트명] 유효성 검사 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 필드에 유효하지 않은 값 입력
  3. 입력 확정
Expected Result:
  # 유효성 검사 오류 메시지 표시
  - 오류 메시지 확인
  - 필드 포커스 유지 또는 하이라이트
```

#### 경계값 테스트
```
Title: [컴포넌트명] 경계값 테스트
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 필드에 최소값 입력 → 확인
  3. [컴포넌트명] 필드에 최대값 입력 → 확인
  4. [컴포넌트명] 필드에 범위 초과값 입력 → 확인
Expected Result:
  # 경계값 처리 정상 확인
  - 최소값: 정상 반영
  - 최대값: 정상 반영
  - 범위 초과: 오류 처리 또는 제한
```

### 1.3 목록/테이블 (List/Table)

#### 목록 표시 테스트
```
Title: [컴포넌트명] 목록 표시 확인
Pre-condition: 프로그램 실행 완료, 데이터 존재
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 영역 확인
Expected Result:
  # 목록이 정상적으로 표시됨
  - 컬럼 헤더 확인
  - 데이터 행 표시 확인
  - 스크롤 기능 확인 (데이터 많은 경우)
```

#### 항목 선택 테스트
```
Title: [컴포넌트명] 항목 선택 확인
Pre-condition: 프로그램 실행 완료, 목록에 데이터 존재
Test Step:
  1. 프로그램 실행 완료
  2. [컴포넌트명] 목록에서 항목 클릭
Expected Result:
  # 선택한 항목이 하이라이트 표시됨
  - 선택 상태 시각적 피드백 확인
```

#### 다중 선택 테스트 (지원하는 경우)
```
Title: [컴포넌트명] 다중 선택 확인
Pre-condition: 프로그램 실행 완료, 목록에 복수 데이터 존재
Test Step:
  1. 프로그램 실행 완료
  2. Ctrl 키 누른 상태에서 복수 항목 클릭
Expected Result:
  # 복수 항목 선택됨
  - 선택된 모든 항목 하이라이트 표시
```

### 1.4 팝업/모달 (Popup/Modal)

#### 팝업 표시 테스트
```
Title: [컴포넌트명] 팝업 표시 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 프로그램 실행 완료
  2. 팝업 트리거 액션 수행 (버튼 클릭 등)
Expected Result:
  # [컴포넌트명] 팝업 정상 표시
  - 팝업 내용 확인
  - 배경 딤처리 확인 (해당하는 경우)
```

#### 팝업 닫기 테스트
```
Title: [컴포넌트명] 팝업 닫기 확인
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 팝업 열기
  2. 닫기 버튼 클릭 또는 ESC 키 입력
Expected Result:
  # 팝업이 정상적으로 닫힘
  - 이전 화면으로 복귀
```

#### 팝업 확인/취소 테스트
```
Title: [컴포넌트명] 팝업 확인/취소 동작
Pre-condition: 팝업 표시 상태
Test Step:
  1. 팝업 표시 상태에서 확인 버튼 클릭
  2. 다시 팝업 표시 후 취소 버튼 클릭
Expected Result:
  # 확인 클릭: 해당 동작 수행
  # 취소 클릭: 동작 취소, 팝업 닫힘
```

### 1.5 드롭다운/콤보박스 (Dropdown/Combobox)

#### 목록 펼치기 테스트
```
Title: [컴포넌트명] 드롭다운 펼치기
Pre-condition: 프로그램 실행 완료
Test Step:
  1. [컴포넌트명] 드롭다운 클릭
Expected Result:
  # 옵션 목록이 펼쳐짐
  - 모든 옵션 표시 확인
```

#### 옵션 선택 테스트
```
Title: [컴포넌트명] 옵션 선택 확인
Pre-condition: 드롭다운 펼쳐진 상태
Test Step:
  1. 원하는 옵션 클릭
Expected Result:
  # 선택한 옵션이 적용됨
  - 드롭다운 닫힘
  - 선택된 값 표시
```

### 1.6 체크박스/라디오 버튼 (Checkbox/Radio)

#### 토글 테스트 (체크박스)
```
Title: [컴포넌트명] 체크박스 토글
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 체크박스 클릭 (체크)
  2. 체크박스 다시 클릭 (해제)
Expected Result:
  # 체크 상태 토글
  - 체크 시 해당 기능 활성화
  - 해제 시 해당 기능 비활성화
```

#### 단일 선택 테스트 (라디오)
```
Title: [컴포넌트명] 라디오 버튼 선택
Pre-condition: 프로그램 실행 완료
Test Step:
  1. 옵션1 라디오 버튼 선택
  2. 옵션2 라디오 버튼 선택
Expected Result:
  # 단일 선택만 가능
  - 옵션2 선택 시 옵션1 자동 해제
```

## 2. 화면 전환 테스트

### 네비게이션 테스트
```
Title: [화면A]에서 [화면B]로 이동
Pre-condition: [화면A] 표시 상태
Test Step:
  1. [네비게이션 버튼/메뉴] 클릭
Expected Result:
  # [화면B] 정상 표시
  - 화면 전환 애니메이션 확인 (해당하는 경우)
  - 필요한 데이터 로딩 확인
```

### 뒤로가기 테스트
```
Title: [화면B]에서 이전 화면으로 복귀
Pre-condition: [화면B] 표시 상태, [화면A]에서 이동한 경우
Test Step:
  1. Back 버튼 클릭
Expected Result:
  # [화면A] 복귀
  - 이전 상태 유지 확인
```

## 3. 데이터 CRUD 테스트

### Create (생성)
```
Title: [대상] 신규 생성
Pre-condition: 생성 가능 권한 보유
Test Step:
  1. 신규 생성 버튼 클릭
  2. 필수 정보 입력
  3. 저장 버튼 클릭
Expected Result:
  # 신규 항목 생성됨
  - 성공 메시지 표시
  - 목록에 신규 항목 추가됨
```

### Read (조회)
```
Title: [대상] 상세 정보 조회
Pre-condition: 조회할 데이터 존재
Test Step:
  1. 목록에서 항목 선택
  2. 상세보기 버튼 클릭 또는 더블클릭
Expected Result:
  # 상세 정보 표시됨
  - 모든 필드 정상 표시
```

### Update (수정)
```
Title: [대상] 정보 수정
Pre-condition: 수정할 데이터 선택 상태
Test Step:
  1. 수정 모드 진입
  2. 정보 변경
  3. 저장 버튼 클릭
Expected Result:
  # 변경사항 반영됨
  - 성공 메시지 표시
  - 변경된 값 표시 확인
```

### Delete (삭제)
```
Title: [대상] 삭제
Pre-condition: 삭제할 데이터 선택 상태
Test Step:
  1. 삭제 버튼 클릭
  2. 확인 팝업에서 확인 클릭
Expected Result:
  # 항목 삭제됨
  - 성공 메시지 표시
  - 목록에서 제거됨
```

## 4. 예외 상황 테스트

### 네트워크 오류
```
Title: 네트워크 연결 끊김 처리
Pre-condition: 프로그램 정상 동작 중
Test Step:
  1. 네트워크 연결 끊기
  2. 서버 통신이 필요한 동작 수행
Expected Result:
  # 오류 메시지 표시
  - 사용자에게 네트워크 상태 안내
  - 재시도 옵션 제공
```

### 권한 오류
```
Title: 권한 없는 기능 접근 시도
Pre-condition: 권한이 제한된 사용자로 로그인
Test Step:
  1. 권한이 필요한 기능 접근 시도
Expected Result:
  # 권한 오류 메시지 표시
  - 기능 접근 차단
```

### 입력 오류
```
Title: 필수 입력 필드 누락
Pre-condition: 입력 폼 표시 상태
Test Step:
  1. 필수 입력 필드 비워둠
  2. 저장 버튼 클릭
Expected Result:
  # 유효성 검사 실패
  - 필수 입력 안내 메시지 표시
  - 해당 필드 하이라이트
```

## 5. 작성 팁

### Test Step 작성 규칙
1. 번호를 붙여 순서대로 작성
2. 사용자 관점에서 구체적인 동작 기술
3. UI 요소명은 [대괄호]로 표시
4. 입력값은 예시 포함

### Expected Result 작성 규칙
1. `#` 마크다운 헤더로 핵심 결과 표시
2. `-` 불릿으로 세부 확인사항 나열
3. 정량적 기준 명시 (가능한 경우)

### Pre-condition 작성 규칙
1. 테스트 시작 전 필요한 상태 명시
2. 데이터 조건, 권한 조건, 화면 상태 등 포함
