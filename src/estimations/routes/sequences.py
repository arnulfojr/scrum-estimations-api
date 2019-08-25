from http import HTTPStatus

from cerberus import Validator
from flask import jsonify, make_response, request

from estimations import schemas
from estimations.exc import ResourceAlreadyExists

from ..app import estimations_app
from ..models import Sequence, Value


@estimations_app.route('/sequences', methods=['GET'])
def get_all_sequences():
    """Get all the sequences.
    ---
    tags:
        - Sequences
    definitions:
        Sequences:
            type: array
            items:
                $ref: '#/definitions/Sequence'
    responses:
        200:
            description: all the sequences
            schema:
                $ref: '#/definitions/Sequences'
    """
    sequences = Sequence.all()
    payload = [sequence.dump() for sequence in sequences]
    return make_response(jsonify(payload), HTTPStatus.OK)


@estimations_app.route('/sequences/', methods=['POST'])
def create_sequence():
    """Create a sequence.
    ---
    tags:
        - Sequences
    parameters:
        - in: body
          name: body
          required: True
          schema:
            type: object
            properties:
                name:
                    type: string
    definitions:
        SequenceWithoutValues:
            type: object
            properties:
                name:
                    type: string
                    example: Fibonacci Sequence
    responses:
        201:
            description: The sequence was created
            schema:
                $ref: '#/definitions/SequenceWithoutValues'
        422:
            description: A sequence already exists
            schema:
                $ref: '#/definitions/UnprocessableEntity'
    """
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
    """Get the sequence by name.
    ---
    tags:
        - Sequences
    parameters:
        - in: path
          name: name
          type: string
          required: True
    definitions:
        Sequence:
            type: object
            properties:
                name:
                    type: string
                    example: Fibonacci
                created_at:
                    type: string
                    format: datetime
                values:
                    type: array
                    items:
                        $ref: '#/definitions/Value'
    responses:
        200:
            description: The sequence
            schema:
                $ref: '#/definitions/Sequence'
        404:
            description: The specified sequence was not found
            schema:
                $ref: '#/definitions/NotFound'
    """
    if not name:
        return make_response(jsonify({
            'message': 'Please provide a sequence identifier.',
        }), HTTPStatus.NOT_FOUND)

    sequence = Sequence.lookup(name)

    return make_response(jsonify(sequence.dump()), HTTPStatus.OK)


@estimations_app.route('/sequences/<name>', methods=['DELETE'])
def remove_sequence(name: str):
    """Delete a sequence and all its values.
    ---
    tags:
        - Sequences
    parameters:
        - in: path
          name: name
          type: string
          required: True
    responses:
        204:
            description: The sequence was deleted
        404:
            description: The specified sequence was not found
            schema:
                $ref: '#/definitions/NotFound'
    """
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
    """Add the values to a sequence.
    ---
    description: 'The values are validated.
    The values are then split into numeric and non-numeric values.
    Numeric values are then sorted from minimum to maximum values and saved as a sequence.
    Non-numeric values are then sorted by the name alphabetically and appended at the end
    of the sequence.'
    tags:
        - Sequences
    parameters:
        - in: path
          name: name
          type: string
          required: True
    definitions:
        Values:
            type: array
            items:
                $ref: '#/definitions/Value'
        Value:
            type: object
            properties:
                id:
                    type: string
                    format: uuid
                name:
                    type: string
                    description: Human readable name of the value
                    example: Coffee Break
                value:
                    type: number
                    description: Numeric representation of the value
                    example: 2.0
                    format: float
    responses:
        201:
            description: Values were created
            schema:
                $ref: '#/definitions/Values'
        400:
            description: Bad input
            schema:
                $ref: '#/definitions/ValidationErrors'
        404:
            description: Sequence not found
            schema:
                $ref: '#/definitions/NotFound'
        422:
            description: The sequence has already values
            schema:
                $ref: '#/definitions/UnprocessableEntity'
    """
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
    """Delete values from sequence.
    ---
    tags:
        - Sequences
    parameters:
        - in: path
          name: name
          required: True
          type: string
    responses:
        204:
            description: Values removed from sequence.
        404:
            description: Sequence not found.
            schema:
                $ref: '#/definitions/NotFound'
    """
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
