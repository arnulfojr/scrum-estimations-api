from datetime import datetime
from decimal import Decimal
from itertools import chain, islice, tee
from typing import Any, Iterator, List, Optional, Tuple, Union
from uuid import uuid4

import peewee

from common.db import database
from common.loggers import logger

from ..exc import (
    ResourceAlreadyExists,
    SequenceNotFound,
    ValueNotFound,
)


class Sequence(peewee.Model):
    """Sequence model.

    Receives the backref from:
        * Value as values
    """

    name = peewee.CharField(primary_key=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        database = database

        table_name = 'sequences'

    @classmethod
    def lookup(cls, name: str) -> 'Sequence':
        """Return the sequence by name."""
        query = cls.select().where(cls.name == name)
        try:
            sequence = query.get()
        except cls.DoesNotExist as e:
            raise SequenceNotFound(f'Sequence with name {name} was not found') from e
        else:
            return sequence

    @classmethod
    def all(cls) -> List['Sequence']:
        """Return all instances."""
        query = cls.select()
        return list(query)

    @classmethod
    def from_data(cls, *, name: str) -> 'Sequence':
        try:
            instance = cls.create(name=name)
        except peewee.IntegrityError as e:
            raise ResourceAlreadyExists(f'Sequence with name {name} already exists') from e
        else:
            return instance

    def dump(self, with_values=True) -> dict:
        data = {
            'name': self.name,
            'created_at': self.created_at.isoformat(),
        }

        if with_values:
            data['values'] = [value.dump() for value in self.sorted_values]

        return data

    @property
    def sorted_values(self) -> List['Value']:
        """Returns a sorted list of the values."""
        if not self.values:
            logger.error('No values found')
            return list()

        numeric_values = [val for val in self.values if val.value is not None]
        if not numeric_values:
            logger.error('Did not found any numeric values')
            return self.values

        root_generator = (nv for nv in numeric_values
                          if nv.previous is None and nv.next is not None)
        root_value = next(root_generator, None)
        if root_value is None:
            logger.error(f'No root value, can not sort in {numeric_values}')
            return self.values

        value, values = root_value, list()
        values.append(value)
        while value.next:
            value = value.next
            if value:
                values.append(value)
            else:
                break

        non_numeric_values = [val for val in self.values if val.value is None]
        if non_numeric_values:
            # sort in place by name, fallback to value's ID
            non_numeric_values.sort(key=lambda v: v.name or str(v.id))

        values.extend(non_numeric_values)
        return values

    def value_pairs(self):
        """Yields the current value and the next value as a 2-value tuple.

        The first pair is (index0, index1) and last pair is (indexN, None).
        Example usage:

        for value, next_value in self.value_pairs():
            pass
        """
        values = self.values
        if not values:
            return

        # start with the root value
        value = next((value for value in values
                     if value.previous is None and value.next is not None), None)
        while value:
            yield value, value.next
            value = value.next

    def closest_possible_value(self, value: Union[Decimal, float],
                               round_up=True) -> Union['Value', None]:
        """Returns the closest possible value in the sequence's values based on the given value."""
        if isinstance(value, float):
            value = Decimal(value)

        left, right = self._closest_adjacent_to(value)
        if left is None and right is None:
            return None
        if left is not None and right is None:
            return left
        if left is None and right is not None:
            return right

        diff_left = abs(left.value - value)
        diff_right = abs(right.value - value)
        if diff_left == diff_right:
            return left if not round_up else right
        if diff_left < diff_right:
            return left
        return right

    def _closest_adjacent_to(self, value) -> Tuple[Optional['Value'], Optional['Value']]:
        for val, next_val in self.value_pairs():
            if next_val is None:
                return None, val
            if val.value is None and next_val.value is None:
                logger.error(f'Value {val.value} and Next Value {next_val.value} are empty')
                continue

            if val.value is not None and next_val.value is None and val.value <= value:
                return val, None
            if val.value is None and next_val.value is not None and value <= next_val.value:
                return None, next_val

            if val.value <= value <= next_val.value:
                return val, next_val

        return None, None

    def get_value_for_numeric_value(self, numeric_value: Union[Decimal, float]) -> Optional['Value']:
        if isinstance(numeric_value, float):
            numeric_value = Decimal(numeric_value)

        # since we do not care about order we will simply remove them all
        numeric_values = [value for value in self.values if value.value is not None]
        for value in numeric_values:
            if value.value == numeric_value:
                return value

        return None

    def get_value_for_value_name(self, name: str, exact_match=True) -> Optional['Value']:
        if not name:
            return None

        # here we actually do not care about the order as well so remove the ones
        # that do not have a name related
        non_numeric_values = [value for value in self.values if value.name is not None]
        for value in non_numeric_values:
            if exact_match:
                if value.name == name:
                    return value
            else:
                if name in value.name:
                    return value

        return None

    def remove_values(self):
        """Removes the related values in an atomic way."""
        values = self.sorted_values
        if not values:
            return
        with database.atomic():
            for value in values:
                value.delete_instance()


class Value(peewee.Model):
    """Estimation value."""

    id = peewee.UUIDField(primary_key=True, default=uuid4)

    sequence = peewee.ForeignKeyField(Sequence, field='name', backref='values',
                                      on_delete='CASCADE',
                                      column_name='sequence')

    previous = peewee.ForeignKeyField('self', null=True, backref='next_value',
                                      on_delete='SET NULL',
                                      column_name='previous')

    next = peewee.ForeignKeyField('self', null=True, backref='previous_value',
                                  on_delete='SET NULL',
                                  column_name='next')

    name = peewee.CharField(null=True)

    value: Decimal = peewee.DecimalField(null=True)

    created_at = peewee.TimestampField(default=datetime.now)

    class Meta:

        indexes = (
            (('previous', 'next'), True),
        )

        database = database

        table_name = 'estimation_values'

    @classmethod
    def lookup(cls, identifier: str):
        query = cls.select().where(cls.id == identifier)
        try:
            value = query.get()
        except cls.DoesNotExist as e:
            raise ValueNotFound(f'No value for {identifier} was found') from e
        else:
            return value

    @classmethod
    def from_list(cls, items: List[dict], sequence: Sequence) -> List['Value']:
        values = list()

        with database.atomic():
            for item in items:
                val = item.get('value')
                try:
                    normalized_value = Decimal(val)
                except TypeError:
                    log_call = logger.error if val is not None else logger.warning
                    log_call(f'Value({val}) was not Decimal and will use None')
                    normalized_value = None

                value = cls(name=item.get('name'),
                            sequence=sequence,
                            value=normalized_value)
                value.save(force_insert=True)
                values.append(value)

        numeric_values = [v for v in values if v.value is not None]
        numeric_values.sort(key=lambda v: v.value)

        non_numeric_values = [v for v in values if v.value is None]
        non_numeric_values.sort(key=lambda v: v.name)

        for previous, current, nxt in previous_and_next(numeric_values):
            current.previous = previous
            current.next = nxt

        with database.atomic():
            for value in numeric_values:
                value.save()

        sorted_values = list()
        sorted_values.extend(numeric_values)
        sorted_values.extend(non_numeric_values)

        return sorted_values

    def dump(self):
        payload = {
            'id': self.id,
        }

        if self.name:
            payload['name'] = self.name

        if self.value is not None:
            payload['value'] = float(self.value)
        else:
            payload['value'] = None

        return payload


def previous_and_next(some_iterable: Iterator[Any]):
    """Iterate over a 3-tuple valued as (previous, current, next)."""
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)
