from googleapiclient import discovery
from dotenv import load_dotenv
import os
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import time

# Configuration
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# User-defined parameters
FILE_PATH = "data/sample.csv"  # CSV 파일 경로를 지정하세요
COL_NAME = "changed_query"  # 분석할 컬럼 이름을 지정하세요

# Perspective API에서 측정 가능한 모든 metrics
AVAILABLE_METRICS = [
    "TOXICITY",
    "SEVERE_TOXICITY",
    "IDENTITY_ATTACK",
    "INSULT",
    "PROFANITY",
    "THREAT",
    "SEXUALLY_EXPLICIT",
    "FLIRTATION",
    "ATTACK_ON_AUTHOR",
    "ATTACK_ON_COMMENTER",
    "INCOHERENT",
    "INFLAMMATORY",
    "LIKELY_TO_REJECT",
    "OBSCENE",
    "SPAM",
    "UNSUBSTANTIAL"
]

# 측정할 metrics 선택 (원하는 것만 리스트에 포함)
METRICS_TO_MEASURE = [
    "TOXICITY",
    "SEVERE_TOXICITY",
    "IDENTITY_ATTACK",
    "INSULT",
    "PROFANITY",
    "THREAT"
]


class PerspectiveAPIAnalyzer:
    """Perspective API를 사용하여 텍스트를 분석하는 클래스"""

    def __init__(self, api_key: str, metrics: List[str]):
        """
        Args:
            api_key: Google API Key
            metrics: 측정할 metric 리스트
        """
        self.api_key = api_key
        self.metrics = metrics
        self.client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=api_key,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )
        self.executor = ThreadPoolExecutor(max_workers=10)

    def analyze_text_sync(self, text: str, max_retries: int = 3) -> Dict[str, float]:
        """
        단일 텍스트를 동기적으로 분석 (재시도 로직 포함)

        Args:
            text: 분석할 텍스트
            max_retries: 최대 재시도 횟수

        Returns:
            각 metric의 점수를 담은 딕셔너리
        """
        if not text or pd.isna(text):
            return {f"psp_{metric.lower()}": None for metric in self.metrics}

        for attempt in range(max_retries):
            try:
                analyze_request = {
                    'comment': {'text': str(text)[:20480]},  # API 제한: 최대 20480 characters
                    'requestedAttributes': {metric: {} for metric in self.metrics},
                    'languages': ['en']  # 필요시 수정
                }

                response = self.client.comments().analyze(body=analyze_request).execute()

                # 결과 파싱
                scores = {}
                for metric in self.metrics:
                    score = response['attributeScores'][metric]['summaryScore']['value']
                    scores[f"psp_{metric.lower()}"] = score

                return scores

            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 1.0
                    print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s due to: {error_msg[:80]}")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed after {max_retries} attempts: {error_msg[:100]}")
                    return {f"psp_{metric.lower()}": None for metric in self.metrics}

        return {f"psp_{metric.lower()}": None for metric in self.metrics}

    async def analyze_text_async(self, text: str) -> Dict[str, float]:
        """
        단일 텍스트를 비동기적으로 분석 (ThreadPoolExecutor 사용)

        Args:
            text: 분석할 텍스트

        Returns:
            각 metric의 점수를 담은 딕셔너리
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self.executor, self.analyze_text_sync, text)
        return result

    async def analyze_batch_async(self, texts: List[str], batch_size: int = 3) -> List[Dict[str, float]]:
        """
        여러 텍스트를 비동기적으로 배치 분석

        Args:
            texts: 분석할 텍스트 리스트
            batch_size: 동시에 처리할 요청 수

        Returns:
            각 텍스트의 점수를 담은 딕셔너리 리스트
        """
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            tasks = [self.analyze_text_async(text) for text in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            # 배치 간 대기 시간 추가
            await asyncio.sleep(1.5)
        return results

    def cleanup(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)


def get_result_path(input_path: str) -> str:
    """
    결과 파일 경로 생성

    Args:
        input_path: 입력 CSV 파일 경로

    Returns:
        결과 파일 경로 (./result/원래이름_result.csv)
    """
    input_file = Path(input_path)
    result_dir = Path("./result")
    result_dir.mkdir(exist_ok=True)

    original_name = input_file.stem
    result_path = result_dir / f"{original_name}_result.csv"

    return str(result_path)


def load_or_create_result_df(input_path: str, result_path: str, col_name: str, metrics: List[str]) -> tuple:
    """
    결과 파일을 로드하거나 새로 생성

    Args:
        input_path: 입력 CSV 파일 경로
        result_path: 결과 CSV 파일 경로
        col_name: 분석할 컬럼 이름
        metrics: 측정할 metric 리스트

    Returns:
        (원본 데이터프레임, 결과 데이터프레임, 시작 인덱스)
    """
    # 원본 데이터 로드
    df_original = pd.read_csv(input_path)

    if col_name not in df_original.columns:
        raise ValueError(f"Column '{col_name}' not found in the CSV file. Available columns: {df_original.columns.tolist()}")

    # 결과 파일이 이미 존재하는지 확인
    result_file = Path(result_path)

    if result_file.exists():
        print(f"Found existing result file: {result_path}")
        df_result = pd.read_csv(result_path)

        # 어디까지 처리되었는지 확인
        metric_cols = [f"psp_{metric.lower()}" for metric in metrics]

        # 모든 metric이 None이 아닌 마지막 행 찾기
        completed_mask = df_result[metric_cols].notna().all(axis=1)
        if completed_mask.any():
            start_idx = completed_mask[::-1].idxmax() + 1
        else:
            start_idx = 0

        print(f"Resuming from index {start_idx} (already processed {start_idx} rows)")
    else:
        print(f"Creating new result file: {result_path}")
        df_result = df_original.copy()

        # 새로운 컬럼 추가
        for metric in metrics:
            col = f"psp_{metric.lower()}"
            df_result[col] = None

        start_idx = 0

    return df_original, df_result, start_idx


def save_progress(df: pd.DataFrame, result_path: str):
    """
    진행 상황을 저장

    Args:
        df: 저장할 데이터프레임
        result_path: 저장 경로
    """
    df.to_csv(result_path, index=False)


async def process_texts(
    analyzer: PerspectiveAPIAnalyzer,
    df_result: pd.DataFrame,
    texts: List[str],
    start_idx: int,
    result_path: str,
    batch_size: int = 5,
    save_interval: int = 10
):
    """
    텍스트들을 처리하고 주기적으로 저장

    Args:
        analyzer: PerspectiveAPIAnalyzer 인스턴스
        df_result: 결과를 저장할 데이터프레임
        texts: 분석할 텍스트 리스트
        start_idx: 시작 인덱스
        result_path: 결과 저장 경로
        batch_size: 배치 크기
        save_interval: 저장 주기
    """
    total = len(texts)

    print(f"\nProcessing {total} texts from index {start_idx}...")

    with tqdm(total=total, initial=0, desc="Analyzing") as pbar:
        for i in range(0, total, batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_indices = list(range(start_idx + i, start_idx + i + len(batch_texts)))

            # 배치 분석
            results = await analyzer.analyze_batch_async(batch_texts, batch_size=batch_size)

            # 결과 저장
            for idx, result in zip(batch_indices, results):
                for col, value in result.items():
                    df_result.at[idx, col] = value

            pbar.update(len(batch_texts))

            # 주기적으로 파일에 저장
            if (i + batch_size) % (save_interval * batch_size) == 0:
                save_progress(df_result, result_path)
                print(f"\nProgress saved at index {start_idx + i + len(batch_texts)}")

    # 최종 저장
    save_progress(df_result, result_path)
    print(f"\nAll results saved to {result_path}")


async def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("Perspective API Text Analyzer")
    print("=" * 50)
    print(f"\nConfiguration:")
    print(f"  Input file: {FILE_PATH}")
    print(f"  Column name: {COL_NAME}")
    print(f"  Metrics to measure: {METRICS_TO_MEASURE}")
    print(f"  API Key: {'***' + API_KEY[-4:] if API_KEY else 'NOT SET'}")
    print()

    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    # 결과 파일 경로 생성
    result_path = get_result_path(FILE_PATH)

    # 데이터 로드
    df_original, df_result, start_idx = load_or_create_result_df(
        FILE_PATH, result_path, COL_NAME, METRICS_TO_MEASURE
    )

    # 분석할 텍스트 추출
    texts_to_analyze = df_original[COL_NAME].iloc[start_idx:].tolist()

    if len(texts_to_analyze) == 0:
        print("All texts have been analyzed already!")
        return

    # Analyzer 생성
    analyzer = PerspectiveAPIAnalyzer(API_KEY, METRICS_TO_MEASURE)

    try:
        # 텍스트 처리
        await process_texts(
            analyzer=analyzer,
            df_result=df_result,
            texts=texts_to_analyze,
            start_idx=start_idx,
            result_path=result_path,
            batch_size=3,  # 동시 처리할 요청 수 (SSL 에러 방지)
            save_interval=5  # 5 * batch_size마다 저장 (15개마다)
        )

        print("\n" + "=" * 50)
        print("Analysis completed successfully!")
        print("=" * 50)

        # 간단한 통계 출력
        print("\nStatistics:")
        for metric in METRICS_TO_MEASURE:
            col = f"psp_{metric.lower()}"
            mean_score = df_result[col].mean()
            print(f"  {metric}: mean = {mean_score:.4f}")

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Progress has been saved.")
        save_progress(df_result, result_path)
    except Exception as e:
        print(f"\n\nError occurred: {str(e)}")
        save_progress(df_result, result_path)
        raise
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
