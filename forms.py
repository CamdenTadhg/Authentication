from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError

def valid_password_length(form, field):
    if len(field.data) < 10:
        raise ValidationError('Password must be at least 10 characters')

def valid_password_characters(form, field):
    special_characters = "!@#$%^&*()_-+=[{]};:|<.>?"
    for char in special_characters:
        if char in field.data:
            return
    raise ValidationError('Password must contain at least one special character.')


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(message="Username is required."), Length(max=20, message="Username must be 20 characters or less.")])
    password = PasswordField("Password", validators=[InputRequired(message="Password is required."), valid_password_length, valid_password_characters])
    password2 = PasswordField("Confirm Password", validators=[InputRequired(message="Please confirm your password.")])
    email = EmailField("Email", validators=[InputRequired(message="Email is required"), Length(max=50, message="Email must be 50 characters or less.")])
    first_name = StringField("First Name", validators=[InputRequired(message="First name is required."), Length(max=30, message="First name must be 30 characters or less.")])
    last_name = StringField("Last Name", validators=[InputRequired(message="Last name is required."), Length(max=30, message='Last name must be 30 characters or less.')])

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(message="Username is required.")])
    password = PasswordField("Password", validators=[InputRequired(message="Password is required.")])

class FeedbackForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired(message="Title is required."), Length(max=100, message="Title must be 100 characters or less.")])
    content = StringField("Content", validators=[InputRequired(message="Content is required.")])

class EmailForm(FlaskForm):
    email = EmailField("Please enter your email", validators=[InputRequired(message="Please enter your email")])

class UpdatePasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[InputRequired(message="Password is required."), valid_password_length, valid_password_characters])
    password2 = PasswordField("Confirm Password", validators=[InputRequired(message="Please confirm your password.")])
