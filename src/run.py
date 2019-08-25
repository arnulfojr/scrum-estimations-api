import os

from flasgger import Swagger
from flask import Flask
from flask_cors import CORS

from common import db
from estimations.app import estimations_app  # noqa
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


# - Add global plugins - #
CORS(app)

Swagger(app, config={
    'headers': [],
    'specs': [
        {
            'endpoint': 'v1',
            'route': '/docs/api/v1.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        },
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': bool(os.getenv('SWAGGER_UI', False)),
    'specs_route': '/docs/api/',
}, template={
    'swagger': '2.0',
    "info": {
        "title": "Estimations API",
        "description": "API documentation for the Estimations API.",
        "contact": {
            "email": "arnulfojr94@gmail.com",
        },
        "version": "0.0.1"
    },
    "schemes": [
        "http",
        "https",
    ],
})

# - register Blueprints - #
app.register_blueprint(health_app, url_prefix='/selfz')

app.register_blueprint(users_app, url_prefix='/users')

app.register_blueprint(organizations_app, url_prefix='/organizations')

app.register_blueprint(estimations_app, url_prefix='/estimations')
