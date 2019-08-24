"""Database singleton."""
from playhouse.pool import PooledMySQLDatabase

from settings import db


database = PooledMySQLDatabase(db.DATABASE,
                               host=db.HOST,
                               port=db.PORT,
                               user=db.USER,
                               password=db.PASSWORD,
                               max_connections=5)


def connect(*args, **kwargs):
    global database
    database.connect()


def close(*args, **kwargs):
    global database

    if database and not database.is_closed():
        database.close()
