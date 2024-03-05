from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import RegisterForm, LoginForm

app = Flask(__name__)

app.app_context().push()

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_test"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = 'requin'
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.route('/')
def route_register():
    return render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def register_user():
    """displays registration form and registers new users"""
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = new_user.username
        flash('Welcome, Successfully created account', 'success')
        return redirect(f'/user/{new_user.username}')
    return render_template('register.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login_user():
    """displays login form and logs in authorized users"""
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        if user: 
            session["username"] = user.username
            return redirect(f'/user/{user.username}')
        else:
            form.username.errors=['invalid username/password']
    return render_template('login.html', form=form)

@app.route('/user/<username>')
def display_user(username):
    """displays a user to authorized users"""
    if "username" not in session: 
        flash("Please register or login first!", "danger")
        return redirect('/')
    user = User.query.get_or_404(username)
    return render_template('user.html', user=user)

@app.route('/logout', methods=["POST"])
def logout_user():
    """clear data from session and redirect to home"""
    session.pop('username')
    flash('Goodbye!', 'primary')
    return redirect('/')


# 13 create feedback model
# 12 make routes for feedback
# 11 make additional routes for users (/users/username, /users/username/delete, users/username/feedback/add GET, users/username/feedback/add POST, /feedback/feedbackid/update GET, /feedback/feedbackid/update POST, /feedback/feedbackid/delete)

# 10 make sure registration and authentication are methods on your user class
# 9 if there is already a username in session, do not allow users to see register or login forms
# 8 add a 404 page and a 401 page when users are not authenticated
# 7 add column to user table for admins. Admines can add, update, or delete any feedback and delete users
# 6 if form submissions fail, display helpful error messages about what went wrong
# 5 add tests for all view functions and model methods
# 4 validate and confirm password
# 3 differentiate between invalid username and invalid password
# 2 add functionality to reset a password
# 1 style it