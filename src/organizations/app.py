from flask import Blueprint


OrganizationsApp = Blueprint('organizations', __name__)

# import the routes
from . import routes  # noqa
