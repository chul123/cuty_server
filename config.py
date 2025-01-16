import os
from dotenv import load_dotenv

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def get_database_url(env_file):
        load_dotenv(env_file)
        
        DB_USERNAME = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '5432')
        DB_NAME = os.getenv('DB_NAME')
        
        if DB_USERNAME and DB_PASSWORD:
            SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        else:
            SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
            
        return SQLALCHEMY_DATABASE_URL

class LocalConfig(Config):
    SQLALCHEMY_DATABASE_URI = Config.get_database_url('.env.local')

class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = Config.get_database_url('.env.prod')

config = {
    'local': LocalConfig,
    'prod': ProdConfig,
    'default': LocalConfig
} 