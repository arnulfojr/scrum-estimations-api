from flask import Blueprint


organizations_app = Blueprint('organizations', __name__)

# import the routes
from . import routes  # noqa
