# root/app/_bokeh/views.py

from flask import Blueprint, request, render_template, flash, redirect, \
url_for, jsonify
from flask_login import login_required, current_user

from app.utils.decorators import check_confirmed
from app.utils.token import confirm_token
from app.models import User, Device, Calibration, Measure
from app._bokeh import forms
from app import db, app

from bokeh.embed import autoload_server
from urllib import urlencode
from sqlalchemy import desc
import json, uuid, datetime


mod = Blueprint('bokeh', __name__,
    template_folder='templates',
    static_folder='static')


def get_user_from(token):
    token_dict = confirm_token(token)
    if isinstance(token_dict, dict) and 'id' in token_dict:
        return User.query.filter_by(id=uuid.UUID(token_dict['id'])).first()
    return None


def get_devices_from(user):
    if user.using_devices:
        _using_devices = [uuid.UUID(key) for key,val in user.using_devices.iteritems()]
        return db.session.query(
                    Device.id,
                    Device.code
                ).\
                filter(Device.id.in_(_using_devices)).\
                all()
    return None


def get_calibrations_from(user):
    if user.using_devices:
        _using_devices = [uuid.UUID(key) for key,val in user.using_devices.iteritems()]
        return  db.session.query(
                    Calibration.id.label('c_id'),
                    Calibration.device_id.label('d_id'),
                    Device.code.label('d_code'),
                    Calibration.data.label('c_data')
                ).\
                distinct(Calibration.device_id).\
                join(Calibration.device).\
                filter(Calibration.device_id.in_(_using_devices)).\
                order_by(Calibration.device_id, Calibration.created_on.desc()).\
                all()
    return None


def get_measurement_from(user):
    return  db.session.query(
                Device.code.label('d_code'),
                Calibration.data.label('c_data'),
                Measure.data.label('m_data'),
                Measure.created_on.op('AT TIME ZONE')('UTC').label('m_date'),
                Measure.id
            ).\
            join(Measure.device).\
            join(Measure.calibration).\
            filter_by(created_by = user.id).\
            order_by(Measure.created_on.desc()).\
            limit(5).\
            all()


@mod.route('/home/')
@mod.route('/', alias=True)
@login_required
@check_confirmed
def index():
    return redirect(url_for('.devices'))


@mod.route('/devices/', methods=['GET', 'POST'])
@login_required
@check_confirmed
def devices():
    form = forms.DeviceForm(request.form)
    if form.validate_on_submit():
        device = Device.query.filter_by(code=form.device_code.data).first()
        if not device:
            device = Device(code = form.device_code.data)
            db.session.add(device)
            db.session.commit()

        if form.use_device.data:
            if current_user.using_devices is None:
                current_user.using_devices = {str(device.id): str(datetime.datetime.utcnow())}
            else:
                _len = len(current_user.using_devices)
                if _len >= 5:
                    _using_devices = sorted(current_user.using_devices.items(), key=lambda x: x[1], reverse=True)
                    for i in _using_devices[4:]:
                        current_user.using_devices.pop(i[0], None)

                current_user.using_devices[str(device.id)] = str(datetime.datetime.utcnow())

            db.session.add(current_user)
            db.session.commit()

        elif current_user.using_devices.pop(str(device.id), None):
            db.session.add(current_user)
            db.session.commit()
    else:
        forms.flash_errors(form)

    return render_template("_bokeh/devices.html", form=form, devices=get_devices_from(current_user))


@mod.route('/get_devices/<token>/')
def get_devices(token):
    user = get_user_from(token)
    if user and user.has_valid_token(token, token_type='bokeh'):
        devices = get_devices_from(user)
        if devices:
            response = dict()
            for row in devices:
                for key in row.keys():
                    if not key in response: response[key] = []
                    response[key].append(getattr(row, key))

            return jsonify(response)

    flash("The token used here may be invalid or expired, "
          "or you have not registered any device to use.", 'danger')
    return 'not_ok'


@mod.route('/calibration/')
@login_required
@check_confirmed
def calibration():
    token = current_user.generate_token(
        expiration = app.config['TOKEN_EXPIRES_IN'],
        token_type = 'bokeh'
    )
    _request = urlencode(dict(token=token))
    script   = autoload_server(model=None, app_path="/_calibre", request=_request)
    return render_template('_bokeh/base_bokeh.html', bokeh_script=script)


@mod.route('/save_calibration/<token>/', methods=['POST'])
def save_calibration(token):
    user = get_user_from(token)
    if user and user.has_valid_token(token, token_type='bokeh'):
        _data = request.get_json(force=True)
        if 'lin' in _data and 'ang' in _data and 'd_id' in _data:
            calibration = Calibration(
                device_id = _data['d_id'],
                data = dict(
                    linear  = _data['lin'],
                    angular = _data['ang'],
                ),
                created_by = user.id,
                updated_by = user.id,
            )
            db.session.add(calibration)
            db.session.commit()

            # Calibration successfully saved
            return 'successfully_saved'

    # The token used here may be invalid or expired,
    # or the data to save may be corrupted
    return 'saving_error'


@mod.route('/get_calibrations/<token>/')
def get_calibrations(token):
    user = get_user_from(token)
    if user and user.has_valid_token(token, token_type='bokeh'):
        calibrations = get_calibrations_from(user)
        if calibrations:
            response = dict()
            for row in calibrations:
                for key in row.keys():
                    if not key in response: response[key] = []
                    response[key].append(getattr(row, key))

            return jsonify(response)

    flash("The token used here may be invalid or expired, "
          "or you have not registered any device to use.", 'danger')
    return 'not_ok'


@mod.route('/measurement/')
@login_required
@check_confirmed
def measurement():
    token = current_user.generate_token(
        expiration = app.config['TOKEN_EXPIRES_IN'],
        token_type = 'bokeh'
    )
    _request = urlencode(dict(token=token))
    script   = autoload_server(model=None, app_path="/_measure", request=_request)
    return render_template('_bokeh/base_bokeh.html', bokeh_script=script)


@mod.route('/save_measurement/<token>/', methods=['POST'])
def save_measurement(token):
    user = get_user_from(token)
    if user and user.has_valid_token(token, token_type='bokeh'):
        _data = request.get_json(force=True)
        if 'f' in _data and 't' in _data and \
        'd_id' in _data and 'c_id' in _data:
            measure = Measure(
                device_id      = _data['d_id'],
                calibration_id = _data['c_id'],
                data = dict(
                    force = _data['f'],
                    time  = _data['t'],
                ),
                created_by = user.id,
                updated_by = user.id,
            )
            db.session.add(measure)
            db.session.commit()

            # Measurement successfully saved
            return 'successfully_saved'

    # The token used here may be invalid or expired,
    # or the data to save may be corrupted
    return 'saving_error'


@mod.route('/get_measurement/<token>/')
def get_measurement(token):
    user = get_user_from(token)
    if user and user.has_valid_token(token, token_type='bokeh'):
        measurements = get_measurement_from(user)
        if measurements:
            response = dict()
            for row in measurements:
                for key in row.keys():
                    if not key in response: response[key] = []
                    response[key].append(getattr(row, key))

            return jsonify(response)

    flash("The token used here may be invalid or expired, "
          "or there is no measurement saved.", 'danger')
    return 'not_ok'


@mod.route('/plot_measures/')
@login_required
@check_confirmed
def plot_measures():
    token = current_user.generate_token(
        expiration = app.config['TOKEN_EXPIRES_IN'],
        token_type = 'bokeh'
    )
    _request = urlencode(dict(token=token))
    script   = autoload_server(model=None, app_path="/_plot", request=_request)
    return render_template('_bokeh/base_bokeh.html', bokeh_script=script)
