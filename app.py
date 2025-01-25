from flask import Flask
from flask_migrate import Migrate
import logging
from src.models import (
    db
)

from src.routes import init_routes
from src.config.env import (
    SECRET_KEY,
    FLASK_ENV,
    DEBUG
)
from src.config.database import DatabaseConfig


def create_app(config_name='local'):
    app = Flask(__name__)
    app.config.from_object(DatabaseConfig())
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DEBUG'] = DEBUG
    
    # 로깅 설정
    if DEBUG:
        app.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    
    db.init_app(app)
    Migrate(app, db)
    
    # 라우트 등록
    init_routes(app)
    
    return app

app = create_app(FLASK_ENV)

if __name__ == '__main__':
    app.run()
