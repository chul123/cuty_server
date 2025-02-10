from flask import Blueprint, current_app, request, jsonify
from src.services.post_service import PostService
from src.utils.auth import token_required
import jwt
from src.services.user_service import UserService

post_bp = Blueprint('post', __name__)

@post_bp.route('', methods=['GET'])
def get_posts():
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 필터링 파라미터
    filters = {
        'category': request.args.get('category'),
        'search': request.args.get('search', ''),
        'school_id': request.args.get('school_id', type=int),
        'college_id': request.args.get('college_id', type=int),
        'department_id': request.args.get('department_id', type=int)
    }
    
    # 현재 사용자의 학교 정보와 ID 가져오기
    current_user_school_id = UserService.get_user_school_id(request.headers)
    current_user_id = UserService.get_user_id(request.headers)
    
    try:
        result = PostService.get_posts(page, per_page, current_user_school_id, current_user_id, **filters)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@post_bp.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    # 현재 사용자 정보 가져오기
    user_id = UserService.get_user_id(request.headers)
    
    # IP 주소 가져오기
    ip_address = request.remote_addr
    
    try:
        result = PostService.get_post(post_id, user_id, ip_address)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@post_bp.route('', methods=['POST'])
@token_required
def create_post(current_user):
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['title', 'content', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field}는 필수 항목입니다'}), 400
    
    try:
        result = PostService.create_post(
            current_user,
            data['title'],
            data['content'],
            data['category']
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@post_bp.route('/<int:post_id>', methods=['PUT'])
@token_required
def update_post(current_user, post_id):
    data = request.get_json()
    
    try:
        result = PostService.update_post(post_id, current_user, data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@post_bp.route('/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    try:
        PostService.delete_post(post_id, current_user)
        return '', 204
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
