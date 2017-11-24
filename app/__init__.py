# root/app/__init__.py

from flask import Flask, render_template, redirect, url_for, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from flask_debugtoolbar import DebugToolbarExtension

import os


###########################################################################
# Configurations
#
from flask.json import JSONEncoder
from datetime import datetime, date

class MyJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.replace(microsecond=0).isoformat(' ')

        if isinstance(obj, date):
            return obj.isoformat(' ')

        return super(MyJSONEncoder, self).default(obj)

app = Flask(__name__)
app.json_encoder = MyJSONEncoder
app.config.from_object(os.environ['APP_CONFIG'])


###########################################################################
# Extensions
#
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
mail = Mail(app)
moment = Moment(app)
toolbar = DebugToolbarExtension(app)
db = SQLAlchemy(app)


###########################################################################
# Blueprints
#
from app.user.views import mod as user_module
from app._bokeh.views import mod as bokeh_module

app.register_blueprint(user_module, url_prefix='/user')
app.register_blueprint(bokeh_module, url_prefix='/bokeh')


###########################################################################
# Login Manager
#
from app.models import User
from uuid import UUID

login_manager.login_view   = "%s.login" % user_module.name
login_manager.refresh_view = "%s.login" % user_module.name
login_manager.login_message_category = "danger"
login_manager.needs_refresh_message_category = "info"

@login_manager.user_loader
def load_user(id):
    return User.query.get(UUID(id))


###########################################################################
# Defaults
#
@app.route('/')
def home():
    return redirect(url_for('%s.index' % user_module.name))
    # return redirect(url_for('%s.index' % bokeh_module.name))

@app.before_request
def before_request():
    session.modified  = True
    session.permanent = True


###########################################################################
# Error handlers
#
@app.errorhandler(403)
def forbidden_page(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error_page(error):
    return render_template("errors/500.html"), 500
