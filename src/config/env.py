import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(f'.env.{os.getenv("FLASK_ENV", "local")}')

# 데이터베이스 설정
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME')

# 보안 설정
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

# 서버 설정
FLASK_ENV = os.getenv('FLASK_ENV', 'local')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
