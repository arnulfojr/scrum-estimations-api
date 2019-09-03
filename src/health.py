from http import HTTPStatus

from flask import Blueprint, jsonify, make_response
from flask_cors import CORS


health_app = Blueprint('health_app', __name__)


CORS(health_app)


@health_app.route('/healthz', methods=['GET'])
def health_check():
    """Checks the service health.
    ---
    tags:
        - selfz
    responses:
        200:
            description: Successful health check response
            schema:
                type: object
                properties:
                    status:
                        type: string
                        example: I'm ok
    """
    return make_response(jsonify({
        'status': 'OK',
    }), HTTPStatus.OK)
