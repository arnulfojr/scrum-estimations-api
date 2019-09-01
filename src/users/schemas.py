import yaml

_EMAIL_SCHEMA = """
email:
    type: string
    regex: '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
"""
EMAIL_SCHEMA = yaml.safe_load(_EMAIL_SCHEMA)


_CREATE_USER_SCHEMA = """
email:
    type: string
    required: True
    empty: False
name:
    type: string
    empty: False
    required: True
password:
    type: string
    required: False
    empty: False
role:
    type: string
    empty: False
organization:
    type: string
"""


CREATE_USER_SCHEMA = yaml.safe_load(_CREATE_USER_SCHEMA)
