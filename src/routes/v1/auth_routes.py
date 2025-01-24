from flask import Blueprint, request, jsonify
from src.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['email', 'password', 'name', 'country_id', 'school_id', 'college_id', 'department_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field}는 필수 항목입니다'}), 400
    
    try:
        user = AuthService.register(data)
        access_token = AuthService.create_access_token(user)
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer"
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': '서버 오류가 발생했습니다'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field}는 필수 항목입니다'}), 400
    
    try:
        user = AuthService.login(data['email'], data['password'])
        access_token = AuthService.create_access_token(user)
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer"
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': '서버 오류가 발생했습니다'}), 500
