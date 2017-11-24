# root/app/utils/token.py

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app import app


def generate_token(data, expiration=1):
    s = Serializer(app.config['SECRET_KEY'], expiration*3600)
    return s.dumps(data, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'])
        return data
    except:
        return False
