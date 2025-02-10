from flask import Blueprint
from src.routes.v1.auth_routes import auth_bp
from src.routes.v1.post_routes import post_bp
from src.routes.v1.comment_routes import comment_bp
from src.routes.v1.school_routes import school_bp
from src.routes.v1.user_routes import user_bp
from src.routes.v1.like_routes import like_bp

def init_routes(app):
    """애플리케이션의 모든 라우트를 등록합니다."""
    
    # API v1 라우트
    
    # 인증 관련 라우트
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    
    # 학교 관련 라우트
    app.register_blueprint(school_bp, url_prefix='/api/v1/countries')
    
    # 게시글 관련 라우트
    app.register_blueprint(post_bp, url_prefix='/api/v1/posts')
    
    # 댓글 관련 라우트
    app.register_blueprint(comment_bp, url_prefix='/api/v1/posts')
    
    # 사용자 관련 라우트
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    
    # 좋아요 관련 라우트
    app.register_blueprint(like_bp, url_prefix='/api/v1/posts')
