from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Country(db.Model, TimestampMixin):
    __tablename__ = 'countries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(2), nullable=False, unique=True)  # ISO 3166-1 alpha-2 코드
    
    # Relationships
    schools = db.relationship('School', backref='country', lazy=True)
    users = db.relationship('User', backref='country', lazy=True)

    def __repr__(self):
        return f'<Country {self.name}>'
    
class School(db.Model, TimestampMixin):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)

    # Relationships
    colleges = db.relationship('College', backref='school', lazy=True)
    users = db.relationship('User', backref='school', lazy=True)
    posts = db.relationship('Post', backref='school', lazy=True)

    def __repr__(self):
        return f'<School {self.name}>'

class College(db.Model, TimestampMixin):
    __tablename__ = 'colleges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)

    # Relationships
    departments = db.relationship('Department', backref='college', lazy=True)
    users = db.relationship('User', backref='college', lazy=True)
    posts = db.relationship('Post', backref='college', lazy=True)

    def __repr__(self):
        return f'<College {self.name}>'

class Department(db.Model, TimestampMixin):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)

    # Relationships
    users = db.relationship('User', backref='department', lazy=True)
    posts = db.relationship('Post', backref='department', lazy=True)

    def __repr__(self):
        return f'<Department {self.name}>'

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True)
    post_comments = db.relationship('PostComment', backref='author', lazy=True)
    post_likes = db.relationship('PostLike', backref='user', lazy=True)
    post_views = db.relationship('PostView', backref='user', lazy=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None
    
    @property
    def display_name(self):
        return "삭제된 유저" if self.is_deleted else self.name

    def __repr__(self):
        return f'<User {self.display_name}>'

class Post(db.Model, TimestampMixin):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    nickname = db.Column(db.String(100), nullable=False)

    # Relationships
    post_comments = db.relationship('PostComment', backref='post', lazy=True)
    post_likes = db.relationship('PostLike', backref='post', lazy=True)
    views = db.relationship('PostView', backref='post', lazy=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def __repr__(self):
        return f'<Post {self.title}>'

class PostComment(db.Model, TimestampMixin):
    __tablename__ = 'post_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('post_comments.id'), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    nickname = db.Column(db.String(100), nullable=False)

    # Relationships
    replies = db.relationship('PostComment', backref=db.backref('parent', remote_side=[id]), lazy=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def display_content(self):
        return "삭제된 댓글입니다." if self.is_deleted else self.content

    def __repr__(self):
        return f'<PostComment {self.display_content[:20]}...>'

class PostLike(db.Model, TimestampMixin):
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'like' 또는 'dislike'

    def __repr__(self):
        return f'<PostLike {self.type} on post {self.post_id}>'

class PostView(db.Model, TimestampMixin):
    __tablename__ = 'post_views'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6도 지원하기 위해 45자로 설정

    def __repr__(self):
        return f'<PostView post_id={self.post_id}, ip={self.ip_address}>'

class Nickname(db.Model):
    __tablename__ = 'nicknames'
    
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Nickname {self.nickname}>'

