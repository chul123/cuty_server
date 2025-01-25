from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app
from src.models import db, User, Country, School, College, Department

class AuthService:
    @staticmethod
    def register(data):
        # 이메일 중복 확인
        if User.query.filter_by(email=data['email']).first():
            raise ValueError('이미 존재하는 이메일입니다')
        
        # 국가 존재 여부 확인
        country = Country.query.get(data['country_id'])
        if not country:
            raise ValueError('유효하지 않은 국가 ID입니다')
        
        # 학교 존재 여부와 국가 관계 확인
        school = School.query.get(data['school_id'])
        if not school:
            raise ValueError('유효하지 않은 학교 ID입니다')
        if school.country_id != data['country_id']:
            raise ValueError('해당 국가의 학교가 아닙니다')
            
        # 단과대학 존재 여부와 학교 관계 확인
        college = College.query.filter_by(
            id=data['college_id'], 
            school_id=data['school_id']
        ).first()
        if not college:
            raise ValueError('유효하지 않은 단과대학 ID이거나 해당 학교에 속하지 않는 단과대학입니다')
            
        # 학과 존재 여부와 단과대학 관계 확인
        department = Department.query.filter_by(
            id=data['department_id'], 
            college_id=data['college_id']
        ).first()
        if not department:
            raise ValueError('유효하지 않은 학과 ID이거나 해당 단과대학에 속하지 않는 학과입니다')

        # 새 사용자 생성
        new_user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),
            name=data['name'],
            country_id=data['country_id'],
            school_id=data['school_id'],
            college_id=data['college_id'],
            department_id=data['department_id']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return new_user

    @staticmethod
    def login(email, password):
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            raise ValueError('이메일 또는 비밀번호가 잘못되었습니다')
            
        # 삭제된 계정 확인
        if user.is_deleted:
            raise ValueError('삭제된 계정입니다')
            
        return user

    @staticmethod
    def create_access_token(user):
        token_data = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=30)
        }
        
        return jwt.encode(
            token_data,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_token(token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user = User.query.get(data['user_id'])
            
            if not user:
                raise ValueError('존재하지 않는 사용자입니다')
                
            if user.is_deleted:
                raise ValueError('삭제된 사용자입니다')
                
            return user
            
        except jwt.ExpiredSignatureError:
            raise ValueError('만료된 토큰입니다')
        except jwt.InvalidTokenError:
            raise ValueError('유효하지 않은 토큰입니다') 