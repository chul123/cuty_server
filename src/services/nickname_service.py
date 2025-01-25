from src.models import db
from random import choice, randint
from sqlalchemy.sql.expression import func
from sqlalchemy import or_
from src.models import db, Nickname, Post, PostComment

class NicknameService:
    @staticmethod
    def get_random_nickname():
        """무작위로 닉네임을 선택하여 반환합니다."""
        nickname = db.session.query(Nickname).order_by(func.random()).first()
        return nickname.nickname if nickname else None

    @staticmethod
    def add_nickname(nickname):
        """새로운 닉네임을 추가합니다."""
        try:
            new_nickname = Nickname(nickname=nickname)
            db.session.add(new_nickname)
            db.session.commit()
            return new_nickname
        except Exception as e:
            db.session.rollback()
            raise ValueError('이미 존재하는 닉네임입니다')

    @staticmethod
    def delete_nickname(nickname):
        """기존 닉네임을 삭제합니다."""
        nickname_obj = Nickname.query.filter_by(nickname=nickname).first()
        if not nickname_obj:
            raise ValueError('존재하지 않는 닉네임입니다')
            
        try:
            db.session.delete(nickname_obj)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def get_all_nicknames():
        """모든 닉네임 목록을 반환합니다."""
        return Nickname.query.all()

    @staticmethod
    def create_unique_nickname():
        """고유한 랜덤 닉네임을 생성합니다."""
        # 기본 닉네임 가져오기
        base_nickname = NicknameService.get_random_nickname()
        if not base_nickname:
            return None
            
        # 최대 100번 시도
        for i in range(100):
            # 랜덤 숫자 추가 (1000~9999)
            random_number = randint(1000, 9999)
            nickname = f"{base_nickname}{random_number}"
            
            # 닉네임 중복 체크
            exists = db.session.query(or_(
                Post.query.filter_by(nickname=nickname).exists(),
                PostComment.query.filter_by(nickname=nickname).exists()
            )).scalar()
            
            if not exists:
                return nickname
                
        return None

    @staticmethod
    def get_comment_nickname(user_id, post_id, post_user_id):
        """댓글 작성자의 닉네임을 결정합니다."""
        # 글쓴이인 경우 게시글의 닉네임을 사용
        if user_id == post_user_id:
            post = Post.query.get(post_id)
            return post.nickname if post else None
            
        # 이전에 작성한 댓글이 있는지 확인
        existing_comment = PostComment.query.filter_by(
            user_id=user_id,
            post_id=post_id,
            deleted_at=None
        ).first()
        
        if existing_comment:
            return existing_comment.nickname
            
        # 새로운 닉네임 생성
        return NicknameService.create_unique_nickname() 