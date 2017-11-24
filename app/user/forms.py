# root/app/user/forms.py

from flask import flash
from flask_wtf import FlaskForm  # , RecaptchaField
from wtforms import StringField, PasswordField, IntegerField, BooleanField,\
ValidationError
from wtforms.validators import InputRequired, Email, EqualTo, Length, \
NumberRange, Regexp
from app.models import User


username     = StringField('Username', [
            Length(min=4, max=30),
            InputRequired(message='Must provide your username.'),
            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                'Usernames must have only letters, numbers, dots or underscores.')])

password     = PasswordField('Password', [
            Length(min=5, max=30),
            InputRequired(message='Must provide a password.')])

password2    = PasswordField('Confirm password', [
            EqualTo('password', message='Must match Password field.'),
            InputRequired(message='Must provide a confirmation for password.')])

old_password = PasswordField('Actual password', [
            Length(min=5, max=30),
            InputRequired(message='Must provide a password.')])

email        = StringField('Email address', [Email(),
            Length(min=6, max=40),
            InputRequired(message='Forgot your email address?')])

email2       = StringField('Confirm email address', [Email(),
            EqualTo('email', message='Must match Email field.'),
            Length(min=6, max=40),
            InputRequired(message='Forgot your email address?')])

firstname    = StringField('First name', [
            Length(min=4, max=30),
            InputRequired(message='Must provide your first name.'),
            Regexp('^[A-Za-z]*$', 0, 'Names must have only letters.')])

lastname     = StringField('Last name', [
            Length(min=4, max=30),
            InputRequired(message='Must provide your last name.'),
            Regexp('^[A-Za-z]*$', 0, 'Names must have only letters.')])

remember_me  = BooleanField('Remember me', default="checked")

accept_tos   = BooleanField('Accept the ToS', [
            InputRequired(message='Must accept the ToS to register.')])


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'danger')


class LoginForm(FlaskForm):
    username    = username
    password    = password
    remember_me = remember_me


class RegistrationForm(FlaskForm):
    username    = username
    password    = password
    password2   = password2
    email       = email
    email2      = email2
    firstname   = firstname
    lastname    = lastname
    remember_me = remember_me

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangeInfoForm(FlaskForm):
    firstname = StringField('First name', [Length(min=4, max=30),
                Regexp('^[A-Za-z]*$', 0, 'Names must have only letters.')])

    lastname  = StringField('Last name', [Length(min=4, max=30),
                Regexp('^[A-Za-z]*$', 0, 'Names must have only letters.')])


class ChangeEmailForm(FlaskForm):
    email    = email
    email2   = email2
    password = password

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangePasswordForm(FlaskForm):
    old_password = old_password
    password     = password
    password2    = password2


class RequestPasswordResetForm(FlaskForm):
    username = username
    email    = email


class PasswordResetForm(FlaskForm):
    email     = email
    password  = password
    password2 = password2

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')
