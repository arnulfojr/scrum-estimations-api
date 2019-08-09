from flask import Blueprint


users_app = Blueprint('users', __name__)

from . import routes  # noqa
