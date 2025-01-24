from .base import db, TimestampMixin

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