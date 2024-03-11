# Stock Data Flow Project

<img src="https://github.com/eclipse25/eclipse25.github.io/assets/109349939/b703fde0-9db4-49d3-91a7-0cd31d58a63d" width="600" alt="title">


### 프로젝트 주제

- 주식 종목들의 과거, 현재, 미래 데이터를 수집하고 처리하는 데이터 파이프라인을 구성하고 각각의 기능으로 보여 주기 위한 웹 서비스인 Stocksight를 구현하는 프로젝트

### [프로젝트 보고서](https://www.notion.so/Project-Report-0eac3062c1af42bd94c22285214bd75d#f4c2ee2e6071462eaf297b3ec576d359)

### 프로젝트 참여자 및 주요 역할

| 이름 | 주요 역할 |
|---|---|
| 유승상 | AWS 인프라 · Kafka 클러스터 구축, 실시간 데이터 파이프라인(Kafka), 대시보드 구성 |
| 윤서진 | Django 서버 구축, 배포 자동화, 웹 개발, 이동평균선 데이터 ETL(Airflow) · 기능 구현 |
| 이정훈 | PM, AWS 인프라(Airflow) 구축, 손익 계산 데이터 ETL(Airflow) · 기능 구현 |
| 최윤주 | 머신 러닝 데이터 ETL(Airflow), 예측 모델 구현, 대시보드 구성 |



## 활용 기술 및 프레임워크

<img src="https://github.com/eclipse25/eclipse25.github.io/assets/109349939/97e39ec3-2375-4103-b2d2-a3e272191bf0" width="800" alt="structure">

- **서버 환경**
    - AWS EC2, S3
    - Google Cloud Compute Engine
- **데이터 파이프라인**
    - Apache Airflow
    - Apache Kafka, Zookeeper
    - AWS RDS
    - Google Cloud SQL(postgres)
- **데이터 시각화**
    - Apache Superset
    - Django, gunicorn, nginx
- **협업 도구**
    - Github
    - Notion
    - Slack

## 활용 데이터

- [한국투자 증권 국내주식시세 API](https://apiportal.koreainvestment.com/apiservice/oauth2#L_5c87ba63-740a-4166-93ac-803510bb9c02)
- yfinance 라이브러리
    - 다우존스 지수 (DJI)
    - 나스닥 종합주지수 (IXIC)
    - 환율 정보
- pykis 라이브러리
    - 상승률 Top5 주가 종목 리스트
- [pykrx 라이브러리](https://github.com/sharebook-kr/pykrx)
    - Top5 주가 종목에 대한 시가, 고가, 저가, 종가, 거래량 10년치 데이터
    - 시가총액 상위 종목 데이터
    - 종목 별 일간 종가 데이터

## 프로젝트 수행 과정

### Airflow, Kafka, Superset 서버 및 환경 구성

- 관리자는 Public Subnet에 있는 Bastion host를 통해 어플리케이션에 접근 가능
- 장고 서버 및 일반 사용자들의 어플리케이션 웹서버 요청, Reverse Proxy, Load Balancing 처리를 위해 ALB 생성
- 어플리케이션 인스턴스는 Private Subnet에 배치
- 각 AZ의 Public Subnet에 NAT 생성
- RDS는 Public Access 허용하여 외부에서 접근 가능

### Airflow 환경 구축 in AWS

- EC2 (webserve/ scheduler , Celery Worker), RDS, Elasticache, S3로 구성
    - ALB, NGW, Bastion host 는 public, 나머지 airflow 관련 인스턴스는 private으로 설정
- 작업에 대한 접근은 Bation host (public) 을 통해 접근, 웹페이지에 대한 접근은 ALB를 통해서 8080 port만 접속 가능하도록 설정
- Celery Executor(Redis)로 작업 할당 및 진행
- 작업 후 저장 되는 곳은 DAG 마다 다르게 설정 , 저장된 데이터는 Superset 혹은 Django 웹페이지로 구현

### [데이터 ETL - Airflow](https://github.com/devcourse-final-prj/airflow)

- **머신러닝 데이터 수집**
    
    [daily_financial_data_to_rds_dag.py](https://github.com/devcourse-final-prj/airflow/blob/main/dags/daily_financial_data_to_rds_dag.py)
    
    - 사용한 라이브러리: yifinance
        - 2014년부터 어제까지의 다우 지수, 나스닥 지수, 환율 정보
    - 실행 시간 : 매일 오전 7시
    - DB : AWS RDS MySQL mlDB.financial_data
    - 수집한 데이터는 ML 주가 예측과 Superset 대시보드 구성에 사용
    
- **이동평균선 데이터 수집**
    
    [stock_daily_closing_price.py](https://github.com/devcourse-final-prj/airflow/blob/main/dags/stock_daily_closing_price.py)
  
    - 사용한 라이브러리: pykrx
    - 실행 시간 : 장 종료 후 평일(월-금) 오후 6시
    - 데이터 흐름
        1. S3에서 2021년 1월부터 어제까지의 주식 **종가** 데이터 테이블 가져오기
        2. Airflow 인스턴스로 가져와서 데이터 갱신 후 인스턴스 data 폴더에 저장
        3. data 폴더에서 두 곳으로 병렬 업로드
            1. AWS S3에 다시 업로드
            2. Django DB(Google Cloud SQL)에서 기존 내용 삭제 후 갱신 된 테이블 COPY
    - 수집한 데이터는 Django 프로젝트 내에서 데이터 처리 후 이동평균선 차트 구현과 매수/매도 신호 구현에 사용
    
- **가격 비교 데이터 수집**
    
    [calc_profit_loss.py](https://github.com/devcourse-final-prj/airflow/blob/main/dags/calc_profit_loss.py)
    
    - 사용한 라이브러리: pykrx
    - 실행시간 장 종료 후 오후 15시 50분
    - 소요시간 : 약 1분 30초 ~ 2분
    - 데이터 수취 (일자 별 가격 조회) 후 구현하려는 로직에 맞는 데이터로 변형
    - 변형된 데이터는 S3에 json file 형태로 저장
        - 변형 후 django에서 대시보드화 할 수 있는 데이터로 변경
        - 해당 페이지 진입 시에 S3 에 있는 데이터로 구현

### [데이터 ETL - Kafka](https://github.com/devcourse-final-prj/kafka_cluster)

- 리소스 제한 한계로 하나의 EC2 인스턴스에 Kafka, Zookeeper 가동
- Zookeeper의 분산 합의 알고리즘 문제로 인스턴스 3대 생성
- 3개의 AZ의 Private Subnet에 위치함
- CPU 사용량 확인 결과 처리량에 문제가 없다고 판단해,
Producer와 Consumer 인스턴스 각 1개씩 구동
- 수집한 데이터는 RDS에 저장 후, Superset에서 사용

### [주가 예측 모델 구현](https://github.com/devcourse-final-prj/stock_pipeline/tree/main/ml)

[daily_stock_price_prediction_to_rds.py](https://github.com/devcourse-final-prj/stock_pipeline/blob/main/ml/daily_stock_price_prediction_to_rds.py)

- 사용한 라이브러리 : pykis, pykrx,TensorFlow
    - pykis : Top5 주가 종목 조회
    - pykrx : Top5 주가 종목에 대한  10년치 데이터
    - TensorFlow : 주식 종가 예측 모델 구현
- 예측 모델에 활용한 데이터
    - 다우 지수, 나스닥 지수, 환율 정보 (10년)
    - 시가, 고가, 저가, 종가, 거래량 데이터 (10년)
- DB : AWS RDS MySQL mlDB.top5_expectation
- 실행 시간
    - 매일 7시 20분 : 어제의 Top5 주가 종목에 대해 오늘의 종가 예측
    - 매일 18시 :  어제의 Top5 주가 종목에 대해 오늘 실제 종가 업데이트
    

### Superset 대시보드 시각화

- AWS 인스턴스를 활용해 Superset 서버 구성
- 실시간 트리맵, 머신러닝 대시보드 구성

### [웹 페이지 개발, 배포](https://github.com/devcourse-final-prj/stock_pipeline/tree/main/web)

- Google Cloud SQL의 postgreSQL을 구성하고 Django 데이터베이스로 연결
- Google Cloud를 이용해 웹 서버 구성, 배포
    - [자세한 웹 인프라 구성, 배포 과정 마크다운 문서](https://github.com/devcourse-final-prj/stock_pipeline/blob/main/web/readme.md)
    - Google Cloud Compute Engine을 이용해 Django 서버 구성
    - Gunicorn, nginx를 이용해 웹사이트 배포
    - Github Workflow를 이용해 Github main branch와 연동, 배포 자동화
- Django 프로젝트에서 웹 페이지 구현
    - 홈페이지와 페이지들에서 공통으로 쓰이는 메뉴바를 위한 **homepage**, **common** 앱 구성
    - Superset 대시보드를 연결하는 페이지 구현을 위해 **superset** 앱 구성
        - 앞서 만든 Superset 대시보드를 해당하는 페이지에 iframe으로 연결
    - Django 데이터베이스(Google Cloud SQL)로 데이터를 받아서 직접 처리하고 시각화하는 페이지 구현을 위해 **viz** 앱 구성
        - views.py에서 데이터를 처리
        - javascript 파일들을 통해 원하는 데이터를 요청하고 views.py의 함수로부터 원하는 데이터를 받아 **이동평균선 차트와 6가지 신호 기능 구현**

## 프로젝트 결과

<img src="https://github.com/eclipse25/eclipse25.github.io/assets/109349939/a3150d45-a079-40f8-9b09-5e3dc6ad395c" width="800" alt="homepage">

![pr-ezgif com-video-to-gif-converter (1)](https://github.com/eclipse25/eclipse25.github.io/assets/109349939/b68e76b4-578f-4b22-9d44-0eb61d820519)
![tm-ezgif com-video-to-gif-converter (1)](https://github.com/eclipse25/eclipse25.github.io/assets/109349939/6c8c5c3d-09fa-440a-8c57-8142181ea3e1)
![moving_average](https://github.com/eclipse25/eclipse25.github.io/assets/109349939/563a632e-f580-431c-a75d-76c39ae2dd50)
![ml-ezgif com-video-to-gif-converter (1)](https://github.com/eclipse25/eclipse25.github.io/assets/109349939/78b45be3-af93-48b7-a46a-d7565b7db647)

- Kafka를 이용해 실시간 데이터를 수집, 처리하여 주식 장이 열려있는 시간 동안 시가총액 상위 순서대로 선정한 주식 종목들의 실시간 데이터를 트리맵으로 나타내고, 트리맵에서 선택한 종목의 실시간 등락률 등의 세부 데이터를 나타내는 대시보드를 구현하였다.
- Airflow와 Django를 이용해 17개 섹터의 5종목씩 총 85종목의 일간 종가 데이터를 수집하고 매일 업데이트 하여, 선택한 종목과, 기간, 이동평균선 기간 2가지를 바탕으로 그래프를 구현하고, 주가 반등, 반락, 골든크로스와 데드크로스, 이동평균선 대비 현재가의 위치 지표를 구현하였다.
- Airflow, 데이터 수집 파이썬 라이브러리와 텐서플로우 등을 이용하여 머신러닝 알고리즘을 적용해 과거 데이터로부터 미래의 주식 가격을 예측하는 모델을 구축하고 결과를 대시보드로 구현하였다.

