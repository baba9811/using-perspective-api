# Perspective API Text Analyzer

Google Perspective API를 사용하여 CSV 파일의 텍스트 데이터를 분석하는 도구입니다. Toxicity, 욕설, 위협 등 다양한 텍스트 속성을 자동으로 측정합니다.

## 주요 기능

- 📊 **CSV 배치 처리**: 대량의 텍스트 데이터를 자동으로 분석
- 🔄 **중단 지점 재개**: 중단 후 다시 실행하면 자동으로 이어서 처리
- 💾 **주기적 저장**: 일정 간격마다 자동 저장하여 데이터 손실 방지
- 🔁 **재시도 로직**: 네트워크 오류 시 자동 재시도 (Exponential backoff)
- 🌍 **다국어 지원**: 한국어, 영어 등 여러 언어 분석 가능
- 📈 **16가지 Metrics**: Toxicity 외에도 다양한 속성 측정 가능

---

## 설치 및 환경설정

### 1. 저장소 클론

```bash
git clone https://github.com/baba9811/using-perspective-api.git
cd using-perspective-api
```

### 2. Python 패키지 설치

**방법 1: uv 사용 (추천)**

```bash
# uv 설치
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
brew install uv

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 가상환경 sync
uv sync

# 가상환경 진입
# macOS or Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

**방법 2: pip 사용**

```bash
pip install -r requirements.txt
```

### 3. API 키 설정

1. [Perspective API Docs](https://developers.perspectiveapi.com/s/docs-get-started?language=en_US)를 참고하여 Google API 키 발급
2. 프로젝트 루트에 `.env` 파일 생성:

```bash
GOOGLE_API_KEY=your_api_key_here
```

---

## 사용 방법

### 1. 설정 변경 (main.py 상단)

```python
# User-defined parameters
FILE_PATH = "data/sample.csv"      # 분석할 CSV 파일 경로
COL_NAME = "text"         # 분석할 컬럼 이름
LANGUAGE = "ko"                    # 분석 언어 (en, ko, es, fr, de, it, pt, ru, ja, zh 등)

# Performance settings
SAVE_INTERVAL = 10                 # N개 처리마다 결과 저장
DELAY_BETWEEN_REQUESTS = 0.5       # 요청 간 대기 시간(초) - rate limit 조절

# 측정할 metrics 선택 (원하는 것만 리스트에 포함)
METRICS_TO_MEASURE = [
    "TOXICITY",
    "SEVERE_TOXICITY",
    "IDENTITY_ATTACK",
    "INSULT",
    "PROFANITY",
    "THREAT"
]
```

### 2. 실행

```bash
uv run main.py

# or
python main.py
```

### 3. 출력 예시

```
==================================================
Perspective API Text Analyzer
==================================================

Configuration:
  Input file: data/sample.csv
  Column name: changed_query
  Language: ko
  Metrics to measure: ['TOXICITY', 'SEVERE_TOXICITY', 'IDENTITY_ATTACK', 'INSULT', 'PROFANITY', 'THREAT']
  Save interval: every 10 items
  Request delay: 0.5s (~120 req/min)
  API Key: ***Hx5A

Creating new result file: result/sample_result.csv

Processing 500 texts from index 0...
Saving progress every 10 items
Rate: ~120 requests/minute

Analyzing: 100%|████████████████████| 500/500 [04:10<00:00,  2.00it/s]
Progress saved at index 100
Progress saved at index 200
...

==================================================
Analysis completed successfully!
==================================================

Statistics:
  TOXICITY: mean = 0.1234
  SEVERE_TOXICITY: mean = 0.0567
  ...
```

---

## 성능 설정 가이드

### 추천 설정값

#### 빠른 처리 (rate limit 걱정 없는 경우)
```python
DELAY_BETWEEN_REQUESTS = 0.5  # 분당 ~120개
SAVE_INTERVAL = 20
```
- **예상 시간**: 500개 기준 약 4분
- **주의**: SSL 에러 발생 가능

#### 안정적 처리 (SSL 에러 최소화) ⭐ 추천
```python
DELAY_BETWEEN_REQUESTS = 1.2  # 분당 ~50개
SAVE_INTERVAL = 10
```
- **예상 시간**: 500개 기준 약 10분
- **장점**: 안정적이면서도 빠름

#### 매우 안정적 (공식 rate limit 준수)
```python
DELAY_BETWEEN_REQUESTS = 1.5  # 분당 ~40개
SAVE_INTERVAL = 10
```
- **예상 시간**: 500개 기준 약 12.5분
- **장점**: 에러 최소화

---

## 사용 가능한 Metrics

Perspective API에서 측정 가능한 16가지 속성:

| Metric | 설명 |
|--------|------|
| `TOXICITY` | 전반적인 독성/유해성 |
| `SEVERE_TOXICITY` | 심각한 독성 |
| `IDENTITY_ATTACK` | 정체성 기반 공격 |
| `INSULT` | 모욕 |
| `PROFANITY` | 욕설/비속어 |
| `THREAT` | 위협 |
| `SEXUALLY_EXPLICIT` | 성적으로 노골적인 내용 |
| `FLIRTATION` | 유혹/작업 멘트 |
| `ATTACK_ON_AUTHOR` | 작성자에 대한 공격 |
| `ATTACK_ON_COMMENTER` | 댓글 작성자에 대한 공격 |
| `INCOHERENT` | 비논리적/지리멸렬 |
| `INFLAMMATORY` | 선동적/논쟁적 |
| `LIKELY_TO_REJECT` | 거부될 가능성 |
| `OBSCENE` | 외설적 |
| `SPAM` | 스팸 |
| `UNSUBSTANTIAL` | 내용 없음 |

`METRICS_TO_MEASURE` 리스트에 원하는 metric만 추가하면 됩니다.

---

## 지원 언어

| 코드 | 언어 |
|------|------|
| `en` | English (영어) |
| `ko` | Korean (한국어) |
| `es` | Spanish (스페인어) |
| `fr` | French (프랑스어) |
| `de` | German (독일어) |
| `it` | Italian (이탈리아어) |
| `pt` | Portuguese (포르투갈어) |
| `ru` | Russian (러시아어) |
| `ja` | Japanese (일본어) |
| `zh` | Chinese (중국어) |

---

## 결과 파일

분석 결과는 `./result/원래파일명_result.csv`에 저장됩니다.

### 결과 파일 형식

원본 CSV의 모든 컬럼 + 새로운 컬럼들:

```csv
changed_query,psp_toxicity,psp_severe_toxicity,psp_identity_attack,psp_insult,psp_profanity,psp_threat
"Hello world",0.025,0.001,0.002,0.003,0.001,0.001
"Bad text",0.856,0.234,0.123,0.567,0.789,0.345
...
```

---

## 중단 및 재개

**중단 방법**:
- `Ctrl + C` 또는 터미널 종료

**재개 방법**:
- 다시 `python main.py` 실행하면 자동으로 이어서 처리됩니다
- 기존 결과 파일을 읽어서 어디까지 완료되었는지 자동 확인

```
Found existing result file: result/sample_result.csv
Resuming from index 127 (already processed 127 rows)

Processing 373 texts from index 127...
```

---

## 에러 처리

### SSL/네트워크 에러 발생 시

자동으로 재시도합니다 (최대 3회):

```
  Retry 1/3 after 2.0s: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC]...
  Retry 2/3 after 4.0s: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC]...
```

### 해결 방법
1. `DELAY_BETWEEN_REQUESTS` 값을 늘림 (예: 1.2 또는 1.5)
2. 재시도 후에도 실패하면 해당 텍스트는 `None`으로 기록되고 계속 진행

---

## FAQ

**Q: 처리 속도가 너무 느려요**
A: `DELAY_BETWEEN_REQUESTS`를 줄여보세요 (예: 0.5). 단, SSL 에러가 발생할 수 있습니다.

**Q: SSL 에러가 계속 발생해요**
A: `DELAY_BETWEEN_REQUESTS`를 늘려보세요 (예: 1.5). 공식 rate limit는 초당 1회입니다.

**Q: 특정 metric만 측정하고 싶어요**
A: `METRICS_TO_MEASURE` 리스트에서 원하는 것만 남기고 나머지를 삭제하세요.

**Q: 결과 파일을 다시 처음부터 생성하고 싶어요**
A: `./result/` 폴더의 기존 결과 파일을 삭제하고 다시 실행하세요.

---

## 참고 자료

- [Perspective API 공식 문서](https://developers.perspectiveapi.com/s/docs-get-started?language=en_US)
- [Perspective API Attributes 목록](https://developers.perspectiveapi.com/s/about-the-api-attributes-and-languages)
