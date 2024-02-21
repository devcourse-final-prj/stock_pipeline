from airflow import DAG
import pandas as pd
from datetime import datetime
import pickle
from pykrx import stock
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.operators.python_operator import PythonOperator


# 데이터 처리 함수
def process_data(**kwargs):
    logger = LoggingMixin().log
    execution_date = kwargs.get('execution_date')  # execution_date 가져오기
    today_formatted = execution_date.strftime('%Y-%m-%d')  # execution_date를 YYYY-MM-DD 형태로 변환
    logger.info(f"작업 실행 날짜: {today_formatted}")

    try:
        # pickle 파일에서 index_search 딕셔너리 불러오기
        with open('data/index_search.pkl', 'rb') as pickle_file:
            index_search = pickle.load(pickle_file)

        # closing_prices_history 불러오기
        closing_prices_history = pd.read_csv("data/closing_prices_history.csv", dtype={'stock_code': str})
        closing_prices_history['date_column'] = pd.to_datetime(closing_prices_history['date_column'])

        new_rows = []  # 추가할 새로운 데이터를 저장할 리스트

        for (sector_code, sector_name), stocks in index_search.items():
            for stock_code, kr_stock_name in stocks:
                # 주식의 과거 OHLCV 데이터를 가져옴
                df = stock.get_market_ohlcv_by_date(today_formatted, today_formatted, stock_code)

                if df.empty:
                    logger.warning(f"데이터가 없습니다: {sector_code}, {stock_code}, {kr_stock_name}")
                    continue

                # 이미 존재하는 데이터인지 확인
                query = f"stock_code == '{stock_code}' & date_column == '{today_formatted}'"
                if not closing_prices_history.query(query).empty:
                    logger.info(f"이미 존재하는 데이터: {sector_code}, {stock_code}, {kr_stock_name}")
                    continue

                # 데이터 추가
                logger.info(f"데이터 추가됨: {sector_code}, {stock_code}, {kr_stock_name}")
                new_row = {
                    'sector_name': sector_name,
                    'stock_code': stock_code,
                    'kr_stock_name': kr_stock_name,
                    'date_column': pd.to_datetime(today_formatted),
                    'closing_price': df.iloc[0]['종가']
                }
                new_rows.append(new_row)

        if new_rows:
            # 새로운 데이터를 DataFrame에 추가
            new_data = pd.DataFrame(new_rows)
            closing_prices_history = pd.concat([closing_prices_history, new_data], ignore_index=True)
            closing_prices_history.drop_duplicates(subset=['sector_name', 'stock_code', 'kr_stock_name', 'date_column'], inplace=True)
            closing_prices_history = closing_prices_history.sort_values(by=['sector_name', 'stock_code', 'kr_stock_name', 'date_column'])
            closing_prices_history.to_csv("data/closing_prices_history.csv", index=False)

    except Exception:
        logger.error("오류 발생", exc_info=True)


default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 2, 18),
    "retries": 1,
}


dag = DAG(
    "stock_graph_local_test",
    default_args=default_args,
    catchup=True,
    schedule_interval="0 18 * * 1-5",
    tags=["stock"],
)

process_data = PythonOperator(
    task_id='process_data',
    python_callable=process_data,
    dag=dag,
)

process_data
