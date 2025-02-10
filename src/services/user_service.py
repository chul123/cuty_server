from flask import current_app
import jwt
from src.models import User, Post, PostComment, PostView, PostLike
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db
from sqlalchemy import func, case, distinct, and_
from src.utils.formatters import get_post_data, get_comment_data

class UserService:
    @staticmethod
    def get_user_from_token(token):
        """토큰으로부터 사용자 정보를 조회합니다."""
        try:
            token = token.split(" ")[1]  # "Bearer " 제거
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user = User.query.get(data['user_id'])
            if user and not user.is_deleted:
                return user
            return None
        except:
            return None

    @staticmethod
    def get_user_school_id(headers):
        """요청 헤더에서 사용자의 학교 ID를 조회합니다."""
        if 'Authorization' not in headers:
            return None
            
        user = UserService.get_user_from_token(headers['Authorization'])
        return user.school_id if user else None

    @staticmethod
    def get_user_id(headers):
        """Authorization 헤더에서 사용자 ID를 추출합니다."""
        try:
            if 'Authorization' in headers:
                token = headers['Authorization'].split(" ")[1]
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                return data['user_id']
        except:
            pass
        return None

    @staticmethod
    def validate_password(password):
        # """비밀번호 유효성을 검사합니다."""
        # if len(password) < 8:
        #     raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        
        # if not any(c.isupper() for c in password):
        #     raise ValueError('비밀번호는 최소 1개의 대문자를 포함해야 합니다')
            
        # if not any(c.islower() for c in password):
        #     raise ValueError('비밀번호는 최소 1개의 소문자를 포함해야 합니다')
            
        # if not any(c.isdigit() for c in password):
        #     raise ValueError('비밀번호는 최소 1개의 숫자를 포함해야 합니다')
            
        # if not any(c in '!@#$%^&*()' for c in password):
        #     raise ValueError('비밀번호는 최소 1개의 특수문자(!@#$%^&*())를 포함해야 합니다')
        pass

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """사용자의 비밀번호를 변경합니다."""
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError('존재하지 않는 사용자입니다')
            
        if user.is_deleted:
            raise ValueError('삭제된 사용자입니다')
            
        if not check_password_hash(user.password, current_password):
            raise ValueError('현재 비밀번호가 일치하지 않습니다')
            
        # 새 비밀번호 유효성 검사
        UserService.validate_password(new_password)
        
        # 현재 비밀번호와 동일한지 확인
        if check_password_hash(user.password, new_password):
            raise ValueError('새 비밀번호는 현재 비밀번호와 달라야 합니다')
            
        # 비밀번호 변경
        user.password = generate_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            current_app.logger.info(f'User {user_id} changed password successfully')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Failed to change password for user {user_id}: {str(e)}')
            raise ValueError('비밀번호 변경 중 오류가 발생했습니다')

    @staticmethod
    def delete_account(user_id):
        """사용자 계정을 삭제합니다."""
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError('존재하지 않는 사용자입니다')
            
        if user.is_deleted:
            raise ValueError('이미 삭제된 사용자입니다')
            
        try:
            # 이메일 앞에 "deleted:" 접두어 추가
            user.email = f"deleted:{user.email}"
            user.deleted_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_user_posts(user_id, page, per_page):
        """사용자가 작성한 게시글 목록을 조회합니다."""
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError('존재하지 않는 사용자입니다')
            
        if user.is_deleted:
            raise ValueError('삭제된 사용자입니다')
            
        posts = user.posts.filter_by(deleted_at=None)\
            .order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
            
        return posts

    @staticmethod
    def get_user_comments(user_id, page, per_page):
        """사용자가 작성한 댓글 목록을 조회합니다."""
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError('존재하지 않는 사용자입니다')
            
        if user.is_deleted:
            raise ValueError('삭제된 사용자입니다')
            
        comments = user.post_comments.filter_by(deleted_at=None)\
            .order_by(PostComment.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
            
        return comments

    @staticmethod
    def get_my_posts(user_id, page, per_page):
        """사용자가 작성한 게시글 목록을 조회합니다."""
        # 사용자 존재 여부 확인
        user = User.query.get(user_id)
        if not user:
            raise ValueError('존재하지 않는 사용자입니다')
        
        if user.is_deleted:
            raise ValueError('삭제된 사용자입니다')
        
        # 게시글 쿼리 생성
        posts_query = db.session.query(
            Post,
            func.count(distinct(PostView.id)).label('view_count'),
            func.count(distinct(case(
                (PostComment.parent_id == None, PostComment.id)
            ))).label('comment_count'),
            func.count(distinct(case((PostLike.type == 'like', PostLike.id)))).label('like_count'),
            func.count(distinct(case((PostLike.type == 'dislike', PostLike.id)))).label('dislike_count'),
            func.count(distinct(case(
                (and_(PostLike.type == 'like', PostLike.user_id == user_id), PostLike.id)
            ))).label('user_like_status'),
            func.count(distinct(case(
                (and_(PostLike.type == 'dislike', PostLike.user_id == user_id), PostLike.id)
            ))).label('user_dislike_status')
        ).outerjoin(PostView, Post.id == PostView.post_id)\
        .outerjoin(PostComment, Post.id == PostComment.post_id)\
        .outerjoin(PostLike, Post.id == PostLike.post_id)\
        .filter(Post.user_id == user_id)\
        .filter(Post.deleted_at == None)\
        .group_by(Post.id)\
        .order_by(Post.created_at.desc())
        
        # 페이지네이션 적용
        pagination = posts_query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 결과 포맷팅
        posts = [
            get_post_data(
                post, 
                view_count, 
                comment_count, 
                like_count, 
                dislike_count,
                bool(user_like_status),
                bool(user_dislike_status)
            )
            for post, view_count, comment_count, like_count, dislike_count, user_like_status, user_dislike_status 
            in pagination.items
        ]
        
        return {
            'posts': posts,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }

    @staticmethod
    def get_my_comments(user_id, page, per_page):
        """사용자가 작성한 댓글 목록을 조회합니다."""
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError('존재하지 않는 사용자입니다')
            
        if user.is_deleted:
            raise ValueError('삭제된 사용자입니다')
            
        # 댓글 쿼리 생성
        comments_query = db.session.query(
            PostComment,
            func.count(distinct(PostComment.replies)).label('reply_count')
        ).select_from(PostComment)\
        .filter(
            PostComment.user_id == user_id,
            PostComment.deleted_at == None  # 삭제되지 않은 댓글만 조회
        ).group_by(
            PostComment.id
        ).order_by(PostComment.created_at.desc())
        
        # 페이지네이션 적용
        pagination = comments_query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 결과 포맷팅
        comments = [
            get_comment_data(comment, reply_count)
            for comment, reply_count in pagination.items
        ]
        
        return {
            'comments': comments,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
