from flask import Blueprint
from flask_cors import CORS


estimations_app = app = Blueprint('estimations', __name__)

CORS(estimations_app)


from . import routes  # noqa: F401
