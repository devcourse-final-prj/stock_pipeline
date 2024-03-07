# 파일명 : daily_stock_price_prediction_to_rds.py
#
# 설  명 : 이 스크립트는 주식 종가를 예측하고 데이터베이스에 업데이트하는 작업을 자동화하는 파이썬 스크립트입니다. 주요 기능은 다음과 같습니다:
#         1. 예측을 위한 필요한 정보 가져오기   1) pykis 라이브러리로 Top5 주가 종목을 가져옵니다.
#                                         2) pykrx 라이브러리로 Top5 주가 종목에 대한 10년치 데이터를 가져옵니다.
#                                         3) AWS RDS MySQL mlDB.financial_data에서 다우지수, 나스닥지수, 환율 정보를 가져옵니다. (fetch_financial_data())
#         2. 예측 모델 만들기                1) 예측을 위한 필요한 정보를 가져와서 TensorFlow 라이브러리로 예측 모델을 만들어 어제 Top5 주식이나 특정 날짜의 Top5 주식 종가를 예측합니다. (predict_stock_close_price())
#                                         2) 예측한 데이터를 AWS RDS MySQL mlDB.top5_expectation에 업데이트합니다.
#                                         3) 실행 시간 : 매일 07:20
#         3. 실제 종가 업데이트              1) 폐장이 되면 실제 주식 종가를 AWS RDS MySQL mlDB.top5_expectation에 업데이트합니다.
#                                         2) 실행 시간 : 매일 18:20
#
# 자동 실행 주기 : schedule 라이브러리를 사용하여 매일 특정 시간에 자동으로 작업이 실행되도록 설정되어 있습니다.
#                07:20 => predict_stock_close_price() 함수 호출
#                18:20 => update_close_price() 함수 호출
#
# 스크립트 실행 부분: 스크립트를 실행할 때 명령줄 인수를 사용하여 특정 날짜의 데이터를 처리하도록 구현되어 있습니다.
#                  특정 날짜의 Top5 주가를 예측하고 싶으면 다음과 같이 실행하면 됩니다.
#                  ex) daily_stock_price_prediction_to_rds.py 20240226
#
# 라이브러리 버전  : numpy==1.24.4
#                 pandas==1.4.1
#                 pykrx==1.0.45
#                 tensorflow==2.15.0
#                 DateTime==5.4
#                 PyMySQL==1.0.2
#                 schedule==1.1.0

import numpy as np
import pandas as pd
from pykis import *
from pykrx import stock
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import datetime as dt
import pymysql
import schedule
import time
import sys
import warnings
warnings.filterwarnings('ignore')

# AWS RDS MySQL 접속 정보 설정
DB_ENDPOINT = 'de-4-3-mysql.ch4xfyi6stod.ap-northeast-2.rds.amazonaws.com'
DB_USER = 'admin'
DB_PASSWORD = '1q2w3e4r'
DB_NAME = 'mlDB'

# MySQL에 연결
conn = pymysql.connect(
    host=DB_ENDPOINT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)


def fetch_financial_data(max_attempts=3):
    for attempt in range(max_attempts):
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM financial_data"
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            # 컬럼 이름을 지정하여 데이터프레임 생성
            df_financial_data = pd.DataFrame(rows, columns=['date', 'dow', 'nasdaq', 'exchange'])

            # Ensure the 'date' column is of datetime type
            df_financial_data['date'] = pd.to_datetime(df_financial_data['date'])
            return df_financial_data

        except Exception as e:
            print(f"데이터를 가져오는 중 오류가 발생: {e}")
            if attempt < max_attempts - 1:
                print(f"다음 시도를 위해 잠시 대기")
                time.sleep(5)  # 재시도 전에 5초 대기
            else:
                print(f"{max_attempts}번의 시도 후에도 데이터를 가져오기 실패.")
                return None


def update_close_price(update_date=None, max_attempts=3):
    # 특정 update 날짜가 없거나 특정 날짜가 오늘일 경우(시간 정보를 받아와야하기 때문)
    if (update_date is None) or (datetime.now(KST).date() == update_date.date()):
        update_date = datetime.now(KST)

    print(f"update_close_price() : {update_date}")

    # 오늘 날짜 가져오기
    today = datetime.now(KST).date()

    for attempt in range(max_attempts):
        try:
            # update_date가 오늘 이전 날짜나 오늘 날짜 18:20 이후인 경우만 실행 (주식 폐장 시간 이후)
            if (update_date.date() < today) or \
                    (update_date.hour > 18 or
                     (update_date.hour == 18 and update_date.minute >= 20)):

                update_date_str = update_date.strftime("%Y-%m-%d")

                cursor = conn.cursor()

                # 전날의 top5_expectation 데이터 가져오기
                select_query = "SELECT * FROM mlDB.top5_expectation WHERE date = %s"
                cursor.execute(select_query, (update_date_str,))
                rows = cursor.fetchall()

                for row in rows:
                    stock_code = row[2]
                    # 전날의 종가 가져오기
                    df = stock.get_market_ohlcv_by_date(update_date_str, update_date_str, stock_code)
                    if not df.empty:
                        close_price = df['종가'][0]  # 종가 데이터
                        # top5_expectation 테이블의 close_price 업데이트
                        update_query = "UPDATE mlDB.top5_expectation " \
                                       "SET close_price = %s WHERE date = %s AND stock_code = %s"
                        cursor.execute(update_query, (close_price, update_date_str, stock_code))
                        conn.commit()

                cursor.close()
            else:
                print("업데이트 시간이 아닙니다.")
            break  # 성공하면 반복문 종료

        except Exception as e:
            print(f"시도 {attempt + 1}에서 데이터 업데이트 중 오류 발생: {e}")
            if attempt < max_attempts - 1:
                print(f"다음 시도를 위해 잠시 대기합니다...")
                time.sleep(5)  # 재시도 전에 5초 대기
            else:
                print(f"{max_attempts}번의 시도 후에도 데이터 업데이트 실패.")


def predict_stock_close_price(prediction_date=None):

    # 날짜 설정
    if prediction_date is None:
        prediction_date = datetime.now(KST)

    print(f"predict_stock_close_price() : {prediction_date}")

    prediction_weekday = prediction_date.weekday()

    # 장이 있었던 다음날 예측 -> 월요일(1)부터 금요일(5)까지 실행
    if prediction_weekday >= 0 and prediction_weekday <= 4:
        # Financial data 가져오기
        df_financial_data = fetch_financial_data()

        # TOP5 종목 가져올 날짜 설정 : 월요일이면 지난 금요일 날짜 가져오고, 다른 요일이면 전날 날짜 가져옴
        if prediction_weekday == 0:
            todate = prediction_date - timedelta(days=3)
        else:
            todate = prediction_date - timedelta(days=1)

        # TOP5 종목 가져오기
        rank = KRXFluctRank.fetch(
            # 날짜가 None인 경우 마지막 장 운영일을 기준으로 조회한다.
            start_date=todate,
            # 날짜가 None인 경우 마지막 장 운영일을 기준으로 조회한다.
            end_date=todate,
            # 테이블명
            table='상승',  # '상승', '하락', '거래상위'
            # 시장 구분
            market='전체',  # '전체', '코스피', '코스닥', '코넥스'
            # 수정주가 적용
            proc=True,
            # 정렬 기준
            sort='자동',  # '자동', '등락율', '거래량', '거래대금'
            # 기준에 반대 차순 정렬
            reverse=False,
        )

        # 월요일이 아니면 전날 데이터 날짜로 작업
        fromdate = (prediction_date - timedelta(days=(365 * 10))).strftime("%Y%m%d")
        todate = todate.strftime("%Y%m%d")

        print(f"과거 데이터 가져오는 기간 {fromdate} ~ {todate}")

        prediction_date = prediction_date.strftime("%Y-%m-%d")

        try:
            cursor = conn.cursor()

            # 트랜잭션 시작
            conn.begin()

            # 오늘 날짜의 데이터가 있는 경우, 모두 삭제
            delete_query = f"DELETE FROM top5_expectation WHERE date = '{prediction_date}'"
            cursor.execute(delete_query)

            total = 0
            for item in rank:

                if total >= 5:
                    break

                print("===============================================================")
                print(f"                    {item.isu_abbrv} {item.isu_cd} 예측 ")
                print("===============================================================")

                # 주식 데이터 가져오기
                stock_data = stock.get_market_ohlcv_by_date(fromdate, todate, item.isu_cd)

                if len(stock_data) <= 100:
                    print(f"주식 과거 데이터가 너무 작음 : {len(stock_data)}")
                    continue

                print(stock_data.tail())
                print(f"주식 과거 데이터 길이 : {len(stock_data)}")

                stock_data.reset_index(inplace=True)
                stock_data.rename(
                    columns={"날짜": "date", "시가": "open", "고가": "high",
                             "저가": "low", "종가": "close", "거래량": "volume"},
                    inplace=True)
                # stock_data와 df_financial_data를 'Date' 컬럼을 기준으로 병합
                stock_data = pd.merge(stock_data, df_financial_data, on='date', how='left')

                # 사용할 특성을 선택
                stock_data = stock_data[
                    ['close', 'open', 'high', 'low', 'volume', 'dow', 'nasdaq', 'exchange']]
                stock_data = stock_data.astype(float)

                # null값 삭제
                stock_data = stock_data.dropna()
                print(f"주식 과거 데이터 길이 (NAN 값 제거) : {len(stock_data)}")
                print(stock_data.tail())

                # 데이터를 정규화
                scaler = StandardScaler()
                scaler = scaler.fit(stock_data)
                stock_data_scaled = scaler.transform(stock_data)

                # LSTM 모델에 입력하기 위한 데이터를 준비
                seq_len = 14  # 시퀀스 길이
                input_dim = 8  # 입력 차원 'close', 'open', 'high', 'low', 'volume', 'dow', 'nasdaq', 'exchange'

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

                print(next_day_prediction)

                # 예측 결과를 원래 스케일로 변환
                next_day_prediction_rescaled = scaler.inverse_transform(
                    np.concatenate((next_day_prediction,
                                    np.zeros((next_day_prediction.shape[0], 7))), axis=1))[:, 0]

                # 예측 결과가 NaN이 아닌 경우에만 정수형으로 변환
                print(next_day_prediction_rescaled[0])

                if not np.isnan(next_day_prediction_rescaled[0]):

                    # 어제 종가
                    yesterday_close_price = stock_data['close'].iloc[-1]

                    # 예측한 종가
                    predicted_price_int = int(next_day_prediction_rescaled[0])

                    # 어제 종가와 예측한 종가의 차이 계산
                    price_difference = predicted_price_int - yesterday_close_price

                    # 상승률 혹은 하락률이 어제 종가의 30% 이상 차이가 나면 조정
                    if ((yesterday_close_price * 1.3) < predicted_price_int) or ((yesterday_close_price * 0.7) > predicted_price_int):

                        # 어제 종가의 30% 차이를 예측한 종가에 더하거나 빼서 조정
                        if price_difference > 0:
                            predicted_price_int = yesterday_close_price * 1.3
                        else:
                            predicted_price_int = yesterday_close_price * 0.7

                        print("예측 종가가 어제 종가와 30% 이상 차이가 나서 조정되었습니다.")

                    if predicted_price_int < 0:
                        predicted_price_int = 0
                        print("예측 종가가 음수라 0으로 조정되었습니다.")


                    # SQL 쿼리 실행하여 데이터 추가
                    insert_query = "INSERT INTO top5_expectation " \
                                   "(date, kr_stock_name, stock_code, yesterday_close_price, expected_price, close_price, saved_time) " \
                                   "VALUES (%s, %s, %s, %s, %s, NULL, %s)"
                    cursor.execute(insert_query,
                                   (prediction_date, item.isu_abbrv, item.isu_cd, yesterday_close_price,
                                    predicted_price_int, datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")))

                    # 예측 결과 출력
                    print("예측 종가:", predicted_price_int)
                    total += 1
                else:
                    print("예측 종가 예측 실패")

                # 모든 작업이 성공적으로 수행되었으므로 커밋
                conn.commit()

        except Exception as e:
            print(f"An error occurred: {e}")
            # 예외가 발생했으므로 롤백
            conn.rollback()

        finally:
            # 커서와 연결 종료
            cursor.close()

    else:
        print(f"{prediction_date}은(는) 증시 휴장일입니다.")

KST = dt.timezone(dt.timedelta(hours=9))


def parse_date_argument(arg):
    try:
        # 제공된 인자를 날짜 형식으로 변환
        return datetime.strptime(arg, "%Y%m%d")
    except ValueError:
        # 인자가 "%Y%m%d" 형식이 아닌 경우 오류 메시지 출력 후 None 반환
        print("오류: 인자는 '%Y%m%d' 형식이어야 합니다.")
        return None


# 과거 날짜 top5 데이터 작업시 : 스크립트 실행시 날짜 정보를 인자로 제공한 경우
if len(sys.argv) > 1:
    date_arg = sys.argv[1]
    prediction_date = parse_date_argument(date_arg)
    if prediction_date:
        predict_stock_close_price(prediction_date)
        update_close_price(prediction_date)

# 현재 날짜 top5 데이터 작업시 : 스크립트 실행시 날짜 정보를 인자로 제공하지 않은 경우
else:
    predict_stock_close_price()
    update_close_price()


schedule.every().day.at("07:20").do(predict_stock_close_price)
schedule.every().day.at("18:20").do(update_close_price)

# 실제 실행하게 하는 코드
while True:
    schedule.run_pending()
    time.sleep(1)
