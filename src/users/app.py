from flask import Blueprint


UsersApp = Blueprint('users', __name__)

from . import routes  # noqa
