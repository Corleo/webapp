# root/app/user/views.py

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user,\
fresh_login_required, login_fresh

from app.utils.decorators import check_confirmed
from app.utils.email import send_email
from app.models import User
from app.user import forms
from app import db, app


mod = Blueprint('user', __name__,
    template_folder='templates',
    static_folder='static')


def send_confirmation_email(
        user, subject, template, redirect_to, token_type,
        to         = None,
        token_dict = None,
        expiration = app.config['TOKEN_EXPIRES_IN']
    ):

    token       = user.generate_token(expiration, token_type, token_dict)
    confirm_url = url_for(redirect_to, token=token, _external=True)
    to          = user.email if to is None else to

    send_email(
        to          = to,
        subject     = subject,
        template    = template,
        user        = user,
        confirm_url = confirm_url,
        expiration  = expiration
    )


def login_dev_user():
    user = User.query.filter_by(username='admin').first()
    login_user(user)


@mod.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        if current_user.confirmed:
            return redirect(url_for('bokeh.index'))
        return render_template("user/home.html")
    return redirect(url_for('.login'))


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    # login_dev_user() # FOR_DEV

    if current_user.is_authenticated and login_fresh():
        return redirect(url_for('.index'))

    form = forms.LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.has_password_equal_to(form.password.data):
            login_user(user, form.remember_me.data)

            flash("Logged in successfully!", 'success')
            return redirect(request.args.get('next') or url_for('.index'))
        else:
            flash("Wrong username or password!", 'danger')
    else:
        forms.flash_errors(form)

    return render_template("user/login.html", form=form)


@mod.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You successfully logged out.', 'success')
    return redirect(url_for('.login'))


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('.index'))

    form = forms.RegistrationForm(request.form)
    if form.validate_on_submit():
        user = User(
            username  = form.username.data,
            password  = form.password.data,
            firstname = form.firstname.data,
            lastname  = form.lastname.data,
            email     = form.email.data
        )
        db.session.add(user)
        db.session.commit()

        send_confirmation_email(
            user,
            subject     = "Please confirm your email",
            template    = 'user/email/confirm.html',
            redirect_to = 'user.confirm_registration',
            token_type  = 'confirm',
        )
        login_user(user, form.remember_me.data)
        flash("A confirmation email has been sent to you by email.", 'info')
        flash("You are logged in with restricted access and need to confirm "
              "to get access to the other pages.", 'warning')
        return redirect(url_for('.index'))

    else:
        forms.flash_errors(form)

    return render_template("user/register.html", form=form)


@mod.route('/unconfirmed/')
@login_required
def unconfirmed():
    if current_user.confirmed:
        flash('Your account has already been confirmed.', 'info')
        return redirect(url_for('.index'))

    flash('Please validate your account using the confirmation email '
          'sent to you.', 'warning')
    return render_template('user/unconfirmed.html')


@mod.route('/confirm/')
@fresh_login_required
def resend_email_confirmation():
    if current_user.confirmed:
        flash('Your account has already been confirmed.', 'info')
        return redirect(url_for('.index'))

    send_confirmation_email(
        current_user,
        subject     = "Please confirm your email",
        template    = 'user/email/confirm.html',
        redirect_to = 'user.confirm_registration',
        token_type  = 'confirm',
    )
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('.unconfirmed'))


@mod.route('/confirm/<token>/')
@fresh_login_required
def confirm_registration(token):
    if current_user.confirmed:
        flash('Your account has already been confirmed.', 'info')

    elif current_user.confirm(token):
        flash('You have confirmed your account. Thank you!', 'success')

    else:
        flash('The confirmation link is invalid or has expired.', 'danger')

    return redirect(url_for('.index'))


@mod.route('/reset/', methods=['GET', 'POST'])
def request_password_reset():
    if not current_user.is_anonymous:
        return redirect(url_for('.index'))

    form = forms.RequestPasswordResetForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.email == form.email.data:
            send_confirmation_email(
                user,
                subject     = "Reset Your Password",
                template    = 'user/email/reset_password.html',
                redirect_to = 'user.password_reset',
                token_type  = 'password',
            )
            flash("An email with instructions to reset your password "
                  "has been sent to you.", 'info')
        else:
            flash("Wrong username or email!", 'danger')
    else:
        forms.flash_errors(form)

    return render_template("user/request_password_reset.html", form=form)


@mod.route('/reset/<token>/', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('.index'))

    form = forms.PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.has_valid_token(token, token_type='password'):
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            flash('Your password has been updated. Please, log in.',
                  'success')
            return redirect(url_for('.login'))

        else:
            flash('The current link to reset your password is invalid or '
                  'has expired. Please, make another request to reset your '
                  'password.',
                  'danger')
            return redirect(url_for('.request_password_reset'))

    else:
        forms.flash_errors(form)

    return render_template('user/reset_password.html', form=form, token=token)


@mod.route('/me/', methods=['GET', 'POST'])
@login_required
@check_confirmed
def my_info():
    form = forms.ChangeInfoForm(request.form)
    if form.validate_on_submit():
        for name, value in form.data.items():
            try:
                user_attr = current_user.__dict__[name]
                form_attr = type(user_attr)(value)

                if user_attr != form_attr:
                    setattr(current_user, name, form_attr)
            except AttributeError:
                return None

        if db.session.is_modified(current_user):
            db.session.add(current_user)
            db.session.commit()

            flash("Your information have been updated successfully!", 'success')

        else:
            flash("You need to change some information to update.", 'warning')

    else:
        forms.flash_errors(form)

    return render_template('user/my_info.html', form=form, user=current_user)


@mod.route('/change-email/', methods=['GET', 'POST'])
@fresh_login_required
@check_confirmed
def request_change_email():
    form = forms.ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.has_password_equal_to(form.password.data):
            send_confirmation_email(
                current_user,
                to          = form.email.data,
                subject     = "Confirm your email address",
                template    = 'user/email/change_email.html',
                redirect_to = 'user.change_email',
                token_type  = 'email',
                token_dict  = dict(email=form.email.data)
            )
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.', 'info')
            return redirect(url_for('.index'))
        else:
            flash('Wrong email or password.')
    else:
        forms.flash_errors(form)

    return render_template("user/change_email.html", form=form)


@mod.route('/change-email/<token>/')
@fresh_login_required
@check_confirmed
def change_email(token):
    if current_user.has_valid_token(token, token_type='email', token_key='email'):
        flash('Your email address has been updated.', 'success')
    else:
        flash('Invalid request to change email.', 'danger')

    return redirect(url_for('.index'))


@mod.route('/change-password/', methods=['GET', 'POST'])
@fresh_login_required
@check_confirmed
def change_password():
    form = forms.ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.has_password_equal_to(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('.index'))
        else:
            flash("Couldn't change your password.", 'danger')
    else:
        forms.flash_errors(form)

    return render_template("user/change_password.html", form=form)
