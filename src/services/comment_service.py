from datetime import datetime
from flask import current_app
import logging
from sqlalchemy import func, distinct, and_
from src.models import db, Post, PostComment, User
from src.services.nickname_service import NicknameService
from src.utils.formatters import get_comment_data

class CommentService:
    
    @staticmethod
    def get_comments(post_id, page, per_page):
        try:
            # 게시글 존재 여부 확인
            post = Post.query.get(post_id)
            if not post:
                raise ValueError('존재하지 않는 게시글입니다')
                
            if post.deleted_at:
                raise ValueError('삭제된 게시글입니다')
            
            # 대댓글 수를 계산하는 서브쿼리
            reply_count_subquery = db.session.query(
                PostComment.parent_id,
                func.count('*').label('reply_count')
            ).filter(
                PostComment.parent_id.isnot(None)
            ).group_by(PostComment.parent_id).subquery()
            
            # 최상위 댓글 쿼리
            comments_query = db.session.query(
                PostComment,
                func.coalesce(reply_count_subquery.c.reply_count, 0).label('reply_count')
            ).outerjoin(
                reply_count_subquery,
                PostComment.id == reply_count_subquery.c.parent_id
            ).filter(
                PostComment.post_id == post_id,
                PostComment.parent_id.is_(None)  # 최상위 댓글만
            ).order_by(PostComment.created_at.desc())
            
            # SQL 쿼리 로깅
            current_app.logger.debug(f"Generated SQL Query: {str(comments_query)}")
            
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
            
        except Exception as e:
            current_app.logger.error(f"Error in get_comments: {str(e)}")
            raise

    @staticmethod
    def get_comment(post_id, comment_id):
        # 게시글 존재 여부 확인
        post = Post.query.get(post_id)
        if not post:
            raise ValueError('존재하지 않는 게시글입니다')
            
        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')
        
        # 댓글 존재 여부 확인
        comment = PostComment.query.get(comment_id)
        if not comment:
            raise ValueError('존재하지 않는 댓글입니다')
            
        if comment.post_id != post_id:
            raise ValueError('해당 게시글의 댓글이 아닙니다')
        
        return get_comment_data(comment, 0)  # reply_count는 필요 없으므로 0으로 전달
    
    @staticmethod
    def get_replies(post_id, comment_id, page, per_page):
        try:
            # 디버그 로깅 추가
            current_app.logger.debug(f"Starting get_replies for post_id: {post_id}, comment_id: {comment_id}")
            
            # 게시글 존재 여부 확인
            post = Post.query.get(post_id)
            if not post:
                raise ValueError('존재하지 않는 게시글입니다')
                
            if post.deleted_at:
                raise ValueError('삭제된 게시글입니다')
            
            # 댓글 존재 여부 확인
            comment = PostComment.query.get(comment_id)
            if not comment:
                raise ValueError('존재하지 않는 댓글입니다')
                
            if comment.post_id != post_id:
                raise ValueError('해당 게시글의 댓글이 아닙니다')
                
            if comment.parent_id is not None:
                raise ValueError('대댓글입니다')
            
            # SQL 쿼리 로깅
            current_app.logger.debug("Executing replies query")
            
            # 대댓글 쿼리
            replies_query = PostComment.query.filter(
                PostComment.parent_id == comment_id
            ).order_by(PostComment.created_at.desc())
            
            # 페이지네이션 적용
            pagination = replies_query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 결과 포맷팅
            replies = [
                get_comment_data(reply, 0)  # 대댓글에는 reply_count가 항상 0
                for reply in pagination.items
            ]

            return {
                'replies': replies,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
            
        except Exception as e:
            # 예외 로깅 추가
            current_app.logger.error(f"Error in get_replies: {str(e)}")
            raise

    @staticmethod
    def create_comment(current_user, post_id, content, parent_id=None):
        # 게시글 존재 여부 확인
        post = Post.query.get(post_id)
        if not post:
            raise ValueError('존재하지 않는 게시글입니다')
            
        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')
        
        # parent_id가 있는 경우 부모 댓글 확인
        if parent_id:
            parent_comment = PostComment.query.get(parent_id)
            if not parent_comment:
                raise ValueError('존재하지 않는 부모 댓글입니다')
            if parent_comment.post_id != post_id:
                raise ValueError('해당 게시글의 댓글이 아닙니다')
            if parent_comment.parent_id is not None:
                raise ValueError('대댓글에는 답글을 달 수 없습니다')
        
        # 자신의 학교의 게시글인지 확인
        if current_user.school_id != post.school_id:
            raise ValueError('자신의 학교의 게시글에만 댓글을 작성할 수 있습니다')
        
        # 랜덤 닉네임 생성
        nickname = NicknameService.get_comment_nickname(current_user.id, post_id, post.user_id)
        if not nickname:
            raise ValueError('닉네임을 생성할 수 없습니다')
        
        # 새 댓글 생성
        new_comment = PostComment(
            content=content,
            user_id=current_user.id,
            post_id=post_id,
            parent_id=parent_id,
            nickname=nickname
        )
        
        db.session.add(new_comment)
        db.session.commit()
        
        # 대댓글 수 조회
        reply_count = 0
        if parent_id is None:  # 최상위 댓글인 경우에만
            reply_count = PostComment.query.filter_by(parent_id=new_comment.id).count()
        
        return get_comment_data(new_comment, reply_count)

    @staticmethod
    def update_comment(current_user, post_id, comment_id, content):
        # 댓글 존재 여부 확인
        comment = PostComment.query.get(comment_id)
        if not comment:
            raise ValueError('존재하지 않는 댓글입니다')
            
        # 게시글 일치 여부 확인
        if comment.post_id != post_id:
            raise ValueError('해당 게시글의 댓글이 아닙니다')
            
        # 권한 확인
        if comment.user_id != current_user.id:
            raise ValueError('댓글을 수정할 권한이 없습니다')
            
        # 삭제된 댓글 확인
        if comment.deleted_at:
            raise ValueError('삭제된 댓글입니다')
        
        comment.content = content
        db.session.commit()
        
        # 대댓글 수 조회
        reply_count = 0
        if comment.parent_id is None:  # 최상위 댓글인 경우에만
            reply_count = PostComment.query.filter_by(parent_id=comment.id).count()
        
        return get_comment_data(comment, reply_count)

    @staticmethod
    def delete_comment(current_user, post_id, comment_id):
        comment = PostComment.query.get(comment_id)
        
        if not comment:
            raise ValueError('존재하지 않는 댓글입니다')
            
        if comment.post_id != post_id:
            raise ValueError('해당 게시글의 댓글이 아닙니다')
            
        if comment.user_id != current_user.id:
            raise ValueError('댓글을 삭제할 권한이 없습니다')
            
        if comment.deleted_at:
            raise ValueError('이미 삭제된 댓글입니다')
        
        comment.deleted_at = datetime.utcnow()
        db.session.commit()

    
