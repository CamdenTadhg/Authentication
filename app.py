from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from werkzeug.exceptions import NotFound, Unauthorized
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.app_context().push()

# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_test"
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
    loggedinuser = session.get('username')
    return render_template("404.html", loggedinuser=loggedinuser)

@app.errorhandler(Unauthorized)
def not_authorized(error):
    loggedinuser = session.get('username')
    return render_template("401.html", loggedinuser=loggedinuser)

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
        try: 
            new_user = User.register(username, password, email, first_name, last_name)
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another')
            return render_template('register.html', form=form)
        session['username'] = new_user.username
        session['admin'] = new_user.is_admin
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
            session["admin"] = user.is_admin
            return redirect(f'/user/{user.username}')
        else:
            form.username.errors=['invalid username/password']
    return render_template('login.html', form=form)

@app.route('/logout', methods=["POST"])
def logout_user():
    """clear data from session and redirect to home"""
    session.pop('username')
    if session.get('admin'):
        session.pop('admin')
    flash('Goodbye!', 'primary')
    return redirect('/')

#USER ROUTES

@app.route('/user/<username>')
def display_user(username):
    """displays a user to authorized users"""
    if "username" not in session: 
        flash('You must be logged in to view this page', 'danger')
        raise Unauthorized()
    user = User.query.get_or_404(username)
    feedbacks = db.session.execute(db.select(Feedback).where(Feedback.username == user.username)).scalars()
    loggedinuser = session['username']
    return render_template('user.html', user=user, feedbacks=feedbacks, loggedinuser=loggedinuser)

@app.route('/user/<username>/delete', methods=["POST"])
def delete_user(username):
    """deletes a user's account and all associated feedback"""
    user = User.query.get_or_404(username)
    if "username" not in session:
        flash('You must be logged in to view this page', 'danger')
        raise Unauthorized()
    elif session['username'] == user.username or session.get('admin') == True:
        feedbacks = db.session.execute(db.select(Feedback).where(Feedback.username == user.username)).scalars()
        for feedback in feedbacks:
            db.session.delete(feedback)
            try: 
                db.session.commit()
            except: 
                flash('Something went wrong. Please try again.')
                return redirect(f'/user/{username}')
        db.session.delete(user)
        try: 
            db.session.commit()
        except:
            flash('Something went wrong. Please try again.')
            return redirect(f'/user/{username}')
        if session['username'] == user.username:
            session.pop('username')
            session.pop('admin')
        flash('Account deleted', 'danger')
        return redirect('/')
    else: 
        flash('You do not have permissions to delete this account', 'danger')
        raise Unauthorized()

#FEEDBACK ROUTES

@app.route('/user/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    """displays a form for adding feedback and adds feedback to the database"""
    user = User.query.get_or_404(username)
    if "username" not in session:
        flash('You must be logged in to add feedback', 'danger')
        raise Unauthorized()
    elif session['username'] == user.username or session.get('admin') == True:
        form = FeedbackForm()
        loggedinuser = session['username']

        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            new_feedback = Feedback(title=title, content=content, username=user.username)
            db.session.add(new_feedback)
            try: 
                db.session.commit()
            except: 
                flash('Something went wrong. Please try again.')
                return redirect(f'/user/{username}/feedback/add')
            return redirect(f'/user/{username}')

        return render_template('addfeedback.html', form=form, loggedinuser=loggedinuser)
    else:
        flash('You do not have permissions to add feedback for this user', 'danger')        
        raise Unauthorized()
    
@app.route('/feedback/<feedback_id>/update', methods=["GET", "POST"])
def update_feedback(feedback_id):
    """displays a form to update feedback and updates feedback in the database"""
    feedback = Feedback.query.get_or_404(feedback_id)
    user = feedback.user
    if "username" not in session: 
        flash('You must be logged in to update feedback', 'danger')
        raise Unauthorized()
    elif session['username'] == user.username or session.get('admin') == True:
        form = FeedbackForm(obj=feedback)
        loggedinuser = session['username']

        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data
            try: 
                db.session.commit()
            except: 
                flash('Something went wrong. Please try again.')
                return redirect(f'/feedback/{feedback_id}/update', form=form, loggedinuser=loggedinuser)
            return redirect(f'/user/{user.username}')

        return render_template("updatefeedback.html", form=form, loggedinuser=loggedinuser)
    else: 
        flash('You do not have permissions to update feedback for this user', 'danger')
        raise Unauthorized()
    
@app.route('/feedback/<feedback_id>/delete', methods=["POST"])
def delete_feedback(feedback_id):
    """deletes a piece of feedback from the database if the user is authorized"""
    feedback = Feedback.query.get_or_404(feedback_id)
    user = feedback.user
    if "username" not in session: 
        flash('You must be logged in to delete feedback', 'danger')
        raise Unauthorized()
    elif session['username'] == user.username or session.get('admin') == True:
        db.session.delete(feedback)
        try:
            db.session.commit()
        except:
            flash('Something went wrong. Please try again.')
            return redirect(f'/feedback/{feedback_id}')
        return redirect(f'/user/{user.username}')
    else:
        flash('You do not have permissions to delete that feedback.')
        raise Unauthorized()



# 6 add tests for all view functions and model methods
# 5 validate and confirm password
# 4 differentiate between invalid username and invalid password
# 3 add functionality to reset a password
# 2 style it
# 1 pull as much logic as possible out of view functions
