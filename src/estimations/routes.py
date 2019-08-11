from http import HTTPStatus

from flask import jsonify, make_response, request

from . import models
from .app import EstimationsApp
from .exc import ResourceAlreadyExists


@EstimationsApp.route('/sequences', methods=['GET'])
def get_all_sequences():
    sequences = models.Sequence.all()

    return [sequence.dump() for sequence in sequences]


@EstimationsApp.route('/sequences', methods=['POST'])
def create_sequence():
    payload = request.get_json()

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


@EstimationsApp.route('/sequences/<name>', methods=['GET'])
def get_sequence(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = models.Sequence.lookup(name)

    return make_response(jsonify(sequence.dump()), HTTPStatus.OK)


@EstimationsApp.route('/sequences/<name>', methods=['DELETE'])
def remove_sequence(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = models.Sequence.lookup(name)
    sequence.delete_instance()

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)


@EstimationsApp.route('/sequences/<name>/values', methods=['GET'])
def get_sequence_values(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = models.Sequence.lookup(name)
    models.Value.get_from_sequence(sequence)
    # TODO: continue
