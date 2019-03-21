import yaml


_CREATE_ORG = """
name:
  type: string
  required: True
"""

CREATE_ORGANIZATION = yaml.safe_load(_CREATE_ORG)


_JOIN_ORGANIZATION = """
user:
  type: dict
  required: True
  allow_unknown: True
  schema:
    id:
      type: string
      required: True
"""

JOIN_ORGANIZATION = yaml.safe_load(_JOIN_ORGANIZATION)
