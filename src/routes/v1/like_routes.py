from flask import Blueprint, jsonify
from src.services.like_service import LikeService
from src.utils.auth import token_required

like_bp = Blueprint('like', __name__)

@like_bp.route('/<int:post_id>/like', methods=['POST'])
@token_required
def like_post(current_user, post_id):
    try:
        result = LikeService.like_post(current_user, post_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@like_bp.route('/<int:post_id>/dislike', methods=['POST'])
@token_required
def dislike_post(current_user, post_id):
    try:
        result = LikeService.dislike_post(current_user, post_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@like_bp.route('/<int:post_id>/unlike', methods=['POST'])
@token_required
def unlike_post(current_user, post_id):
    try:
        result = LikeService.unlike_post(current_user, post_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@like_bp.route('/<int:post_id>/undislike', methods=['POST'])
@token_required
def undislike_post(current_user, post_id):
    try:
        result = LikeService.undislike_post(current_user, post_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
