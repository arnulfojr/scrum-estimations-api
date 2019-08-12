from http import HTTPStatus
from typing import Union

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas

from . import models
from .app import estimations_app
from .exc import ResourceAlreadyExists, SequenceNotFound


@estimations_app.errorhandler(SequenceNotFound)
def handle_not_found(error: Union[SequenceNotFound, None]):
    return make_response(jsonify({
        'message': str(error),
    }), HTTPStatus.NOT_FOUND)


@estimations_app.route('/sequences', methods=['GET'])
def get_all_sequences():
    sequences = models.Sequence.all()
    payload = [sequence.dump() for sequence in sequences]
    return make_response(jsonify(payload), HTTPStatus.OK)


@estimations_app.route('/sequences/', methods=['POST'])
def create_sequence():
    payload = request.get_json()

    validator = Validator()
    if not validator.validate(payload, schemas.CREATE_SEQUENCE):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        sequence = models.Sequence.from_data(**payload)
    except ResourceAlreadyExists as e:
        return make_response(jsonify({
            'message': str(e),
        }), HTTPStatus.UNPROCESSABLE_ENTITY)
    else:
        return make_response(
            jsonify(sequence.dump()),
            HTTPStatus.CREATED,
        )


@estimations_app.route('/sequences/<name>', methods=['GET'])
def get_sequence(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = models.Sequence.lookup(name)

    return make_response(jsonify(sequence.dump()), HTTPStatus.OK)


@estimations_app.route('/sequences/<name>', methods=['DELETE'])
def remove_sequence(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = models.Sequence.lookup(name)
    sequence.delete_instance()

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)


@estimations_app.route('/sequences/<name>/values', methods=['GET'])
def get_sequence_values(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = models.Sequence.lookup(name)
    models.Value.get_from_sequence(sequence)
    # TODO: continue
