from .base import db, TimestampMixin

class PostLike(db.Model, TimestampMixin):
    __tablename__ = 'post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'like' 또는 'dislike'

    def __repr__(self):
        return f'<PostLike {self.type} on post {self.post_id}>'