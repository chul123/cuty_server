from flask import Blueprint, request, jsonify
from src.services.user_service import UserService
from src.utils.auth import token_required
from src.utils.formatters import get_current_user_data

user_bp = Blueprint('user', __name__)

@user_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    try:
        return jsonify(get_current_user_data(current_user)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/me', methods=['DELETE'])
@token_required
def delete_account(current_user):
    try:
        UserService.delete_account(current_user.id)
        return '', 204
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/me/password', methods=['PUT'])
@token_required
def change_password(current_user):
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['current_password', 'new_password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field}는 필수 항목입니다'}), 400
    
    try:
        UserService.change_password(
            current_user.id,
            data['current_password'],
            data['new_password']
        )
        return '', 204
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@user_bp.route('/me/posts', methods=['GET'])
@token_required
def get_my_posts(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        result = UserService.get_my_posts(current_user.id, page, per_page)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/me/comments', methods=['GET'])
@token_required
def get_my_comments(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        result = UserService.get_my_comments(current_user.id, page, per_page)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

