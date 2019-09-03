from flask import Blueprint
from flask_cors import CORS


users_app = Blueprint('users', __name__)

CORS(users_app)

from . import routes  # noqa
