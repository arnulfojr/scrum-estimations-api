from flask import Flask

from common import db
from estimations.app import EstimationsApp  # noqa
from health import HealthApp
from organizations.app import OrganizationsApp
from users.app import UsersApp


App = Flask(__name__)


@App.before_request
def setup_database():
    db.connect()


@App.after_request
def clean_up(exc):
    db.close(exc)


# - register Blueprints - #
App.register_blueprint(HealthApp, url_prefix='/selfz')

App.register_blueprint(UsersApp, '/users')

App.register_blueprint(OrganizationsApp, '/organizations')
