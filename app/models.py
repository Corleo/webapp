# root/app/models.py

from app import db, bcrypt
from app.utils.token import generate_token, confirm_token

from flask_login import current_user

from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

import uuid


# Associate MutableDict with all future instances of JSON
MutableDict.associate_with(JSON)

def utcnow():
    return db.func.timezone('UTC', db.func.current_timestamp())


def current_user_id():
    try:
        return current_user.id
    except:
        return None


class Base(db.Model):
    __abstract__ = True

    id         = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_on = db.Column(db.DateTime, default=utcnow())
    updated_on = db.Column(db.DateTime, default=utcnow(), onupdate=utcnow())


class BaseUser(Base):
    __abstract__ = True

    @declared_attr
    def created_by(cls):
        return db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), default=current_user_id)

    @declared_attr
    def updated_by(cls):
        return db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), default=current_user_id, onupdate=current_user_id)


class User(Base):
    __tablename__ = 'users'

    username         = db.Column(db.String(32), nullable=False, unique=True)
    _password        = db.Column('password', db.String(128), nullable=False)
    firstname        = db.Column(db.String(32), nullable=False)
    lastname         = db.Column(db.String(32), nullable=False)
    email            = db.Column(db.String(64), nullable=False, unique=True)
    admin            = db.Column(db.Boolean, nullable=False, default=False)
    _confirmed       = db.Column('confirmed', db.Boolean, nullable=False, default=False)
    _confirmed_on    = db.Column('confirmed_on', db.DateTime, nullable=True)
    _token           = db.Column('token', JSON)
    using_devices    = db.Column(JSON)

    devices_created  = db.relationship('Device', backref='creator', lazy='dynamic', foreign_keys="Device.created_by")
    measures_created = db.relationship('Measure', backref='creator', lazy='dynamic', foreign_keys="Measure.created_by")
    devices_updated  = db.relationship('Device', backref='updater', lazy='dynamic', foreign_keys="Device.updated_by")
    measures_updated = db.relationship('Measure', backref='updater', lazy='dynamic', foreign_keys="Measure.updated_by")

    # def __init__(self, **kwargs):
    #     super(User, self).__init__(**kwargs)
    #     # do custom initialization here

    def __repr__(self):
        return '<User:{}>'.format(self.username)

    @property
    def is_active(self):
        """True, as all users are active."""
        return True

    @property
    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True

    def get_id(self):
        """Return the id to satisfy Flask-Login's requirements."""
        try:
            return unicode(self.id) # python 2
        except NameError:
            return str(self.id)     # python 3

    @property
    def confirmed(self):
        return self._confirmed

    @confirmed.setter
    def confirmed(self):
        raise AttributeError('this attribute must be modified by the'
                             ' "confirm()" method.')

    @property
    def confirmed_on(self):
        return self._confirmed_on

    @confirmed_on.setter
    def confirmed_on(self):
        raise AttributeError('this attribute must be modified by the'
                             ' "confirm()" method.')

    def confirm(self, token):
        if not self._confirmed and self.has_valid_token(token, 'confirm'):
            self._confirmed    = True
            self._confirmed_on = utcnow()
            db.session.add(self)
            db.session.commit()
            return True

        return False

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self._password = bcrypt.generate_password_hash(password)

    def has_password_equal_to(self, password):
        return bcrypt.check_password_hash(self._password, password)

    def raise_if_no_attr(self, attr):
        if not hasattr(self, attr):
            raise AttributeError("There is no attribute '%s' in %s object." %
                                (str(attr), self.__class__.__name__))

    @staticmethod
    def cast(obj, value):
        try:
            return type(obj)(value)
        except AttributeError:
            return None

    @property
    def token(self):
        raise AttributeError('token is not a readable attribute')

    @token.setter
    def token(self):
        raise AttributeError('token is not a writable attribute')

    def generate_token(self, expiration, token_type, token_dict=None):
        try:
            _dict = dict(id=str(self.id))

            if token_dict:
                if not isinstance(token_dict, dict) or len(token_dict) > 1:
                    raise AttributeError("'token_dict' must be a single elemment dict.")

                self.raise_if_no_attr(list(token_dict)[0])
                _dict.update(token_dict)

            if token_type:
                if not isinstance(token_type, str):
                    raise AttributeError("'token_type' must be a string name.")

                _token = generate_token(_dict, expiration)
                if self._token is None:
                    self._token = {str(token_type): _token}
                else:
                    self._token.update({str(token_type): _token})

                db.session.add(self)
                db.session.commit()

                return _token

        except (TypeError, AttributeError) as e:
            raise e

    def has_valid_token(self, token, token_type, token_key=None):
        try:
            if token_type:
                if not isinstance(token_type, str):
                    raise AttributeError("'token_type' must be a string name.")

                # invalid token
                if token_type not in self._token or \
                   self._token[token_type] != token:
                    return False

            token_dict = confirm_token(token)
            if isinstance(token_dict, dict):
                # validate user.id from token
                if not 'id' in token_dict: return None
                if self.id != self.cast(self.id, token_dict['id']): return None

                if token_key:
                    # 'token_key' must be a single string argument
                    self.raise_if_no_attr(token_key)
                    if len(token_dict) > 2: return None

                    token_key = str(token_key)
                    if not token_key in token_dict: return None

                    # update user attribute
                    self_arg = self.__dict__[token_key]
                    cast_arg = self.cast(self_arg, token_dict[token_key])
                    setattr(self, token_key, cast_arg)
                    db.session.add(self)
                    db.session.commit()

                return True

            return False

        except TypeError:
            return None


class Device(BaseUser):
    __tablename__ = 'devices'

    code        = db.Column(db.String(32), nullable=False, unique=True)

    calibration = db.relationship('Calibration', backref='device', lazy='dynamic', foreign_keys="Calibration.device_id")
    measures    = db.relationship('Measure', backref='device', lazy='dynamic', foreign_keys="Measure.device_id")

    def __repr__(self):
        return '<Device:{}>'.format(self.code)


class Calibration(BaseUser):
    __tablename__ = 'calibrations'

    device_id   = db.Column(UUID(as_uuid=True), db.ForeignKey('devices.id'), nullable=False)
    data        = db.Column(JSON, nullable=False)

    measures    = db.relationship('Measure', backref='calibration', lazy='dynamic', foreign_keys="Measure.calibration_id")

    def __repr__(self):
        return '<Calibration:{}>'.format(self.id)


class Measure(BaseUser):
    __tablename__ = 'measures'

    device_id      = db.Column(UUID(as_uuid=True), db.ForeignKey('devices.id'), nullable=False)
    calibration_id = db.Column(UUID(as_uuid=True), db.ForeignKey('calibrations.id'), nullable=False)
    data           = db.Column(JSON, nullable=False)

    def __repr__(self):
        return '<Measure:{}>'.format(self.id)

