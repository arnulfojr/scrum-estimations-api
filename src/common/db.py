"""Database singleton."""
import peewee

from settings import db


database = peewee.MySQLDatabase(db.DATABASE,
                                host=db.HOST,
                                port=db.PORT,
                                user=db.USER,
                                password=db.PASSWORD)


def connect(*args, **kwargs):
    global database
    database.connect()


def close(exc, *args, **kwargs):
    global database

    if database and not database.is_closed():
        database.close()
