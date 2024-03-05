from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from werkzeug.exceptions import NotFound, Forbidden

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
    if 'username' in session:
        loggedinuser = session['username']
        return render_template('index.html', loggedinuser=loggedinuser)
    else: 
        username = ''
    return render_template('index.html')

@app.errorhandler(NotFound)
def not_found(error):
    return render_template("404.html")

@app.errorhandler(Forbidden)
def not_authorized(error):
    return render_template("403.html")

#AUTHENTICATION ROUTES

@app.route('/register', methods=["GET", "POST"])
def register_user():
    """displays registration form and registers new users. If user already logged in, redirects to home"""
    if "username" in session: 
        flash('You already have an account.', 'danger')
        return redirect('/')
    
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
    """displays login form and logs in authorized users. If user already logged in, redirects to home"""
    if "username" in session: 
        flash('You are already logged in.', 'danger')
        return redirect('/')
    
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

@app.route('/logout', methods=["POST"])
def logout_user():
    """clear data from session and redirect to home"""
    session.pop('username')
    flash('Goodbye!', 'primary')
    return redirect('/')

#USER ROUTES

@app.route('/user/<username>')
def display_user(username):
    """displays a user to authorized users"""
    if "username" not in session: 
        flash('You must be logged in to view this page', 'danger')
        raise Forbidden()
    user = User.query.get_or_404(username)
    feedbacks = db.session.execute(db.select(Feedback).where(Feedback.username == user.username)).scalars()
    loggedinuser = session['username']
    print(loggedinuser)
    return render_template('user.html', user=user, feedbacks=feedbacks, loggedinuser=loggedinuser)

@app.route('/user/<username>/delete', methods=["POST"])
def delete_user(username):
    """deletes a user's account and all associated feedback"""
    user = User.query.get_or_404(username)
    if "username" not in session:
        flash('You must be logged in to view this page', 'danger')
        raise Forbidden()
    elif session['username'] == user.username:
        feedbacks = db.session.execute(db.select(Feedback).where(Feedback.username == user.username)).scalars()
        for feedback in feedbacks:
            db.session.delete(feedback)
            db.session.commit()
        db.session.delete(user)
        db.session.commit()
        session.pop('username')
        flash('Account deleted', 'danger')
    else: 
        flash('You do not have permissions to delete this account', 'danger')
        raise Forbidden()

#FEEDBACK ROUTES

@app.route('/user/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    """displays a form for adding feedback and adds feedback to the database"""
    user = User.query.get_or_404(username)
    if "username" not in session:
        flash('You must be logged in to add feedback', 'danger')
        raise Forbidden()
    elif session['username'] == user.username:
        form = FeedbackForm()
        loggedinuser = session['username']

        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            new_feedback = Feedback(title=title, content=content, username=user.username)
            db.session.add(new_feedback)
            db.session.commit()
            return redirect(f'/user/{username}')

        return render_template('addfeedback.html', form=form, loggedinuser=loggedinuser)
    else:
        flash('You do not have permissions to add feedback for this user', 'danger')        
        raise Forbidden()
    
@app.route('/feedback/<feedback_id>/update', methods=["GET", "POST"])
def update_feedback(feedback_id):
    """displays a form to update feedback and updates feedback in the database"""
    feedback = Feedback.query.get_or_404(feedback_id)
    user = feedback.user
    if "username" not in session: 
        flash('You must be logged in to update feedback', 'danger')
        raise Forbidden()
    elif session['username'] == user.username:
        form = FeedbackForm(obj=feedback)
        loggedinuser = session['username']

        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data
            db.session.commit()
            return redirect(f'/user/{user.username}')

        return render_template("updatefeedback.html", form=form, loggedinuser=loggedinuser)
    else: 
        flash('You do not have permissions to update feedback for this user', 'danger')
        raise Forbidden()
    
@app.route('/feedback/<feedback_id>/delete', methods=["POST"])
def delete_feedback(feedback_id):
    """deletes a piece of feedback from the database if the user is authorized"""
    feedback = Feedback.query.get_or_404(feedback_id)
    user = feedback.user
    if "username" not in session: 
        flash('You must be logged in to delete feedback', 'danger')
        raise Forbidden()
    elif session['username'] == user.username:
        db.session.delete(feedback)
        db.session.commit()
        return redirect(f'/user/{user.username}')
    else:
        flash('You do not have permissions to delete that feedback.')
        raise Forbidden()


# 9 add a 404 page and a 401 page when users are not authenticated
# 8 add column to user table for admins. Admines can add, update, or delete any feedback and delete users
# 7 if form submissions fail, display helpful error messages about what went wrong (messages in forms.py file, username already taken, wrong lengths on values, see what other ways you can break it!)
# 6 add tests for all view functions and model methods
# 5 validate and confirm password
# 4 differentiate between invalid username and invalid password
# 3 add functionality to reset a password
# 2 style it
# 1 pull as much logic as possible out of view functions
