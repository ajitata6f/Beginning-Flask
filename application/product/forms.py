from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, SubmitField
from wtforms.validators import InputRequired, EqualTo, Length, Email, ValidationError
from flask_pagedown.fields import PageDownField

from application.product.models import User, UserRole


class LoginForm(FlaskForm):
    username = StringField("username:", validators=[InputRequired("Username is required.")])
    password = PasswordField("password:", validators=[InputRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    username = StringField('username:', validators=[InputRequired()])
    email = StringField('Email:', validators=[InputRequired()])
    password = PasswordField('Password:', validators=[InputRequired(), EqualTo('confirm_password', message='Password must match')])
    confirm_password = PasswordField('Confirm Passord:', validators=[InputRequired()])

class EditProfileForm(FlaskForm):
    firstname = StringField('Firstname', validators=[Length(0, 64)])
    lastname = StringField('Lastname', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')

class EditProfileFormAdmin(FlaskForm):
    firstname = StringField("Firstname", validators=[Length(0, 64)])
    lastname = StringField("Lastname", validators=[Length(0, 64)])
    email = StringField('Email', validators=[InputRequired(), Length(1, 64), Email()])
    username = StringField("Username", validators=[InputRequired(), Length(1, 54)])
    confirmed = BooleanField("Confirmed")
    #choices=[('Admin','1'), ('User','2'), ('Moderator','3')],
    role = SelectField("Role", coerce=int)
    location = StringField("Location", validators=[Length(0, 64)])
    about_me = TextAreaField("About me", validators=[Length(0, 64)])
    submit = SubmitField("Submit")

    def __init__(self, user, *args, **kwargs):
        super(EditProfileFormAdmin, self).__init__(*args, **kwargs)
        self.role.choices = [(role.roleID, role.role_name) for role in UserRole.query.order_by(UserRole.role_name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already exist')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exist')

class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[InputRequired()])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    body = StringField('', validators=[InputRequired()])
    submit = SubmitField('Submit')

