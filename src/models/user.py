from .base import db, TimestampMixin
from .enums import UserType

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 실명
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    register_type = db.Column(db.Enum(UserType), nullable=False, default=UserType.USER)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    posts = db.relationship('Post', backref='user', lazy=True)
    post_comments = db.relationship('PostComment', backref='user', lazy=True)
    post_likes = db.relationship('PostLike', backref='user', lazy=True)
    post_views = db.relationship('PostView', backref='user', lazy=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None
    
    @property
    def display_nickname(self):
        return "삭제된 유저" if self.is_deleted else self.nickname

    def __repr__(self):
        return f'<User {self.display_nickname}>'