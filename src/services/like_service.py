from datetime import datetime
from sqlalchemy import func, case, distinct, and_
from src.models import db, Post, PostLike, PostComment, PostView
from src.utils.formatters import get_post_data

class LikeService:
    @staticmethod
    def _get_post_data(post_id, user_id):
        """게시글 데이터를 조회합니다."""
        post_data = db.session.query(
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
        .filter(Post.id == post_id)\
        .group_by(Post.id)\
        .first()

        if not post_data:
            raise ValueError('존재하지 않는 게시글입니다')

        post, view_count, comment_count, like_count, dislike_count, user_like_status, user_dislike_status = post_data
        
        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')
            
        return get_post_data(
            post, 
            view_count, 
            comment_count, 
            like_count, 
            dislike_count,
            bool(user_like_status),
            bool(user_dislike_status)
        )

    @staticmethod
    def like_post(user, post_id):
        """게시글에 좋아요를 추가합니다."""
        # 게시글 존재 여부 확인
        post = Post.query.get(post_id)
        if not post:
            raise ValueError('존재하지 않는 게시글입니다')
            
        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')
            
        # 자신의 학교의 게시글인지 확인
        if user.school_id != post.school_id:
            raise ValueError('자신의 학교의 게시글에만 좋아요를 할 수 있습니다')

        # 기존 좋아요/싫어요 확인
        existing_like = PostLike.query.filter_by(
            user_id=user.id,
            post_id=post_id
        ).first()

        if existing_like:
            if existing_like.type == 'like':
                raise ValueError('이미 좋아요한 게시글입니다')
            # 싫어요를 좋아요로 변경
            existing_like.type = 'like'
            existing_like.updated_at = datetime.utcnow()
        else:
            # 새로운 좋아요 생성
            new_like = PostLike(
                user_id=user.id,
                post_id=post_id,
                type='like'
            )
            db.session.add(new_like)

        try:
            db.session.commit()
            return LikeService._get_post_data(post_id, user.id)
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def unlike_post(user, post_id):
        """게시글의 좋아요를 취소합니다."""
        # 게시글 존재 여부 확인
        post = Post.query.get(post_id)
        if not post:
            raise ValueError('존재하지 않는 게시글입니다')
            
        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')

        # 좋아요 확인
        like = PostLike.query.filter_by(
            user_id=user.id,
            post_id=post_id,
            type='like'
        ).first()

        if not like:
            raise ValueError('좋아요하지 않은 게시글입니다')

        try:
            db.session.delete(like)
            db.session.commit()
            return LikeService._get_post_data(post_id, user.id)
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def dislike_post(user, post_id):
        """게시글에 싫어요를 추가합니다."""
        # 게시글 존재 여부 확인
        post = Post.query.get(post_id)
        if not post:
            raise ValueError('존재하지 않는 게시글입니다')
            
        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')
            
        # 자신의 학교의 게시글인지 확인
        if user.school_id != post.school_id:
            raise ValueError('자신의 학교의 게시글에만 싫어요를 할 수 있습니다')

        # 기존 좋아요/싫어요 확인
        existing_like = PostLike.query.filter_by(
            user_id=user.id,
            post_id=post_id
        ).first()

        if existing_like:
            if existing_like.type == 'dislike':
                raise ValueError('이미 싫어요한 게시글입니다')
            # 좋아요를 싫어요로 변경
            existing_like.type = 'dislike'
            existing_like.updated_at = datetime.utcnow()
        else:
            # 새로운 싫어요 생성
            new_like = PostLike(
                user_id=user.id,
                post_id=post_id,
                type='dislike'
            )
            db.session.add(new_like)

        try:
            db.session.commit()
            return LikeService._get_post_data(post_id, user.id)
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def undislike_post(user, post_id):
        """게시글의 싫어요를 취소합니다."""
        # 게시글 존재 여부 확인
        post = Post.query.get(post_id)
        if not post:
            raise ValueError('존재하지 않는 게시글입니다')
            
        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')

        # 싫어요 확인
        like = PostLike.query.filter_by(
            user_id=user.id,
            post_id=post_id,
            type='dislike'
        ).first()

        if not like:
            raise ValueError('싫어요하지 않은 게시글입니다')

        try:
            db.session.delete(like)
            db.session.commit()
            return LikeService._get_post_data(post_id, user.id)
        except Exception as e:
            db.session.rollback()
            raise e
