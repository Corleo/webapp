# root/app/user/forms.py

from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import InputRequired, Length, Regexp, ValidationError
from app.models import Device

device_code = StringField('Device code', [
            Length(min=4, max=32),
            InputRequired(message='Must provide the device code.'),
            Regexp('^[A-Za-z0-9]*$', 0, 'Codes must have only letters and numbers.')])

use_device  = BooleanField('Use this device', default="unchecked")


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'danger')


class DeviceForm(FlaskForm):
    device_code = device_code
    use_device  = use_device

    # def validate_device_code(self, field):
    #     if Device.query.filter_by(code=field.data).first():
    #         raise ValidationError('Device code already in use.')
