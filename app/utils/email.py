# root/app/utils/email.py

from flask import current_app, render_template
from flask_mail import Message
from app import mail
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(
        subject    = app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        recipients = [to],
        html       = render_template(template, **kwargs),
        sender     = app.config['MAIL_DEFAULT_SENDER']
    )
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
