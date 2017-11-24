# root/manage.py

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import app, db, bcrypt
from app.models import User

import os

app.config.from_object(os.environ['APP_CONFIG'])

migrate = Migrate(app, db, directory=app.config['MIGRATION_DIR'])
manager = Manager(app)

# for migrations
manager.add_command('db', MigrateCommand)


@manager.command
def create_db():
    """Creates the db tables."""
    db.create_all()


@manager.command
def drop_db():
    """Drops the db tables."""
    db.drop_all()
    db.session.execute("drop table if exists alembic_version;")
    db.session.commit()


@manager.command
def create_admin():
    """Creates the admin user."""
    user = User(
        firstname    = app.config['ADM_FIRSTNAME'],
        lastname     = app.config['ADM_LASTNAME'],
        username     = app.config['ADM_USERNAME'],
        password     = app.config['ADM_PASSWORD'],
        email        = app.config['ADM_MAIL'],
        admin        = True,
    )
    db.session.add(user)
    db.session.commit()

    token = user.generate_token(
        expiration = app.config['TOKEN_EXPIRES_IN'],
        token_type = 'confirm',
    )
    user.confirm(token)


if __name__ == '__main__':
    manager.run()
