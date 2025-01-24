from .base import db, TimestampMixin

class Nickname(db.Model, TimestampMixin):
    __tablename__ = 'nicknames'
    
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100), nullable=False, unique=True)


    def __repr__(self):
        return f'<Nickname {self.nickname}>'