from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas

from ..app import estimations_app
from ..models import Session


@estimations_app.route('/sessions/<code>', methods=['GET'])
def get_session(code: str):
    if not code:
        return make_response(jsonify({
            'message': 'Please provide the session identifier.',
        }), HTTPStatus.NOT_FOUND)

    session = Session.lookup(code)

    return make_response(jsonify(session.dump()), HTTPStatus.OK)


@estimations_app.route('/sessions/', methods=['POST'])
def create_session():
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.CREATE_SESSION):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    session = Session.from_data(**payload)

    return make_response(jsonify(session.dump()), HTTPStatus.CREATED)
