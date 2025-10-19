# Google Perspective API 사용


## 0. uv python package manager 설치 및 환경설정

```bash

# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
brew install uv

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# pip - 추천 X
pip install uv
```
가상환경 sync

```bash
uv sync

# 가상환경 진입
# macOS or Linux
source .venv\bin\activate
# Windows
.venv\Scripts\activate
```

Perspective API docs 설명에 따라 API 설정 및 API 키 발급 -
[Perspective API Docs](https://developers.perspectiveapi.com/s/docs-get-started?language=en_US)

디렉토리 내부에 `.env` 파일 생성 후 Google API key 환경변수 입력

## 1. main.py 수정 및 실행

main.py 파일 안의 아래 내용을 원하는 text로 수정
```python
analyze_request = {
  'comment': { 'text': 'friendly greetings from python' },
  'requestedAttributes': {'TOXICITY': {}}
}
```

```bash
uv run main.py
```

main.py 결과 예시
```
{
  "attributeScores": {
    "TOXICITY": {
      "spanScores": [
        {
          "begin": 0,
          "end": 30,
          "score": {
            "value": 0.025556687,
            "type": "PROBABILITY"
          }
        }
      ],
      "summaryScore": {
        "value": 0.025556687,
        "type": "PROBABILITY"
      }
    }
  },
  "languages": [
    "en"
  ],
  "detectedLanguages": [
    "en"
  ]
}
```