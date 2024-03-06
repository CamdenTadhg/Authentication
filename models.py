from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def connect_db(app):
    """Connect to feedback database"""

    db.app = app
    db.init_app(app)

class User(db.Model):

    __tablename__ = 'users'

    username = db.Column(db.String(length=20), primary_key=True)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(length=50), nullable=False)
    first_name = db.Column(db.String(length=30), nullable=False)
    last_name = db.Column(db.String(length=30), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    @classmethod
    def register(cls, username, pwd, email, first_name, last_name):
        """Register user w/ hashed password and return user"""

        hashed = bcrypt.generate_password_hash(pwd)
        # turn byte string into normal string
        hashed_utf8 = hashed.decode('utf8')

        #return instance of user w/ username and hashed password
        return cls(username=username, password=hashed_utf8, email=email, first_name=first_name, last_name=last_name)
    
    @classmethod
    def authenticate(cls, username, pwd):
        """Validate that a user exists, have given the right password. Return user if valid, else false"""

        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, pwd):
            #return user instance
            return u
        else:
            return False
    
    @property
    def fullname(self):
        """return user's full name"""
        return f"{self.first_name} {self.last_name}"
    
class Feedback(db.Model):

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(length=100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, db.ForeignKey('users.username'))

    user = db.relationship('User', backref="feedback")