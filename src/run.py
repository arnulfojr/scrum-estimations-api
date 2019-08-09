from flask import Flask

from common import db
from estimations.app import EstimationsApp  # noqa
from health import health_app
from organizations.app import organizations_app
from users.app import users_app


app = Flask(__name__)


@app.before_request
def setup_database():
    db.connect()


@app.teardown_request
def clean_up(exc):
    db.close()


# - register Blueprints - #
app.register_blueprint(health_app, url_prefix='/selfz')

app.register_blueprint(users_app, url_prefix='/users')

app.register_blueprint(organizations_app, url_prefix='/organizations')
