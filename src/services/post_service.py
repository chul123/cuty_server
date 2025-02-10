from datetime import datetime
from flask import current_app
from sqlalchemy import func, case, distinct, and_, or_
from src.models import (
    db, Post, PostComment, PostLike, PostView,
    School, College, Department, User
)
from src.utils.formatters import (
    get_post_data, get_school_data, get_college_data, 
    get_department_data
)
from src.services.nickname_service import NicknameService

class PostService:
    @staticmethod
    def get_posts(page, per_page, current_user_school_id=None, current_user_id=None, **filters):
        """게시글 목록을 조회합니다."""
        school_id = filters.get('school_id')
        college_id = filters.get('college_id')
        department_id = filters.get('department_id')
        category = filters.get('category')
        search = filters.get('search', '')

        # 학교 ID가 지정되지 않았고 로그인하지 않은 경우 첫 번째 학교 선택
        if not school_id and not current_user_school_id:
            default_school = School.query.first()
            if default_school:
                school_id = default_school.id

        # 게시물 쿼리 생성
        posts_query = db.session.query(
            Post,
            func.count(distinct(PostView.id)).label('view_count'),
            func.count(distinct(case(
                (PostComment.parent_id == None, PostComment.id)
            ))).label('comment_count'),
            func.count(distinct(case((PostLike.type == 'like', PostLike.id)))).label('like_count'),
            func.count(distinct(case((PostLike.type == 'dislike', PostLike.id)))).label('dislike_count'),
            func.count(distinct(case(
                (and_(PostLike.type == 'like', PostLike.user_id == current_user_id), PostLike.id)
            ))).label('user_like_status'),
            func.count(distinct(case(
                (and_(PostLike.type == 'dislike', PostLike.user_id == current_user_id), PostLike.id)
            ))).label('user_dislike_status')
        ).outerjoin(PostView, Post.id == PostView.post_id)\
        .outerjoin(PostComment, Post.id == PostComment.post_id)\
        .outerjoin(PostLike, Post.id == PostLike.post_id)\
        .filter(Post.deleted_at == None)

        # 필터 적용
        if school_id:
            posts_query = posts_query.filter(Post.school_id == school_id)
        elif current_user_school_id:
            posts_query = posts_query.filter(Post.school_id == current_user_school_id)

        if college_id:
            posts_query = posts_query.filter(Post.college_id == college_id)

        if department_id:
            posts_query = posts_query.filter(Post.department_id == department_id)

        if category:
            posts_query = posts_query.filter(Post.category == category)

        if search:
            search_filter = or_(
                Post.title.ilike(f'%{search}%'),
                Post.content.ilike(f'%{search}%'),
            )
            posts_query = posts_query.filter(search_filter)

        # 정렬 및 그룹화
        posts_query = posts_query.group_by(Post.id)\
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

        # 현재 적용된 필터의 학교/단과대/학과 정보 가져오기
        current_school = None
        current_college = None
        current_department = None

        if school_id:
            current_school = School.query.get(school_id)
        elif current_user_school_id:
            current_school = School.query.get(current_user_school_id)

        if college_id and current_school:
            current_college = College.query.filter_by(id=college_id, school_id=current_school.id).first()

        if department_id and current_college:
            current_department = Department.query.filter_by(id=department_id, college_id=current_college.id).first()

        return {
            'posts': posts,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'current_filters': {
                'school': get_school_data(current_school) if current_school else None,
                'college': get_college_data(current_college) if current_college else None,
                'department': get_department_data(current_department) if current_department else None,
                'category': category,
                'search': search
            }
        }

    @staticmethod
    def get_post(post_id, user_id=None, ip_address=None):
        """특정 게시글을 조회합니다."""
        post_query = db.session.query(
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

        if not post_query:
            raise ValueError('존재하지 않는 게시글입니다')

        post, view_count, comment_count, like_count, dislike_count, user_like_status, user_dislike_status = post_query

        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')

        # 조회수 증가 로직
        existing_view = PostView.query.filter(
            PostView.post_id == post_id,
            or_(
                and_(PostView.user_id == user_id, PostView.user_id != None),
                and_(PostView.ip_address == ip_address, PostView.user_id == None)
            )
        ).first()

        if not existing_view:
            new_view = PostView(
                post_id=post_id,
                user_id=user_id,
                ip_address=ip_address if not user_id else None
            )
            db.session.add(new_view)
            db.session.commit()
            view_count += 1

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
    def create_post(user, title, content, category):
        """새 게시글을 생성합니다."""
        # 랜덤 닉네임 생성
        anonymous_nickname = NicknameService.create_unique_nickname()
        if not anonymous_nickname:
            raise ValueError('닉네임을 생성할 수 없습니다')

        new_post = Post(
            title=title,
            content=content,
            category=category,
            user_id=user.id,
            nickname=anonymous_nickname,
            school_id=user.school_id,
            college_id=user.college_id,
            department_id=user.department_id
        )

        try:
            db.session.add(new_post)
            db.session.commit()
            return get_post_data(new_post, 0, 0, 0, 0, False, False)
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_post(post_id, user, data):
        """게시글을 수정합니다."""
        post = Post.query.get(post_id)

        if not post:
            raise ValueError('존재하지 않는 게시글입니다')

        if post.deleted_at:
            raise ValueError('삭제된 게시글입니다')

        if post.user_id != user.id:
            raise ValueError('게시글을 수정할 권한이 없습니다')

        # 수정 가능한 필드 확인
        updatable_fields = ['title', 'content', 'category']
        for field in updatable_fields:
            if field in data:
                setattr(post, field, data[field])

        try:
            db.session.commit()

            post_data = db.session.query(
                Post,
                func.count(distinct(PostView.id)).label('view_count'),
                func.count(distinct(case(
                    (PostComment.parent_id == None, PostComment.id)
                ))).label('comment_count'),
                func.count(distinct(case((PostLike.type == 'like', PostLike.id)))).label('like_count'),
                func.count(distinct(case((PostLike.type == 'dislike', PostLike.id)))).label('dislike_count'),
                func.count(distinct(case(
                    (and_(PostLike.type == 'like', PostLike.user_id == user.id), PostLike.id)
                ))).label('user_like_status'),
                func.count(distinct(case(
                    (and_(PostLike.type == 'dislike', PostLike.user_id == user.id), PostLike.id)
                ))).label('user_dislike_status')
            ).outerjoin(PostView, Post.id == PostView.post_id)\
            .outerjoin(PostComment, Post.id == PostComment.post_id)\
            .outerjoin(PostLike, Post.id == PostLike.post_id)\
            .filter(Post.id == post_id)\
            .group_by(Post.id)\
            .first()

            post, view_count, comment_count, like_count, dislike_count, user_like_status, user_dislike_status = post_data
            return get_post_data(
                post, 
                view_count, 
                comment_count, 
                like_count, 
                dislike_count,
                bool(user_like_status),
                bool(user_dislike_status)
            )

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_post(post_id, user):
        """게시글을 삭제합니다."""
        post = Post.query.get(post_id)

        if not post:
            raise ValueError('존재하지 않는 게시글입니다')

        if post.deleted_at:
            raise ValueError('이미 삭제된 게시글입니다')

        if post.user_id != user.id:
            raise ValueError('게시글을 삭제할 권한이 없습니다')

        try:
            post.deleted_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
