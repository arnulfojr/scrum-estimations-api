from flask import Blueprint
from flask_cors import CORS


organizations_app = Blueprint('organizations', __name__)


CORS(organizations_app)

# import the routes
from . import routes  # noqa
