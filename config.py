# root/config.py

import os, datetime
try:
    # Python 2.7
    import ConfigParser as configparser
except ImportError:
    # Python 3
    import configparser

basedir = os.path.abspath(os.path.dirname(__file__))


def _get_bool_env_var(varname, default=None):

    value = os.environ.get(varname, default)

    if value is None:
        return False
    elif isinstance(value, str) and value.lower() == 'false':
        return False
    elif bool(value) is False:
        return False
    else:
        return bool(value)


class BaseConfig(object):
    """Base configuration."""

    # main config
    SECRET_KEY                   = 'my_precious'
    SECURITY_PASSWORD_SALT       = 'my_precious_two'
    WTF_CSRF_SECRET_KEY          = 'my_precious_three'
    WTF_CSRF_ENABLED             = True
    BCRYPT_LOG_ROUNDS            = 13    # 4 <= BCRYPT_LOG_ROUNDS <= 31
    TOKEN_EXPIRES_IN             = int(os.environ.get('APP_TOKEN_EXPIRES_IN', '48')) # in hours
    THREADS_PER_PAGE             = 2
    DEBUG                        = False
    DEBUG_TB_ENABLED             = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # login
    USE_SESSION_FOR_NEXT         = True
    PERMANENT_SESSION_LIFETIME   = datetime.timedelta(hours=8)
    REMEMBER_COOKIE_DURATION     = datetime.timedelta(days=30)

    # migration
    MIGRATION_DIR = os.path.join(basedir, 'migrations')

    # system admin
    ADM_FIRSTNAME           = os.environ.get('APP_ADM_FIRSTNAME', 'admin_firstname')
    ADM_LASTNAME            = os.environ.get('APP_ADM_LASTNAME', 'admin_lastname')
    ADM_USERNAME            = os.environ.get('APP_ADM_USERNAME', 'admin')
    ADM_PASSWORD            = os.environ.get('APP_ADM_PASSWORD', 'admin')
    ADM_MAIL                = os.environ.get('APP_ADM_MAIL', 'admin@email.com')

    # database config
    DB_USERNAME             = os.environ.get('APP_DB_USERNAME', 'postgres')
    DB_PASSWORD             = os.environ.get('APP_DB_PASSWORD', 'postgres')
    DB_HOST                 = os.environ.get('APP_DB_HOST', 'localhost')
    DB_PORT                 = os.environ.get('APP_DB_PORT', '5432')
    DB_NAME                 = os.environ.get('APP_DB_NAME', 'postgres')
    SQLALCHEMY_DATABASE_URI = "postgresql://%s:%s@%s:%s/%s" % \
        (DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

    # mail settings
    MAIL_SERVER  = os.environ.get('APP_MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT    = int(os.environ.get('APP_MAIL_PORT', 465))
    MAIL_USE_TLS = _get_bool_env_var('APP_MAIL_USE_TLS', False)
    MAIL_USE_SSL = _get_bool_env_var('APP_MAIL_USE_SSL', True)

    # mail authentication
    MAIL_USERNAME = os.environ.get('APP_MAIL_USERNAME', None)
    MAIL_PASSWORD = os.environ.get('APP_MAIL_PASSWORD', None)

    # mail accounts
    MAIL_DEFAULT_SENDER = 'uDina admin <admin@udina.org>'
    MAIL_SUBJECT_PREFIX = '[uDina]'


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG                          = True
    BCRYPT_LOG_ROUNDS              = 4
    WTF_CSRF_ENABLED               = False
    SQLALCHEMY_ECHO                = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DEBUG_TB_ENABLED               = True
    TEMPLATES_AUTO_RELOAD          = True
    TOKEN_EXPIRES_IN               = 1 # in hours
    PERMANENT_SESSION_LIFETIME     = datetime.timedelta(minutes=20)
    REMEMBER_COOKIE_DURATION       = datetime.timedelta(minutes=20)


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING           = True
    DEBUG             = True
    BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED  = False


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG                  = False
    DEBUG_TB_ENABLED       = False

    STRIPE_SECRET_KEY      = None
    STRIPE_PUBLISHABLE_KEY = None

    # production config takes precedence over env variables
    # production config file at /root/instance/production.cfg
    config_path = os.path.join(basedir, 'instance', 'production.cfg')

    # if config file exists, read it:
    if os.path.isfile(config_path):
        config = configparser.ConfigParser(os.environ)

        with open(config_path) as configfile:
            config.readfp(configfile)

        SECRET_KEY             = config.get('keys', 'SECRET_KEY')
        WTF_CSRF_SECRET_KEY    = config.get('keys', 'WTF_CSRF_SECRET_KEY')
        SECURITY_PASSWORD_SALT = config.get('keys', 'SECURITY_PASSWORD_SALT')

        # mail settings
        MAIL_SERVER  = config.get('mail', 'MAIL_SERVER')
        MAIL_PORT    = config.getint('mail', 'MAIL_PORT')
        MAIL_USE_TLS = config.getboolean('mail', 'MAIL_USE_TLS')
        MAIL_USE_SSL = config.getboolean('mail', 'MAIL_USE_SSL')

        # mail authentication
        MAIL_USERNAME       = config.get('mail', 'MAIL_USERNAME')
        MAIL_PASSWORD       = config.get('mail', 'MAIL_PASSWORD')

        # database URI
        DB_USERNAME             = config.get('db', 'DB_USERNAME')
        DB_PASSWORD             = config.get('db', 'DB_PASSWORD')
        DB_HOST                 = config.get('db', 'DB_HOST')
        DB_PORT                 = config.get('db', 'DB_PORT')
        DB_NAME                 = config.get('db', 'DB_NAME')
        SQLALCHEMY_DATABASE_URI = "postgresql://%s:%s@%s:%s/%s" % \
        (DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

        # system admin
        ADM_FIRSTNAME           = config.get('adm', 'ADM_FIRSTNAME')
        ADM_LASTNAME            = config.get('adm', 'ADM_LASTNAME')
        ADM_USERNAME            = config.get('adm', 'ADM_USERNAME')
        ADM_PASSWORD            = config.get('adm', 'ADM_PASSWORD')
        ADM_MAIL                = config.get('adm', 'ADM_MAIL')

        # stripe keys
        STRIPE_SECRET_KEY      = config.get('stripe', 'STRIPE_SECRET_KEY')
        STRIPE_PUBLISHABLE_KEY = config.get('stripe', 'STRIPE_PUBLISHABLE_KEY')
