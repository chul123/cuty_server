from flask import Flask, request, jsonify
from flask_migrate import Migrate
from models import db, School, College, Department, User, Post, PostComment, PostLike, PostView, Country, Nickname
from config import config
from werkzeug.security import generate_password_hash, check_password_hash
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func, case, distinct, and_, or_
import random

def create_app(config_name='local'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
    
    db.init_app(app)
    Migrate(app, db)
    
    return app

app = create_app(os.getenv('FLASK_ENV', 'local'))


def get_country_data(country):
    return {
        'id': country.id,
        'name': country.name,
        'code': country.code,

    }


def get_school_data(school):
    return {
        'id': school.id,
        'name': school.name,
    
    }

def get_college_data(college):
    return {
        'id': college.id,
        'name': college.name,

    }

def get_department_data(department):
    return {
        'id': department.id,
        'name': department.name,

    }

def get_post_data(post, view_count, comment_count, like_count, dislike_count):
    return {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'category': post.category,
        'author': get_user_data(post.author),
        'school': {
            'id': post.school.id,
            'name': post.school.name
        },
        'college': {
            'id': post.college.id,
            'name': post.college.name
        },
        'department': {
            'id': post.department.id,
            'name': post.department.name
        },
        'view_count': view_count,
        'comment_count': comment_count,
        'like_count': like_count,
        'dislike_count': dislike_count,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat()
    }


def get_comment_data(comment, reply_count):
    return {
        'id': comment.id,
        'content': comment.display_content,
        'author': {
            'id': comment.author.id,
            'nickname': comment.author.display_nickname
        },
        'reply_count': reply_count,
        'is_deleted': comment.is_deleted,
        'created_at': comment.created_at.isoformat(),
        'updated_at': comment.updated_at.isoformat()
    }

def get_user_data(user):
    if user.is_deleted:
        return {
            'id': user.id,
            'email': 'deleted@mail.com',
            'name': 'deleted',
            'country': None,
            'school': None,
            'college': None,
            'department': None,
            'created_at': None,
            'updated_at': None,
            'deleted_at': user.deleted_at.isoformat() if user.deleted_at else None
        }
    
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'country': {
            'id': user.country.id,
            'name': user.country.name,
            'code': user.country.code
        },
        'school': {
            'id': user.school.id,
            'name': user.school.name
        },
        'college': {
            'id': user.college.id,
            'name': user.college.name
        },
        'department': {
            'id': user.department.id,
            'name': user.department.name
        },
        'created_at': user.created_at.isoformat(),
        'updated_at': user.updated_at.isoformat(),
        'deleted_at': user.deleted_at.isoformat() if user.deleted_at else None
    }

def generate_random_nickname():
    """랜덤 닉네임을 생성합니다."""
    # 모든 닉네임 템플릿을 가져옵니다
    nicknames = Nickname.query.all()
    if not nicknames:
        return None
    
    # 랜덤하게 하나를 선택합니다
    base_nickname = random.choice(nicknames).nickname
    
    # 1000부터 9999 사이의 랜덤 숫자를 생성합니다
    random_number = random.randint(1000, 9999)
    
    # 기본 닉네임과 랜덤 숫자를 조합합니다
    return f"{base_nickname}{random_number}"

def is_nickname_available(nickname):
    """닉네임 사용 가능 여부를 확인합니다."""
    return User.query.filter_by(nickname=nickname).first() is None

def create_unique_nickname():
    """유니크한 닉네임을 생성합니다."""
    max_attempts = 10  # 최대 시도 횟수
    
    for _ in range(max_attempts):
        nickname = generate_random_nickname()
        if nickname and is_nickname_available(nickname):
            return nickname
            
    return None  # 모든 시도 실패

# JWT 토큰 검증을 위한 데코레이터
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': '유효하지 않은 토큰 형식입니다'}), 401

        if not token:
            return jsonify({'error': '토큰이 필요합니다'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            # 유저가 존재하지 않거나 삭제된 경우 확인
            if not current_user:
                return jsonify({'error': '존재하지 않는 사용자입니다'}), 401
            
            if current_user.is_deleted:
                return jsonify({'error': '삭제된 사용자입니다'}), 401
                
        except:
            return jsonify({'error': '유효하지 않은 토큰입니다'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/api/countries', methods=['GET'])
def get_countries():
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 검색어 파라미터
    search = request.args.get('search', '')
    
    # 국가 쿼리 생성
    countries_query = Country.query
    
    # 검색어가 있는 경우 필터 적용
    if search:
        countries_query = countries_query.filter(
            or_(
                Country.name.ilike(f'%{search}%'),
                Country.code.ilike(f'%{search}%')
            )
        )
    
    # 정렬 적용
    countries_query = countries_query.order_by(Country.name.asc())
    
    # 페이지네이션 적용
    pagination = countries_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 결과 포맷팅
    countries = [get_country_data(country) for country in pagination.items]
    
    return jsonify({
        'countries': countries,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'search': search
    }), 200

@app.route('/api/countries/<int:country_id>/schools', methods=['GET'])
def get_schools_by_country(country_id):
    # 국가 존재 여부 확인
    country = Country.query.get(country_id)
    if not country:
        return jsonify({'error': '존재하지 않는 국가입니다'}), 404
    
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    # 학교 쿼리 생성
    schools_query = School.query.filter_by(country_id=country_id)
    
    if search:
        schools_query = schools_query.filter(School.name.ilike(f'%{search}%'))
    
    schools_query = schools_query.order_by(School.name.asc())
    pagination = schools_query.paginate(page=page, per_page=per_page, error_out=False)
    
    schools = [get_school_data(school) for school in pagination.items]
    
    return jsonify({
        'schools': schools,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'search': search
    }), 200

@app.route('/api/countries/<int:country_id>/schools/<int:school_id>/colleges', methods=['GET'])
def get_colleges(country_id, school_id):
    # 국가 존재 여부 확인
    country = Country.query.get(country_id)
    if not country:
        return jsonify({'error': '존재하지 않는 국가입니다'}), 404
    
    # 학교 존재 여부와 국가 관계 확인
    school = School.query.get(school_id)
    if not school:
        return jsonify({'error': '존재하지 않는 학교입니다'}), 404
    if school.country_id != country_id:
        return jsonify({'error': '해당 국가의 학교가 아닙니다'}), 400
    
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    # 단과대학 쿼리 생성
    colleges_query = College.query.filter_by(school_id=school_id)
    
    if search:
        colleges_query = colleges_query.filter(College.name.ilike(f'%{search}%'))
    
    colleges_query = colleges_query.order_by(College.name.asc())
    pagination = colleges_query.paginate(page=page, per_page=per_page, error_out=False)
    
    colleges = [get_college_data(college) for college in pagination.items]
    
    return jsonify({
        'colleges': colleges,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'search': search
    }), 200

@app.route('/api/countries/<int:country_id>/schools/<int:school_id>/colleges/<int:college_id>/departments', methods=['GET'])
def get_departments(country_id, school_id, college_id):
    # 국가 존재 여부 확인
    country = Country.query.get(country_id)
    if not country:
        return jsonify({'error': '존재하지 않는 국가입니다'}), 404
    
    # 학교 존재 여부와 국가 관계 확인
    school = School.query.get(school_id)
    if not school:
        return jsonify({'error': '존재하지 않는 학교입니다'}), 404
    if school.country_id != country_id:
        return jsonify({'error': '해당 국가의 학교가 아닙니다'}), 400
    
    # 단과대학 존재 여부와 학교 관계 확인
    college = College.query.get(college_id)
    if not college:
        return jsonify({'error': '존재하지 않는 단과대학입니다'}), 404
    if college.school_id != school_id:
        return jsonify({'error': '해당 학교의 단과대학이 아닙니다'}), 400
    
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    # 학과 쿼리 생성
    departments_query = Department.query.filter_by(college_id=college_id)
    
    if search:
        departments_query = departments_query.filter(Department.name.ilike(f'%{search}%'))
    
    departments_query = departments_query.order_by(Department.name.asc())
    pagination = departments_query.paginate(page=page, per_page=per_page, error_out=False)
    
    departments = [get_department_data(department) for department in pagination.items]
    
    return jsonify({
        'departments': departments,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'search': search
    }), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['email', 'password', 'nickname', 'country_id', 'school_id', 'college_id', 'department_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field}는 필수 항목입니다'}), 400
    
    # 이메일 중복 확인
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '이미 존재하는 이메일입니다'}), 400
        
    # 닉네임 중복 확인
    if User.query.filter_by(nickname=data['nickname']).first():
        return jsonify({'error': '이미 존재하는 닉네임입니다'}), 400
    
    # 국가 존재 여부 확인
    country = Country.query.get(data['country_id'])
    if not country:
        return jsonify({'error': '유효하지 않은 국가 ID입니다'}), 400
    
    # 학교 존재 여부와 국가 관계 확인
    school = School.query.get(data['school_id'])
    if not school:
        return jsonify({'error': '유효하지 않은 학교 ID입니다'}), 400
    if school.country_id != data['country_id']:
        return jsonify({'error': '해당 국가의 학교가 아닙니다'}), 400
        
    # 단과대학 존재 여부와 학교 관계 확인
    college = College.query.filter_by(
        id=data['college_id'], 
        school_id=data['school_id']
    ).first()
    if not college:
        return jsonify({'error': '유효하지 않은 단과대학 ID이거나 해당 학교에 속하지 않는 단과대학입니다'}), 400
        
    # 학과 존재 여부와 단과대학 관계 확인
    department = Department.query.filter_by(
        id=data['department_id'], 
        college_id=data['college_id']
    ).first()
    if not department:
        return jsonify({'error': '유효하지 않은 학과 ID이거나 해당 단과대학에 속하지 않는 학과입니다'}), 400
    
    # 새 사용자 생성
    new_user = User(
        email=data['email'],
        password=generate_password_hash(data['password']),
        nickname=data['nickname'],
        country_id=data['country_id'],
        school_id=data['school_id'],
        college_id=data['college_id'],
        department_id=data['department_id']
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # JWT 토큰 생성
        access_token = jwt.encode(
            {
                'user_id': new_user.id,
                'email': new_user.email,
                'nickname': new_user.nickname,
                'exp': datetime.utcnow() + timedelta(days=30)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # 사용자 조회
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # JWT 토큰 생성
    access_token = jwt.encode(
        {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=30)
        },
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return jsonify({
        "access_token": access_token,
        "token_type": "bearer"
    }), 200


@app.route('/api/posts', methods=['GET'])
def get_posts():
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 필터링 파라미터
    category = request.args.get('category')
    search = request.args.get('search', '')
    school_id = request.args.get('school_id', type=int)
    college_id = request.args.get('college_id', type=int)
    department_id = request.args.get('department_id', type=int)
    
    # 현재 사용자의 학교 정보 가져오기
    current_user_school_id = None
    if 'Authorization' in request.headers:
        try:
            token = request.headers['Authorization'].split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user = User.query.get(data['user_id'])
            if user:
                current_user_school_id = user.school_id
        except:
            pass
    
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
            (PostComment.deleted_at == None, PostComment.id)
        ))).label('comment_count'),
        func.count(distinct(case((PostLike.type == 'like', PostLike.id)))).label('like_count'),
        func.count(distinct(case((PostLike.type == 'dislike', PostLike.id)))).label('dislike_count')
    ).outerjoin(PostView, Post.id == PostView.post_id)\
    .outerjoin(PostComment, Post.id == PostComment.post_id)\
    .outerjoin(PostLike, Post.id == PostLike.post_id)\
    .filter(Post.deleted_at == None)
    
    # 학교 필터 적용
    if school_id:
        posts_query = posts_query.filter(Post.school_id == school_id)
    elif current_user_school_id:
        posts_query = posts_query.filter(Post.school_id == current_user_school_id)
    
    # 단과대학 필터 적용
    if college_id:
        posts_query = posts_query.filter(Post.college_id == college_id)
    
    # 학과 필터 적용
    if department_id:
        posts_query = posts_query.filter(Post.department_id == department_id)
    
    # 카테고리 필터 적용
    if category:
        posts_query = posts_query.filter(Post.category == category)
    
    # 검색어 필터 적용
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
    
    # 결과 포맷팅
    posts = [
        get_post_data(post, view_count, comment_count, like_count, dislike_count)
        for post, view_count, comment_count, like_count, dislike_count in pagination.items
    ]
    
    return jsonify({
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
    }), 200

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    # 게시물 쿼리 생성
    post_query = db.session.query(
        Post,
        func.count(distinct(PostView.id)).label('view_count'),
        func.count(distinct(case(
            (PostComment.deleted_at == None, PostComment.id)
        ))).label('comment_count'),
        func.count(distinct(case((PostLike.type == 'like', PostLike.id)))).label('like_count'),
        func.count(distinct(case((PostLike.type == 'dislike', PostLike.id)))).label('dislike_count')
    ).outerjoin(PostView, Post.id == PostView.post_id)\
    .outerjoin(PostComment, Post.id == PostComment.post_id)\
    .outerjoin(PostLike, Post.id == PostLike.post_id)\
    .filter(Post.id == post_id)\
    .group_by(Post.id)\
    .first()

    if not post_query:
        return jsonify({'error': '존재하지 않는 게시글입니다'}), 404

    post, view_count, comment_count, like_count, dislike_count = post_query
    
    if post.deleted_at:
        return jsonify({'error': '삭제된 게시글입니다'}), 404

    # 조회수 증가 로직
    user_id = None
    if 'Authorization' in request.headers:
        try:
            token = request.headers['Authorization'].split(" ")[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
        except:
            pass

    # IP 주소 가져오기
    ip_address = request.remote_addr

    # 이미 조회한 기록이 있는지 확인
    existing_view = PostView.query.filter(
        PostView.post_id == post_id,
        or_(
            and_(PostView.user_id == user_id, PostView.user_id != None),
            and_(PostView.ip_address == ip_address, PostView.user_id == None)
        )
    ).first()

    # 조회 기록이 없으면 새로 생성
    if not existing_view:
        new_view = PostView(
            post_id=post_id,
            user_id=user_id,
            ip_address=ip_address if not user_id else None
        )
        db.session.add(new_view)
        db.session.commit()
        view_count += 1

    return jsonify(get_post_data(post, view_count, comment_count, like_count, dislike_count)), 200

@app.route('/api/posts', methods=['POST'])
@token_required
def create_post(current_user):
    data = request.get_json()
    
    # 필수 필드 확인
    required_fields = ['title', 'content', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field}는 필수 항목입니다'}), 400
    
    # 랜덤 닉네임 생성
    anonymous_nickname = create_unique_nickname()
    if not anonymous_nickname:
        return jsonify({'error': '닉네임을 생성할 수 없습니다'}), 500
    
    # 새 게시글 생성
    new_post = Post(
        title=data['title'],
        content=data['content'],
        category=data['category'],
        user_id=current_user.id,
        nickname=anonymous_nickname,  # anonymous_nickname에서 변경
        school_id=current_user.school_id,
        college_id=current_user.college_id,
        department_id=current_user.department_id
    )
    
    try:
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify(get_post_data(new_post, 0, 0, 0, 0)), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_post(current_user, post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': '존재하지 않는 게시글입니다'}), 404
        
    if post.deleted_at:
        return jsonify({'error': '삭제된 게시글입니다'}), 404
        
    if post.user_id != current_user.id:
        return jsonify({'error': '게시글을 수정할 권한이 없습니다'}), 403
    
    data = request.get_json()
    
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
                (PostComment.deleted_at == None, PostComment.id)
            ))).label('comment_count'),
            func.count(distinct(case((PostLike.type == 'like', PostLike.id)))).label('like_count'),
            func.count(distinct(case((PostLike.type == 'dislike', PostLike.id)))).label('dislike_count')
        ).outerjoin(PostView, Post.id == PostView.post_id)\
        .outerjoin(PostComment, and_(Post.id == PostComment.post_id, PostComment.deleted_at == None))\
        .outerjoin(PostLike, Post.id == PostLike.post_id)\
        .filter(Post.id == post_id)\
        .group_by(Post.id)\
        .first()
        
        post, view_count, comment_count, like_count, dislike_count = post_data
        return jsonify(get_post_data(post, view_count, comment_count, like_count, dislike_count)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': '존재하지 않는 게시글입니다'}), 404
        
    if post.deleted_at:
        return jsonify({'error': '이미 삭제된 게시글입니다'}), 404
        
    if post.user_id != current_user.id:
        return jsonify({'error': '게시글을 삭제할 권한이 없습니다'}), 403
    
    try:
        post.deleted_at = datetime.utcnow()
        db.session.commit()
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 게시글 존재 여부 확인
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '존재하지 않는 게시글입니다'}), 404
        
    if post.deleted_at:
        return jsonify({'error': '삭제된 게시글입니다'}), 404
    
    # 최상위 댓글과 대댓글 수 쿼리
    comments_query = db.session.query(
        PostComment,
        func.count(distinct(PostComment.replies.any())).label('reply_count')
    ).select_from(PostComment).filter(
        PostComment.post_id == post_id,
        PostComment.parent_id == None,  # 최상위 댓글만 가져오기
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
    
    return jsonify({
        'comments': comments,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@token_required
def create_comment(current_user, post_id):
    # 게시글 존재 여부 확인
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '존재하지 않는 게시글입니다'}), 404
        
    if post.deleted_at:
        return jsonify({'error': '삭제된 게시글입니다'}), 404
    
    data = request.get_json()
    
    # 필수 필드 확인
    if 'content' not in data:
        return jsonify({'error': 'content는 필수 항목입니다'}), 400
    
    # parent_id가 있는 경우 부모 댓글 확인
    parent_id = data.get('parent_id')
    if parent_id:
        parent_comment = PostComment.query.get(parent_id)
        if not parent_comment:
            return jsonify({'error': '존재하지 않는 부모 댓글입니다'}), 404
        if parent_comment.post_id != post_id:
            return jsonify({'error': '해당 게시글의 댓글이 아닙니다'}), 400
        if parent_comment.parent_id is not None:
            return jsonify({'error': '대댓글에는 답글을 달 수 없습니다'}), 400
    
    # 랜덤 닉네임 생성
    anonymous_nickname = create_unique_nickname()
    if not anonymous_nickname:
        return jsonify({'error': '닉네임을 생성할 수 없습니다'}), 500
    
    # 새 댓글 생성
    new_comment = PostComment(
        content=data['content'],
        user_id=current_user.id,
        post_id=post_id,
        parent_id=parent_id,
        nickname=anonymous_nickname  # anonymous_nickname에서 변경
    )
    
    try:
        db.session.add(new_comment)
        db.session.commit()
        
        # 대댓글 수 조회
        reply_count = 0
        if parent_id is None:  # 최상위 댓글인 경우에만
            reply_count = PostComment.query.filter_by(parent_id=new_comment.id).count()
        
        return jsonify(get_comment_data(new_comment, reply_count)), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>/comments/<int:comment_id>', methods=['PUT'])
@token_required
def update_comment(current_user, post_id, comment_id):
    # 댓글 존재 여부 확인
    comment = PostComment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '존재하지 않는 댓글입니다'}), 404
        
    # 게시글 일치 여부 확인
    if comment.post_id != post_id:
        return jsonify({'error': '해당 게시글의 댓글이 아닙니다'}), 400
        
    # 권한 확인
    if comment.user_id != current_user.id:
        return jsonify({'error': '댓글을 수정할 권한이 없습니다'}), 403
        
    # 삭제된 댓글 확인
    if comment.deleted_at:
        return jsonify({'error': '삭제된 댓글입니다'}), 400
    
    data = request.get_json()
    
    # 필수 필드 확인
    if 'content' not in data:
        return jsonify({'error': 'content는 필수 항목입니다'}), 400
    
    try:
        comment.content = data['content']
        db.session.commit()
        
        # 대댓글 수 조회
        reply_count = 0
        if comment.parent_id is None:  # 최상위 댓글인 경우에만
            reply_count = PostComment.query.filter_by(parent_id=comment.id).count()
        
        return jsonify(get_comment_data(comment, reply_count)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, post_id, comment_id):
    comment = PostComment.query.get(comment_id)
    
    if not comment:
        return jsonify({'error': '존재하지 않는 댓글입니다'}), 404
        
    if comment.post_id != post_id:
        return jsonify({'error': '해당 게시글의 댓글이 아닙니다'}), 400
        
    if comment.user_id != current_user.id:
        return jsonify({'error': '댓글을 삭제할 권한이 없습니다'}), 403
        
    if comment.deleted_at:
        return jsonify({'error': '이미 삭제된 댓글입니다'}), 400
    
    try:
        comment.deleted_at = datetime.utcnow()
        db.session.commit()
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/<int:post_id>/comments/<int:comment_id>/replies', methods=['GET'])
def get_comment_replies(post_id, comment_id):
    # 페이지네이션 파라미터
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 게시글 존재 여부 확인
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '존재하지 않는 게시글입니다'}), 404
        
    if post.deleted_at:
        return jsonify({'error': '삭제된 게시글입니다'}), 404
    
    # 댓글 존재 여부 확인
    comment = PostComment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '존재하지 않는 댓글입니다'}), 404
        
    if comment.post_id != post_id:
        return jsonify({'error': '해당 게시글의 댓글이 아닙니다'}), 400
        
    if comment.parent_id is not None:
        return jsonify({'error': '대댓글에는 답글을 달 수 없습니다'}), 400
    
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
    
    return jsonify({
        'replies': replies,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200

@app.route('/api/users/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify(get_user_data(current_user)), 200


if __name__ == '__main__':
    app.run()
