# 이미지 추출 스킬

<command-name>extract-images</command-name>

화면정의서(PPTX)에서 이미지를 추출하여 분석 준비합니다.

## 트리거

- `/extract-images`
- `/ei`

## 자동 트리거 키워드

다음 키워드가 포함되면 자동 실행:
- "이미지 추출"
- "이미지 분석"
- "화면 캡처"
- PPTX 파일 언급 + "이미지"

## 사용법

```
/extract-images <PPTX_파일_경로> [--output 출력폴더]
```

## 실행 (에이전트 위임)

Task 도구로 Bash 에이전트에게 위임:

```bash
# {PROJECT_ROOT}는 CLAUDE.md가 있는 프로젝트 루트 경로
cd "{PROJECT_ROOT}/testcase-generator/scripts"
py extract_images.py "<PPTX_파일_경로>" --output "<출력폴더>"
```

스크립트 경로는 `config.py`의 `SCRIPTS_DIR`에서 자동 감지됩니다.

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--output`, `-o` | 이미지 출력 폴더 | output/images |
| `--quiet`, `-q` | 보안 경고 메시지 생략 | false |
| `--no-fullpage` | 슬라이드 전체 캡처 건너뛰기 | false |

## 요구사항

- `python-pptx`: PPTX 파싱 및 개별 이미지 추출 (필수)
- `pywin32`: 슬라이드 전체 캡처 (선택, PowerPoint 설치 필요)
  - 미설치 시 개별 이미지 추출만 동작 (graceful fallback)

## 출력 파일

```
output/
├── images/
│   ├── slide_01_fullpage.png      # 슬라이드 전체 캡처 (win32com)
│   ├── slide_02_fullpage.png
│   ├── slide_01_image_00.png      # 개별 삽입 이미지
│   ├── slide_01_image_01.png
│   ├── slide_02_image_00.png
│   └── ...
└── image_manifest.json
```

### image_manifest.json 구조

```json
{
  "pptx_file": "화면정의서.pptx",
  "extraction_date": "2026-02-04T12:00:00",
  "total_images": 15,
  "images": [
    {
      "filename": "slide_01_image_00.png",
      "slide_number": 1,
      "content_type": "image/png",
      "size": {"width_inches": 8.5, "height_inches": 6.0},
      "position": {"left_inches": 1.0, "top_inches": 2.0}
    }
  ],
  "fullpage_images": [
    {
      "filename": "slide_01_fullpage.png",
      "path": "절대경로",
      "slide_number": 1,
      "image_type": "fullpage",
      "content_type": "image/png",
      "size": {"width_px": 1920, "height_px": 1080}
    }
  ],
  "total_fullpage_images": 7,
  "fullpage_export_method": "win32com",
  "fullpage_resolution": {"width": 1920, "height": 1080}
}
```

### fullpage_export_method 값

| 값 | 의미 |
|---|---|
| `win32com` | 정상 내보내기 성공 |
| `unavailable` | pywin32 미설치 또는 PowerPoint 미설치 |
| `skipped` | `--no-fullpage` 옵션으로 건너뜀 |

## 후속 작업

이미지 추출 완료 후:

1. **이미지 분석 요청**:
   ```
   "output/images 폴더의 이미지들을 분석해서 UI 요소 정보를 추출해줘"
   ```

2. **분석 결과와 함께 TC 생성**:
   ```bash
   py run_all.py "화면정의서.pptx" --with-analysis "output/image_analysis.json"
   ```

## 결과 출력

```
============================================================
  이미지 추출 완료
============================================================
소스: 화면정의서.pptx
추출된 이미지: 15개
출력 폴더: output/images/
매니페스트: output/image_manifest.json
------------------------------------------------------------
다음 단계: 이미지 분석 요청
"output/images 폴더의 이미지들을 분석해줘"
------------------------------------------------------------
```
