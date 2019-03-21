"""Schemas for the input."""
import yaml


_CREATE_USER_SCHEMA = """
email:
    type: string
    required: True
name:
    type: string
password:
    type: string
    required: True
role:
    type: string
organization:
    type: string
"""


CREATE_USER_SCHEMA = yaml.safe_load(_CREATE_USER_SCHEMA)
