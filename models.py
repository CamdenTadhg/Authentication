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

    username = db.Column(db.Text(length=20), primary_key=True)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text(length=50), nullable=False)
    first_name = db.Column(db.Text(length=30), nullable=False)
    last_name = db.Column(db.Text(length=30), nullable=False)