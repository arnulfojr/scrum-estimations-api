"""Schemas for the input."""
import yaml


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
    required: True
    empty: False
role:
    type: string
    empty: False
organization:
    type: string
"""


CREATE_USER_SCHEMA = yaml.safe_load(_CREATE_USER_SCHEMA)
