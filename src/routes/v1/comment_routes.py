from flask import Blueprint, request, jsonify
from src.services.comment_service import CommentService
from src.utils.auth import token_required
from flask import current_app

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        result = CommentService.get_comments(post_id, page, per_page)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comment_bp.route('/<int:post_id>/comments', methods=['POST'])
@token_required
def create_comment(current_user, post_id):
    data = request.get_json()
    
    if 'content' not in data:
        return jsonify({'error': 'content는 필수 항목입니다'}), 400
    
    try:
        result = CommentService.create_comment(
            current_user,
            post_id,
            data['content'],
            data.get('parent_id')
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comment_bp.route('/<int:post_id>/comments/<int:comment_id>', methods=['PUT'])
@token_required
def update_comment(current_user, post_id, comment_id):
    data = request.get_json()
    
    if 'content' not in data:
        return jsonify({'error': 'content는 필수 항목입니다'}), 400
    
    try:
        result = CommentService.update_comment(
            current_user,
            post_id,
            comment_id,
            data['content']
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comment_bp.route('/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, post_id, comment_id):
    try:
        CommentService.delete_comment(current_user, post_id, comment_id)
        return '', 204
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@comment_bp.route('/<int:post_id>/comments/<int:comment_id>/replies', methods=['GET'])
def get_comment_replies(post_id, comment_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        current_app.logger.debug(f"Fetching replies for post_id: {post_id}, comment_id: {comment_id}")
        result = CommentService.get_replies(post_id, comment_id, page, per_page)
        return jsonify(result), 200
    except ValueError as e:
        current_app.logger.error(f"ValueError in get_comment_replies: {str(e)}")
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_comment_replies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@comment_bp.route('/<int:post_id>/comments/<int:comment_id>', methods=['GET'])
def get_comment(post_id, comment_id):
    try:
        result = CommentService.get_comment(post_id, comment_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404 if '존재하지 않는' in str(e) else 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
