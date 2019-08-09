from flask import Blueprint


EstimationsApp = Blueprint('estimations', __name__)


from . import routes  # noqa: F401
