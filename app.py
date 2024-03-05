from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User

app = Flask(__name__)

app.app_context().push()

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_test"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = 'requin'
app.config["DEBUG_TB_INTERCEPT_REDIRECT"] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

# 17 create base template
# 16 make user routes (/, /register GET, /register POST, /login GET, /login POST, /secret)
# 15 limit access to /secret
# 14 make logout route
# 13 change /secret route to a user page
# 12 create feedback model
# 11 make routes for feedback
# 10 make additional routes for users (/users/username, /users/username/delete, users/username/feedback/add GET, users/username/feedback/add POST, /feedback/feedbackid/update GET, /feedback/feedbackid/update POST, /feedback/feedbackid/delete)

# 9 make sure registration and authentication are methods on your user class
# 8 if there is already a username in session, do not allow users to see register or login forms
# 7 add a 404 page and a 401 page when users are not authenticated
# 6 add column to user table for admins. Admines can add, update, or delete any feedback and delete users
# 5 if form submissions fail, display helpful error messages about what went wrong
# 4 add tests for all view functions and model methods
# 3 validate and confirm password
# 2 add functionality to reset a password
# 1 style it