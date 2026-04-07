# MariaDB 설정 가이드

## 1. MariaDB 설치 (Mac)

```bash
# Homebrew로 MariaDB 설치
brew install mariadb

# MariaDB 서버 시작
brew services start mariadb

# MariaDB 초기 보안 설정
mysql_secure_installation
```

## 2. 데이터베이스 생성

```bash
# MariaDB 접속
mysql -u root -p

# 데이터베이스 생성
CREATE DATABASE turkey_event_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 사용자 생성 및 권한 부여 (선택사항)
CREATE USER 'turkey_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON turkey_event_db.* TO 'turkey_user'@'localhost';
FLUSH PRIVILEGES;

# 종료
EXIT;
```

## 3. Django 설정 업데이트

`backend/config/settings.py` 파일에서 데이터베이스 설정을 확인하고 수정하세요:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'turkey_event_db',
        'USER': 'root',  # 또는 'turkey_user'
        'PASSWORD': '',  # MariaDB 비밀번호 입력
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

## 4. Python 패키지 설치

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## 5. 마이그레이션 실행

```bash
# 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 실행
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser
```

## 6. 서버 실행

```bash
python manage.py runserver 0.0.0.0:8000
```

## 문제 해결

### mysqlclient 설치 오류 시

Mac에서 mysqlclient 설치 시 오류가 발생하면:

```bash
# pkg-config 설치
brew install pkg-config

# mysql-client 설치
brew install mysql-client

# 환경변수 설정
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
export LDFLAGS="-L/opt/homebrew/opt/mysql-client/lib"
export CPPFLAGS="-I/opt/homebrew/opt/mysql-client/include"

# 다시 설치
pip install mysqlclient
```

### 연결 오류 시

1. MariaDB 서비스 확인:
   ```bash
   brew services list
   ```

2. MariaDB 재시작:
   ```bash
   brew services restart mariadb
   ```

3. 포트 확인:
   ```bash
   mysql -u root -p -e "SHOW VARIABLES LIKE 'port';"
   ```
