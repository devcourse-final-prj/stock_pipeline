from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
from time import strftime
import datetime as dt
import pytz

import numpy as np
import pandas as pd
from pykis import *
from pykrx import stock
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler

import pendulum
# from plugins import slack
import logging

LOCAL_TZ = pendulum.timezone("Asia/Seoul")

def get_Redshift_connection(autocommit=True):
    hook = PostgresHook(postgres_conn_id='redshift_dev_db')
    conn = hook.get_conn()
    conn.autocommit = autocommit
    return conn.cursor()

def load_predictions_to_db(**context):
    logging.info("load_predictions_to_db started")
    schema = context["params"]["schema"]
    table = context["params"]["table"]

    stock_prediction_info = context["task_instance"].xcom_pull(key="return_value", task_ids="predict_closing_prices")
    execution_date = context['execution_date']
    # UTC 시간을 로컬 시간으로 변환 (예시로 'Asia/Seoul' 사용)
    local_time = execution_date.astimezone(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d')

    # BEGIN과 END를 사용해서 SQL 결과를 트랜잭션으로 만들어주는 것이 좋음
    cur = get_Redshift_connection()
    try:
        cur.execute("BEGIN;")
        # 테이블이 존재하는지 확인
        cur.execute(f"SELECT to_regclass('{schema}.{table}');")
        exists = cur.fetchone()[0]

        if not exists:
            # 테이블이 존재하지 않는 경우, 새 테이블 생성
            cur.execute(f"""
                CREATE TABLE {schema}.{table} (
                    date DATE,
                    kr_stock_name VARCHAR(100),
                    stock_code VARCHAR(50),
                    expected_price INT
                );
            """)
        else:
            # 테이블이 이미 존재하는 경우, 기존 데이터 삭제
            cur.execute(f"DELETE FROM {schema}.{table};")
        # INSERT 쿼리 실행
        for stock in stock_prediction_info:
            name = stock[0]
            code = stock[1]
            value = stock[2]
            print(name, "-", code, ":", value)
            cur.execute(f"""
                INSERT INTO {schema}.{table} (date, kr_stock_name, stock_code, expected_price)
                VALUES ('{local_time}', '{name}', '{code}', {value});
            """)
        cur.execute("COMMIT;")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        cur.execute("ROLLBACK;")
        raise
    finally:
        cur.close()  # 데이터베이스 연결을 닫습니다.
        logging.info("load done")

def predict_closing_prices(**context):

    stock_items = context["task_instance"].xcom_pull(key="return_value", task_ids="fetch_stock_data")

    stock_info = []

    # for 문을 사용하여 stock_items 리스트의 각 항목에 접근
    for item in stock_items:
        # 각 항목의 주식 이름, 종목 코드, 그리고 데이터를 출력
        logging.info(f"Name: {item['name']}, Code: {item['code']}, Data: {item['data']}")

        # 주식 데이터 가져오기
        stock_data = pd.DataFrame(item['data'])
        stock_data.reset_index(inplace=True)
        stock_data.rename(columns={"날짜": "Date", "시가": "Open", "고가": "High", "저가": "Low", "종가": "Close", "거래량": "Volume"},
                          inplace=True)

        # 시각화를 위해 날짜 데이터를 별도로 저장
        dates = pd.to_datetime(stock_data['Date'])

        # 사용할 특성을 선택
        stock_data = stock_data[['Close', 'Open', 'High', 'Low', 'Volume']]
        stock_data = stock_data.astype(float)

        # 데이터를 정규화
        scaler = StandardScaler()
        scaler = scaler.fit(stock_data)
        stock_data_scaled = scaler.transform(stock_data)

        # LSTM 모델에 입력하기 위한 데이터를 준비
        seq_len = 14  # 시퀀스 길이
        input_dim = 5  # 입력 차원 'Close', 'Open', 'High', 'Low', 'Volume'

        X = []
        Y = []

        # 데이터 준비
        for i in range(seq_len, len(stock_data_scaled)):
            X.append(stock_data_scaled[i - seq_len:i])
            Y.append(stock_data_scaled[i][0])  # 다음 날 종가 예측

        X, Y = np.array(X), np.array(Y)

        # LSTM 모델을 정의
        model = Sequential()
        model.add(LSTM(64, input_shape=(seq_len, input_dim), return_sequences=True))
        model.add(LSTM(32, return_sequences=False))
        model.add(Dense(1))  # 단일 값을 예측하므로 출력 차원을 1로 설정

        # 학습률을 설정하고 모델을 컴파일
        learning_rate = 0.01
        optimizer = Adam(learning_rate=learning_rate)
        model.compile(optimizer=optimizer, loss='mse')

        # 모델 학습
        model.fit(X, Y, epochs=30, batch_size=32, validation_split=0.1, verbose=1)

        # 다음 날 종가 예측
        # 마지막 `seq_len` 일의 데이터를 사용하여 다음 날의 종가 예측
        last_sequence = np.expand_dims(stock_data_scaled[-seq_len:], axis=0)
        next_day_prediction = model.predict(last_sequence)

        # 예측 결과를 원래 스케일로 변환
        next_day_prediction_rescaled = scaler.inverse_transform(
            np.concatenate((next_day_prediction, np.zeros((next_day_prediction.shape[0], 4))), axis=1))[:, 0]

        logging.info("=====다음 날 예측 종가=====")
        stock_info.append([item['name'], item['code'], int(next_day_prediction_rescaled[0])])
        logging.info(int(next_day_prediction_rescaled[0]))

    return stock_info

def fetch_stock_data(**context):
    # TOP5 종목 가져오기
    rank = KRXLimitRank.fetch(
        # 날짜가 None인 경우 마지막 장 운영일을 기준으로 조회한다.
        date=None,
        # 테이블명
        table='상한가',  # 또는 '하한가'
        # 시장 구분
        market='전체',  # '전체', '코스피', '코스닥', '코넥스'
        # 정렬 기준
        sort='거래량',  # '거래량', '거래대금'
        # 기준에 반대 차순 정렬
        reverse=False,
    )

    KST = dt.timezone(dt.timedelta(hours=9))

    # Today's date
    today = datetime.now(KST)
    # Date 10 years ago
    ten_years_ago = today - timedelta(days=365 * 10)

    # Format dates as "yyyymmdd"
    today_str = today.strftime("%Y%m%d")
    ten_years_ago_str = ten_years_ago.strftime("%Y%m%d")

    stock_items = []

    for i, item in enumerate(rank):

        if i >= 5:
            break
        # 주식 데이터 가져오기
        stock_data = stock.get_market_ohlcv_by_date(ten_years_ago_str, today_str, item.isu_cd)

        if len(stock_data) <= 100:
            print(f"주식 과거 데이터가 너무 작음 : {len(stock_data)}")
            continue

        stock_items.append({
            "name": item.isu_abbrv,
            "code": item.isu_cd,
            "data": stock_data
        })

    return stock_items

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1, tzinfo=LOCAL_TZ),
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 10,
    'retry_delay': timedelta(minutes=5),
    # 'on_failure_callback':slack.on_failure_callback,
}

dag = DAG(
    'daily_stock_price_prediction_dag',
    default_args=default_args,
    description='Fetches stock prices and predicts next day closing prices',
    schedule_interval='0 5 * * *',  # 매일 새벽 5시에 실행
    catchup=False,
)

fetch_stock_data = PythonOperator(
    task_id='fetch_stock_data',
    python_callable=fetch_stock_data,
    params={
    },
    dag=dag,
)

predict_closing_prices = PythonOperator(
    task_id='predict_closing_prices',
    python_callable=predict_closing_prices,
    params={
     },
    dag=dag,
)

load_predictions_to_db = PythonOperator(
    task_id='load_predictions_to_db',
    python_callable=load_predictions_to_db,
    params = {
        'schema': 'analytics',
        'table': 'ml_top5_expectation'
    },
    dag=dag,
)

fetch_stock_data >> predict_closing_prices >> load_predictions_to_db