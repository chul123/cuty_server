from src.config.env import (
    DB_USERNAME,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME
)

class DatabaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    def __init__(self):
        if DB_USERNAME and DB_PASSWORD:
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        else:
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

    @staticmethod
    def get_database_url():
        """데이터베이스 URL을 생성합니다."""
        if not DB_NAME:
            raise ValueError("DB_NAME은 필수 환경 변수입니다")
            
        if DB_USERNAME and DB_PASSWORD:
            return f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        return f"postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SQLALCHEMY_DATABASE_URI = get_database_url() 