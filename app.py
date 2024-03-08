from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, EmailForm, UpdatePasswordForm
from werkzeug.exceptions import NotFound, Unauthorized
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
from sqlalchemy import update
from local_settings import MAIL_PASSWORD


app = Flask(__name__)

app.app_context().push()

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_test"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = 'requin'
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'theenbydeveloper@gmail.com'
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD

mail = Mail(app)

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.route('/')
def display_home():
    if 'username' in session:
        loggedinuser = session['username']
        return render_template('index.html', loggedinuser=loggedinuser)
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
        password2 = form.password2.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        if password != password2:
            form.password2.errors=['Passwords do not match']
        else: 
            try: 
                new_user = User.register(username, password, email, first_name, last_name)
                db.session.add(new_user)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                if 'Key (username)' in str(e):
                    form.username.errors.append('Username taken. Please pick another')
                if 'Key (email)' in str(e):
                    form.email.errors.append('Email already registered. Please log in')
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
        elif not db.session.execute(db.select(User).where(User.username == username)).scalar():
            form.username.errors = ['Invalid username'] 
        else:
            form.password.errors=['Invalid password']
    return render_template('login.html', form=form)

@app.route('/logout', methods=["POST"])
def logout_user():
    """clear data from session and redirect to home"""
    session.pop('username')
    if session.get('admin'):
        session.pop('admin')
    flash('Goodbye!', 'primary')
    return redirect('/')

@app.route('/passwordreset', methods=["GET", "POST"])
def reset_password():
    """displays password reset request form and sends password reset email"""
    if "username" in session:
        flash('You are already logged in.', 'danger')
        return redirect('/')
    
    form = EmailForm()

    if form.validate_on_submit():
        email = form.email.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user: 
            prt = user.get_password_reset_token()
            stmt = update(User).where(User.email == email).values(password_reset_token=prt)
            db.session.execute(stmt)
            db.session.commit()
            msg = Message(subject='Password Reset Link', sender='theenbydeveloper@gmail.com', recipients=[email])
            msg.html = render_template('passwordresetemail.html', prt=prt, email=email)
            mail.send(msg)
            return redirect('/login')
        else:
            form.email.errors=['Email not in database. Please register to proceed.']

    return render_template('reset.html', form=form)

@app.route('/updatepassword', methods=["GET", "POST"])
def update_password():
    """Displays password reset form and resets password"""
    if "username" in session:
        flash('You are already logged in.', 'danger')
        return redirect('/')
    
    form = UpdatePasswordForm()
    email = request.args.get('email')
    prt = request.args.get('prt')
    user = db.session.execute(db.select(User).where(User.email == email)).scalar()

    if form.validate_on_submit():
        password = form.password.data
        password2 = form.password2.data
        if password != password2:
            form.password2.errors=['Passwords do not match']
            return render_template('updatepassword.html', form=form)
        stmt = user.update_password(pwd=password, email=email)
        db.session.execute(stmt)
        try:
            db.session.commit()
        except: 
            flash('Something went wrong. Please try again.')
            return redirect('/passwordreset')
        stmt2 = update(User).where(User.email == email).values(password_reset_token=None)
        db.session.execute(stmt2)
        try:
            db.session.commit()
        except:
            flash('Something went wrong. Please try again')
            return redirect('/passwordreset')
        return redirect('/login')
    elif user and user.password_reset_token == prt:
        return render_template('updatepassword.html', form=form)
    else: 
        flash('Unauthorized password reset attempt', 'danger')
        return redirect('/')
    
@app.route('/getusername', methods=["GET", "POST"])
def get_username():
    """displays username request form and sends username via email"""
    if "username" in session:
        flash('You are already logged in.', 'danger')
        return redirect('/')
    
    form = EmailForm()

    if form.validate_on_submit():
        email = form.email.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user: 
            msg = Message(subject='Feedback App Username', sender='theenbydeveloper@gmail.com', recipients=[email])
            msg.html = render_template('usernameemail.html', username=user.username)
            mail.send(msg)
            return redirect('/login')
        else:
            form.email.errors=['Email not in database. Please register to proceed.']

    return render_template('getusername.html', form=form)


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
            if session.get('admin'):
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
