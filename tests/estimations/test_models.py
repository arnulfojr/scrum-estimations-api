from decimal import Decimal
from unittest import mock
from uuid import uuid4

import pytest

from estimations.models.sequences import Sequence, Value


def linked_valid_values():
    values = list()
    return values


@pytest.fixture(scope='module')
def sequence_without_values():
    sequence = Sequence(name='Empty Sequence')
    sequence.values = []
    return sequence


@pytest.fixture(scope='module')
def sequence_with_valid_linked_values():
    sequence = Sequence(name='Linked Sequence')

    values = list()

    root_value = Value(id=uuid4(), sequence=sequence,
                       name='Root', value=Decimal('0.0'),
                       previous=None, next=None)
    second_value = Value(id=uuid4(), sequence=sequence,
                         name='Second', value=Decimal('1.0'),
                         previous=None, next=None)
    third_value = Value(id=uuid4(), sequence=sequence,
                        name='Third', value=Decimal('2.0'),
                        previous=None, next=None)
    non_numeric_value = Value(id=uuid4(), sequence=sequence,
                              name='Fourth', value=None,
                              previous=None, next=None)

    root_value.previous = None
    root_value.next = second_value
    second_value.previous = root_value
    second_value.next = third_value
    third_value.previous = second_value
    third_value.next = non_numeric_value
    non_numeric_value.previous = third_value
    non_numeric_value.next = None

    # randomly added
    values.append(third_value)
    values.append(non_numeric_value)
    values.append(second_value)
    values.append(root_value)

    sequence.values = values
    return sequence


@pytest.fixture(scope='module')
def sequence_with_no_root_value():
    sequence = Sequence(name='No-Root Sequence')

    values = list()

    first_value = Value(id=uuid4(), sequence=sequence,
                        name='First', value=None,
                        previous=None, next=None)
    second_value = Value(id=uuid4(), sequence=sequence,
                         name='Second', value=None,
                         previous=None, next=None)
    third_value = Value(id=uuid4(), sequence=sequence,
                        name='Third', value=None,
                        previous=None, next=None)
    non_numeric_value = Value(id=uuid4(), sequence=sequence,
                              name='Fourth', value=None,
                              previous=None, next=None)

    first_value.previous = non_numeric_value
    first_value.next = second_value
    second_value.previous = first_value
    second_value.next = third_value
    third_value.previous = second_value
    third_value.next = non_numeric_value
    non_numeric_value.previous = third_value
    non_numeric_value.next = None

    # randomly added
    values.append(third_value)
    values.append(non_numeric_value)
    values.append(second_value)
    values.append(first_value)

    sequence.values = values
    return sequence


def test_sorted_values_for_empty_sequence(sequence_without_values):
    actual_values = sequence_without_values.sorted_values
    assert actual_values is not None
    assert isinstance(actual_values, list)
    assert not actual_values


def test_sorted_values_for_sequence_with_values(sequence_with_valid_linked_values):
    actual_values = sequence_with_valid_linked_values.sorted_values
    assert actual_values is not None
    assert isinstance(actual_values, list)
    assert actual_values
    assert actual_values[0].value == Decimal('0.0')
    assert actual_values[1].value == Decimal('1.0')
    assert actual_values[2].value == Decimal('2.0')
    assert actual_values[3].value is None and actual_values[3].name == 'Fourth'


def test_sorted_values_for_sequence_without_root(sequence_with_no_root_value):
    actual_values = sequence_with_no_root_value.sorted_values
    assert actual_values is not None
    assert isinstance(actual_values, list)
    assert actual_values
    # values aren't supposed to be ordered
    assert actual_values[0].name == 'Third'
    assert actual_values[1].name == 'Fourth'
    assert actual_values[2].name == 'Second'
    assert actual_values[3].name == 'First'


@pytest.fixture(scope='module')
def value_list():
    return [
        {
            'name': 'Two',
            'value': 2.0,
        },
        {
            'name': 'One',
            'value': 1.0,
        },
        {
            'name': 'Third',
            'value': 3.0,
        },
        {
            'name': '?',
        },
        {
            'name': 'Coffee',
        },
    ]


@mock.patch('estimations.models.sequences.database')
@mock.patch.object(Value, 'save')
def test_value_from_list(save_mock, database_mock, value_list):
    values = Value.from_list(value_list, None)
    assert values
    assert database_mock.atomic.called
    # assert the order of values
    for value in values:
        assert value.sequence_id is None
        if value.value:
            assert isinstance(value.value, Decimal)
        assert value.name
        assert value.id is not None

    assert values[0].value <= values[1].value <= values[2].value
    assert values[-1].value is None
    assert values[-1].name == 'Coffee'
    assert values[-2].value is None
    assert values[-2].name == '?'


def test_sequence_value_pairs_without_values(sequence_without_values: Sequence):
    generator = sequence_without_values.value_pairs()
    assert not list(generator)
    assert None is next(generator, None)


def test_sequence_value_pairs_with_valid_values(sequence_with_valid_linked_values: Sequence):
    generator = sequence_with_valid_linked_values.value_pairs()
    pair_values = list(generator)
    assert pair_values

    # test that we actually get pairs
    for pair in pair_values:
        assert pair
        assert pair[0] != pair[1]

    # the last element's right/last value is always None
    assert pair_values[-1][0] is not None
    assert pair_values[-1][1] is None


def test_sequence_value_pairs_with_no_root_value(sequence_with_no_root_value: Sequence):
    generator = sequence_with_no_root_value.value_pairs()
    pair_values = list(generator)
    assert not pair_values


def test_sequence_closest_possible_value(sequence_with_valid_linked_values: Sequence):
    # test 0
    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('0'))
    assert actual.value == Decimal('0.0')

    # test the closest value is one of them
    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('1.0'))
    assert actual.value == Decimal('1.0')
    # test the closest value is one of them
    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('2.0'))
    assert actual.value == Decimal('2.0')

    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('1.5'), round_up=False)  # noqa: E501
    assert actual.value == Decimal('1.0')
    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('1.5'), round_up=True)  # noqa: E501
    assert actual.value == Decimal('2.0')
    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('0.5'), round_up=False)  # noqa: E501
    assert actual.value == Decimal('0.0')
    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('0.5'), round_up=True)  # noqa: E501
    assert actual.value == Decimal('1.0')

    # test the closest value is the higher than the max value
    actual = sequence_with_valid_linked_values.closest_possible_value(Decimal('10'))
    assert actual.value == Decimal('2.0')
