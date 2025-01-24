from .base import db, TimestampMixin

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
    nickname = db.Column(db.String(100), nullable=False)  # 랜덤 닉네임
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    post_comments = db.relationship('PostComment', backref='post', lazy=True)
    post_likes = db.relationship('PostLike', backref='post', lazy=True)
    views = db.relationship('PostView', backref='post', lazy=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def __repr__(self):
        return f'<Post {self.title}>'