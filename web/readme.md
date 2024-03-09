# Django 웹페이지 개발

## 로컬 환경

프레임워크 : Django / nginx

개발환경 : Windows

디렉토리 : stock_pipeline\web


### 환경 설정

```bash
# 가상환경 생성(윈도우)
python -m venv stock_django_env

# 가상환경 활성화(윈도우)
stock_django_env\Scripts\activate.bat

# 가상환경 비활성화(윈도우)
deactivate

# Django 설치(윈도우)
python -m pip install Django
# Successfully installed Django-5.0.2 asgiref-3.7.2 sqlparse-0.4.4 tzdata-2024.1

# 설치 버전 체크
django-admin --version
# 5.0.2

# 장고 프로젝트 루트 디렉토리에서 가상환경 생성 후 requirements.txt 설치
cd stock_data_flow
pip install -r requirements.txt

```

### 앱 생성

```bash
# 루트 디렉토리에서 실행
python manage.py startapp homepage
```

### .env (로컬에 없으면 로컬에서 실행 불가)

- Django 프로젝트의 다음 변수들은 현재 깃허브에서 숨긴 상태
- manage.py가 있는 루트 디렉토리에 .env 파일을 만들고 다음을 입력 후 저장

```python
SECRET_KEY='...'
DATABASE_USER='...'
DATABASE_PASSWORD='...'
DATABASE_HOST='...'
```

### 프로젝트 생성/실행

```bash
# Django 프로젝트 생성
django-admin startproject stock_data_flow

# 생성한 프로젝트를 서버에서 실행(윈도우)
cd stock_data_flow
python manage.py runserver
```

### ★ 주의사항

- web/stock_data_flow/stock_data_flow/settings.py
    - git pull 받은 후 settings.py에서 꼭 Debug 옵션을 True로 바꿔주어야 로컬에서 테스트 가능
    - 로컬에서 push할 때 Debug=False로 변경 후 push 혹은 settings.py는 제외하고 커밋할 것

## 데이터베이스 - GCP Google Cloud SQL

```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': '5432',  # 기본 포트
    }
}

# 의존성 추가: psycopg2 패키지는 Django가 Postgres와 통신하기 위해 필요
# 이를 위해 pip install psycopg2 명령어를 사용하여 설치하고, requirements.txt 파일에 추가

# 데이터베이스 마이그레이션: python manage.py migrate 명령어를 실행
# Django 모델을 Postgres 데이터베이스에 마이그레이션

# 로컬 테스트: 모든 변경 사항이 정상적으로 작동하는지 로컬 환경에서 테스트
```

- viz - 이동평균선(graph) 페이지 `DailyStockPrice` 모델 정의
    
    ```python
    from django.db import models
    
    class DailyStockPrice(models.Model):
        sector_name = models.CharField(max_length=100, verbose_name="부문")
        stock_code = models.CharField(max_length=10, verbose_name="주식 코드")
        kr_stock_name = models.CharField(max_length=100, verbose_name="회사 이름")
        date_column = models.DateField(verbose_name="날짜")
        closing_price = models.IntegerField(verbose_name="종가")
    
        def __str__(self):
            return f"[{self.sector_name}] {self.kr_stock_name}({self.stock_code}) - {self.date_column}: {self.closing_price}"
    
        class Meta:
            verbose_name = "주식 일간 종가"
            verbose_name_plural = "주식 일간 종가들"
    ```
    
- **데이터베이스 마이그레이션**
    
    모델을 정의한 후, 모델을 데이터베이스 스키마에 반영하기 위해 마이그레이션을 생성하고 적용
    
    - 마이그레이션 파일 생성:
        
        ```bash
        python manage.py makemigrations
        ```
        
    - 마이그레이션 적용:
        
        ```bash
        python manage.py migrate
        ```
        
    
    이 과정을 통해 모델에 해당하는 데이터베이스 테이블 생성
    

## GCP + Django + nginx + Gunicorn 배포
![Architecture](https://blog.kakaocdn.net/dn/c9ZwjC/btrlDwyPuvc/dxX8OhYkRl18DnQiGaMn8k/img.png)

### GCP

- Compute Engine에서 VM 인스턴스 생성(Ubuntu 서버)
- VPC 네트워크 설정
    - 방화벽 규칙 만들기
    - IP 주소 - 고정 주소 예약 - static01, IPv4

- 서버 접속(VM SSH)
    
    - `sudo apt-get update && sudo apt-get dist-upgrade`  패키지 업데이트
    - `sudo apt install python3-pip`  pip 설치
    - git clone https://github_pat_...:x-oauth-basic@github.com/devcourse-final-prj/stock_pipeline.git
- 가상환경 설정(VM SSH)
    - `sudo apt install python3-venv`  # python3-venv 패키지가 없다면 설치
    - `python3 -m venv myenv`  # 'myenv'는 가상 환경의 이름
    - `source myenv/bin/activate`  # 가상 환경 활성화
    - 가상환경 위치 - /home/.../myenv
- 의존성 설치
    - `cd web/stock_data_flow/`
    - `pip install -r requirements.txt`  # requirements.txt 파일에 명시된 패키지 설치
        - PostgreSQL 개발 파일 설치
            - psycopg2를 빌드하기 위해 필요한 PostgreSQL 개발 헤더 및 라이브러리를 설치
                - `sudo apt-get install libpq-dev`
            - psycopg2를 빌드하기 위해 필요한 PostgreSQL 개발 파일들을 설치
                - `sudo apt-get install python3-dev`
            - 다시 `pip install -r requirements.txt` 실행하여 완료
- Gunicorn 설치
    - `cd ~/stock_pipeline`
    - `pip install gunicorn`  # Gunicorn WSGI 서버 설치
- Django 애플리케이션 실행 테스트
    - `cd web/stock_data_flow`
    - `python [manage.py](http://manage.py/) runserver 0.0.0.0:8000`  # Gunicorn으로 전환하기 전에 테스트
    - [**http://34.64.83.141:8000/**](http://34.64.83.141:8000/)
    - Gunicorn으로 Django 실행
        - `gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application`
- Systemd 서비스 파일 생성
    - Gunicorn을 systemd 서비스로 구성해서 서버 부팅 시 자동으로 Gunicorn이 시작되도록 하고, 필요시 쉽게 시작/정지를 관리할 수 있도록 한다.
    - `cd /etc/systemd/system/`
    - `sudo nano gunicorn.service`
        
        ```python
        [Unit]
        Description=gunicorn daemon
        After=network.target
        
        [Service]
        User=ubuntu
        Group=www-data
        WorkingDirectory=/home/.../stock_pipeline/web/stock_data_flow
        EnvironmentFile=/home/.../stock_pipeline/web/stock_data_flow/.env
        ExecStart=/home/.../myenv/bin/gunicorn \
                --workers 3 --bind 0.0.0.0:8000 stock_data_flow.wsgi:application
        
        [Install]
        WantedBy=multi-user.target
        ```
        
    - ctrl O로 저장, enter, ctrl X로 nano 종료
- Gunicorn 서비스를 활성화
    - Gunicorn이 TCP 포트 **`0.0.0.0:8000`**에서 리스닝하며, **`stock_data_flow`** Django 프로젝트를 서빙할 준비 완료
        
        ```powershell
        sudo systemctl daemon-reload  # systemd 데몬 리로드
        sudo systemctl start gunicorn.service  # gunicorn 서비스 시작
        sudo systemctl enable gunicorn.service  # 부팅 시 gunicorn 서비스 자동 시작 활성화
        sudo systemctl status gunicorn.service  # gunicorn 서비스 상태 확인
        ```
        
    - ubuntu 사용자 권한 설정
        - `sudo chmod -R +x /home/...`
        - `sudo chown -R ubuntu:www-data /home/.../stock_pipeline`
- Nginx 설치
    - `sudo apt install nginx`
- Nginx 설정:
    - Nginx를 통해 Gunicorn 서버를 프록시로 설정하고, 정적 및 미디어 파일을 제공하기 위한 설정을 추가
    - `cd /`
    - `cd /etc/nginx/sites-available`
    - `sudo nano stock_data_flow`
        
        ```powershell
        server {
            listen 80;
            server_name 34.64.83.141;
        
            location = /favicon.ico { access_log off; log_not_found off; }
            location /static/ {
                alias /var/www/stock_data_flow/static/;
            }
        
            location / {
                include proxy_params;
                proxy_pass http://localhost:8000;
            }
        }
        ```
        
- 심볼릭 링크 연결(sites-available → sites-enabled)
    
    ```powershell
    (myenv) ...@instance-20240226-...:/etc/nginx$ ls -l /etc/nginx/sites-enabled/
    total 0
    lrwxrwxrwx 1 root root 34 Feb 26 15:49 default -> /etc/nginx/sites-available/default
    (myenv) ...@instance-20240226-...:/etc/nginx$ sudo ln -s /etc/nginx/sites-available/stock_data_flow /etc/nginx/sites-enabled/
    (myenv) ...@instance-20240226-...:/etc/nginx$ ls -l /etc/nginx/sites-enabled/
    total 0
    lrwxrwxrwx 1 root root 34 Feb 26 15:49 default -> /etc/nginx/sites-available/default
    lrwxrwxrwx 1 root root 42 Feb 28 05:48 stock_data_flow -> /etc/nginx/sites-available/stock_data_flow
    ```
    
- Django settings.py
    
    - **`/var/www/stock_data_flow`** 디렉토리 (웹서버에서 깃 범위 밖)
    - 권한 허용
    
    ```powershell
    sudo chgrp -R www-data /var/www/stock_data_flow
    sudo chmod -R g+w /var/www/stock_data_flow
    sudo usermod -a -G www-data ...  #이후 SSH 재부팅
    ```
    
    - `python3 manage.py collectstatic`  으로 nginx에서 정적 파일에 접근 가능하도록 설정
- Nginx 구성 파일의 문법이 올바른지 검사
    - `sudo nginx -t`
- Nginx 활성화
    
    ```powershell
    sudo systemctl reload nginx
    sudo systemctl restart nginx
    sudo systemctl status nginx   # 서비스 상태 확인
    ```

- 방화벽 설정:
    - 외부에서 애플리케이션에 접근할 수 있도록 네트워크 설정 조정
    

## 겪은 문제

gunicorn, nginx를 이용해서 호스팅할 때 정적 파일이 연결되지 않는 문제

http://34.64.83.141:8000 에 연결은 되지만 정적파일을 nginx로 받아오지 못하고 있었음

### 환경

- gunicorn.service
    
    ```powershell
    [Unit]
    Description=gunicorn daemon
    After=network.target
    
    [Service]
    User=ubuntu
    Group=www-data
    WorkingDirectory=/home/.../stock_pipeline/web/stock_data_flow
    EnvironmentFile=/home/.../stock_pipeline/web/stock_data_flow/.env
    ExecStart=/home/.../stock_pipeline/myenv/bin/gunicorn \
            --workers 3 --bind 0.0.0.0:8000 stock_data_flow.wsgi:application
    
    [Install]
    WantedBy=multi-user.target
    ```
    
- django - settings.py
    
    ```powershell
    # 정적 파일을 제공할 URL
    STATIC_URL = '/static/'
    
    # collectstatic 명령이 정적 파일을 수집하여 저장할 경로
    STATIC_ROOT = '/var/www/stock_data_flow/static/'
    
    ```
    
    - nginx, gunicorn 없이 실행되는 로컬에서는 정적파일 적용에 문제 없음
- nginx - stock_data_flow(sites-available)
    
    ```powershell
    server {
        listen 80;
        server_name 34.64.83.141;
    
        location = /favicon.ico { access_log off; log_not_found off; }
        location /static/ {
            alias /var/www/stock_data_flow/static/;
        }
    
        location / {
            include proxy_params;
            proxy_pass http://34.64.83.141:8000;
        }
    }
    ```
    

- homepage app의 index.html
    
    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta http-equiv="X-UA-Compatible" content="IE=edge" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      {% load static %}
      <link rel="stylesheet" href="{% static 'homepage/css/style.css' %}" />
      <title>StockSight</title>
    </head>
    <body>
      <h2 id="clock">00:00:00</h2>
      <script src="{% static 'homepage/js/clock.js' %}"></script>
    </body>
    </html>
    ```
    
    - 로컬에서는 잘 돌아감(git으로 debug 옵션 제외 동일하게 설정)
        - http://127.0.0.1:8000/static/homepage/css/style.css - OK
    - http://34.64.83.141:8000/static/homepage/css/style.css  - 404

- VM 내에서 /var/www/stock_data_flow/static/ 내용물
    
    ```powershell
    (myenv) ...@instance-20240226-...:/var/www/stock_data_flow/static$ ls
    admin  homepage
    (myenv) ...@instance-20240226-...:/var/www/stock_data_flow/static$ cd homepage
    (myenv) ...@instance-20240226-...:/var/www/stock_data_flow/static/homepage$ ls
    css  js
    ```
    
- nginx.conf
    
    ```powershell
    user ubuntu;
    worker_processes auto;
    pid /run/nginx.pid;
    include /etc/nginx/modules-enabled/*.conf;
    
    ...
    ```
    
- nginx의 정적 파일 디렉토리의 권한
    
    ```powershell
    (myenv) ...@instance-20240226-...:/$ ls -l /var/www/stock_data_flow/static/
    total 8
    drwxr-xr-x 5 ubuntu www-data 4096 Feb 27 13:06 admin
    drwxr-xr-x 4 ubuntu www-data 4096 Feb 27 13:06 homepage
    ```
    

### 해결

1. `nginx.conf`에서 nginx 설정 파일들을 `/etc/nginx/sites-enabled/` 폴더에서 가져오고 있었는데 `/etc/nginx/sites-available/` 폴더에 설정 파일을 만들어 놓고 `sites-enabled` 폴더와 연결하지 않아서 적용이 되지 않았음
2. 1번을 해결하고 나니 여전히 정적 파일은 연결되지 않았지만 postman에서 테스트 중 http://34.64.83.141/static/homepage/css/style.css 에서 정적 파일이 반환되는 것을 확인함
3. 위의  `/etc/nginx/sites-enabled/stock_data_flow` 설정 파일에서 
    
    ```powershell
    server {
        listen 80;
        server_name 34.64.83.141;
    
        location = /favicon.ico { access_log off; log_not_found off; }
        location /static/ {
            alias /var/www/stock_data_flow/static/;
        }
    
        location / {
            include proxy_params;
            proxy_pass http://34.64.83.141:8000; 
        }
    }
    ```
    
    proxy_pass을 로컬호스트(http://localhost:8000;)로 바꾸었더니 정적 파일이 제대로 연결되었다. 외부에서 오픈 된 주소를 통해 정적 파일을 가져올 때 권한 등 보안 관련 문제가 있었던 것으로 추정된다.
    

## 깃허브 main branch와 sync하는 CD workflow

- 방화벽(default로 설정) - 22번 포트
    
- SSH에서 SSH 키(public-private) 발급
    - `ssh-keygen -t rsa -b ... -C "...@....com"`
        
        ```powershell
        (myenv) ...@instance-20240226-...:~/.ssh$ ssh-keygen -t rsa -b 4096 -C "...@....com"
        Generating public/private rsa key pair.
        Enter file in which to save the key (/home/.../.ssh/id_rsa): 
        Enter passphrase (empty for no passphrase): 
        Enter same passphrase again: 
        Your identification has been saved in /home/.../.ssh/id_rsa
        Your public key has been saved in /home/.../.ssh/id_rsa.pub
        The key fingerprint is:
        
        (myenv) ...@instance-20240226-...:~/.ssh$ cat /home/.../.ssh/id_rsa  
        -----BEGIN OPENSSH PRIVATE KEY-----
        ...
        -----END OPENSSH PRIVATE KEY-----
        
        (myenv) ...@instance-20240226-...:~/.ssh$ cat /home/.../.ssh/id_rsa.pub
        ssh-rsa ...
        ```
        
- VM 인스턴스에 SSH public키 등록
- 깃허브 secret actions에  SSH private키와 여러 비밀 변수들 등록
- 깃허브 액션 작성
    
    ```yaml
    name: Django CD
    
    on:
      push:
        branches: ["main"]
        paths:
          - "web/**"
          - ".github/workflows/**"
      pull_request:
        branches: ["main"]
        paths:
          - "web/**"
          - ".github/workflows/**"
    
      workflow_dispatch:
    
    jobs:
      build:
        runs-on: ubuntu-latest
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          DATABASE_USER: ${{ secrets.DATABASE_USER }}
          DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
          DATABASE_HOST: ${{ secrets.DATABASE_HOST }}
        steps:
          - uses: actions/checkout@v3
          - name: Set up Python 3.12
            uses: actions/setup-python@v3
            with:
              python-version: 3.12
    
          - name: Execute Remote SSH Commands
            uses: appleboy/ssh-action@master
            with:
              host: ${{ secrets.SERVER_IP }}
              username: ${{ secrets.SSH_USER }}
              key: ${{ secrets.SSH_PRIVATE_KEY }}
              port: 22
              script: |
                source myenv/bin/activate || exit 1
                cd stock_pipeline || exit 1
                git pull origin main || exit 1
                cd web/stock_data_flow || exit 1
                python3 manage.py collectstatic --noinput || exit 1
                python3 manage.py migrate || exit 1
                sudo systemctl daemon-reload || exit 1
                sudo systemctl restart gunicorn.service || exit 1
                sudo systemctl reload nginx || exit 1
    
    ```
    
