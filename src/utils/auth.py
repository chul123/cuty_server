from functools import wraps
from flask import request, jsonify
import jwt
from src.models import User

from src.config.env import (
    SECRET_KEY
)


# JWT 토큰 검증을 위한 데코레이터
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': '유효하지 않은 토큰 형식입니다'}), 401

        if not token:
            return jsonify({'error': '토큰이 필요합니다'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            # 유저가 존재하지 않거나 삭제된 경우 확인
            if not current_user:
                return jsonify({'error': '존재하지 않는 사용자입니다'}), 401
            
            if current_user.is_deleted:
                return jsonify({'error': '삭제된 사용자입니다'}), 401
                
        except:
            return jsonify({'error': '유효하지 않은 토큰입니다'}), 401

        return f(current_user, *args, **kwargs)

    return decorated