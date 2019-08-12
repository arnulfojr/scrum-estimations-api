import yaml


_CREATE_SEQUENCE = """
name:
    type: string
    required: True
    empty: False
"""

CREATE_SEQUENCE = yaml.safe_load(_CREATE_SEQUENCE)
