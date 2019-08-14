import yaml


_CREATE_SEQUENCE = """
name:
    type: string
    required: True
    empty: False
"""

CREATE_SEQUENCE = yaml.safe_load(_CREATE_SEQUENCE)


_CREATE_VALUES = """
values:
    type: list
    schema:
        type: dict
        schema:
            value:
                type: number
                empty: False
            name:
                type: string
                empty: False
"""
CREATE_VALUES_SCHEMA = yaml.safe_load(_CREATE_VALUES)
