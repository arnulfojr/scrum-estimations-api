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


_CREATE_SESSION = """
name:
    type: string
    required: True
    empty: False

organization:
    type: dict
    required: True
    schema:
        id:
            type: string
            empty: False
            required: True
sequence:
    type: dict
    required: True
    schema:
        name:
            type: string
            empty: False
            required: True
"""
CREATE_SESSION = yaml.safe_load(_CREATE_SESSION)
