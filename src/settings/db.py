import os


HOST = os.environ['DB_HOST']

PORT = int(os.getenv('DB_PORT', 3306))

USER = os.environ['DB_USER']

PASSWORD = os.environ['DB_PASSWORD']

DATABASE = os.getenv('DB_NAME', 'admin-tool')

ENDPOINT = f'mysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'
