from flask import Blueprint


estimations_app = app = Blueprint('estimations', __name__)


from . import routes  # noqa: F401
