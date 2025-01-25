from .base import db, TimestampMixin

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
    replies = db.relationship('PostComment', 
                            backref=db.backref('parent', remote_side=[id]),
                            lazy='dynamic')

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def display_content(self):
        return "삭제된 댓글입니다." if self.is_deleted else self.content

    def __repr__(self):
        return f'<PostComment {self.display_content[:20]}...>'