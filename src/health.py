from http import HTTPStatus

from flask import Blueprint, jsonify, make_response


health_app = Blueprint('health_app', __name__)


@health_app.route('/healthz', methods=['GET'])
def health_check():
    return make_response(jsonify({
        'status': 'OK',
    }), HTTPStatus.OK)
