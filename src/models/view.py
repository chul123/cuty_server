from .base import db, TimestampMixin

class PostView(db.Model, TimestampMixin):
    __tablename__ = 'post_views'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6도 지원하기 위해 45자로 설정

    def __repr__(self):
        return f'<PostView post_id={self.post_id}, ip={self.ip_address}>'