# Third-party imports
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

# Local imports
from tradelogger.models import Users

class RegistrationForm(FlaskForm):
    # DataRequired = cannot be empty
    # Length = min, max len of username
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is taken. Please choose another username.")
    
    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is already registered. Do you want to log in instead?")


class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class NewLogForm(FlaskForm):
    stock_name = StringField('Stock Name', validators=[DataRequired(), Length(min=2, max=20)])
    buy_price = FloatField('Buy Price', validators=[DataRequired()])
    sell_price = FloatField('Sell Price', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    sell_type = TextAreaField('Sell Type', validators=[DataRequired(), Length(min=1, max=200)])
    submit = SubmitField('Submit')