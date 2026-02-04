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
cd "C:\Users\Osstem\Desktop\testcasemaker V 2.0\testcase-generator\scripts"
py extract_images.py "<PPTX_파일_경로>" --output "<출력폴더>"
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--output`, `-o` | 이미지 출력 폴더 | output/images |
| `--format`, `-f` | 이미지 포맷 (png/jpg) | png |
| `--min-size` | 최소 이미지 크기 (px) | 50 |

## 출력 파일

```
output/
├── images/
│   ├── slide_01_img_001.png
│   ├── slide_01_img_002.png
│   ├── slide_02_img_001.png
│   └── ...
└── image_manifest.json
```

### image_manifest.json 구조

```json
{
  "source": "화면정의서.pptx",
  "extracted_at": "2026-02-04T12:00:00",
  "total_images": 15,
  "images": [
    {
      "filename": "slide_01_img_001.png",
      "slide_number": 1,
      "slide_title": "Main Layout",
      "position": {"x": 100, "y": 200, "width": 800, "height": 600},
      "size_bytes": 45678
    }
  ]
}
```

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
