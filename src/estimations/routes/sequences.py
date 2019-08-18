from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas
from estimations.exc import ResourceAlreadyExists

from ..app import estimations_app
from ..models import Sequence, Value


@estimations_app.route('/sequences', methods=['GET'])
def get_all_sequences():
    sequences = Sequence.all()
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
        sequence = Sequence.from_data(**payload)
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

    sequence = Sequence.lookup(name)

    return make_response(jsonify(sequence.dump()), HTTPStatus.OK)


@estimations_app.route('/sequences/<name>', methods=['DELETE'])
def remove_sequence(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = Sequence.lookup(name)

    if sequence.sessions:
        return make_response(jsonify({
            'message': f'The sequence has sessions and therefore can not be deleted',
        }), HTTPStatus.UNPROCESSABLE_ENTITY)

    sequence.delete_instance()

    return make_response(jsonify(None), HTTPStatus.NO_CONTENT)


@estimations_app.route('/sequences/<name>/values/', methods=['POST'])
def create_values_for_sequence(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = Sequence.lookup(name=name)

    if sequence.values:
        return make_response(jsonify({
            'message': 'The sequence already has values, please remove them',
        }), HTTPStatus.UNPROCESSABLE_ENTITY)

    payload = request.get_json()
    elements = {'values': payload}

    validator = Validator()
    if not validator.validate(elements, schemas.CREATE_VALUES_SCHEMA):
        return make_response(
            jsonify(validator.errors),
            HTTPStatus.BAD_REQUEST,
        )

    values = Value.from_list(payload, sequence)

    return make_response(
        jsonify([value.dump() for value in values]),
        HTTPStatus.CREATED,
    )


@estimations_app.route('/sequences/<name>/values', methods=['DELETE'])
def remove_values_from_sequence(name: str):
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = Sequence.lookup(name=name)
    if not sequence.values:
        return make_response(jsonify({
            f'No values were found for sequence {name}',
        }), HTTPStatus.NOT_FOUND)

    sequence.remove_values()

    return make_response(jsonify({}), HTTPStatus.NO_CONTENT)
