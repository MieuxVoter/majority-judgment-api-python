"""
Local database abstraction layer for step defs.
"""
from behave.runner import Context
from fastapi import Depends
from sqlalchemy.orm import Session
# from sqlalchemy.testing import db

from app import errors
from app.crud import get_election
from app.database import get_db
from app.models import Election


db: Session = Depends(get_db)


class User:
    def __init__(self, username):
        self.username = username


def make_user(context: Context, username):
    user = User(username)
    context.users[username] = user
    return user


def count_users(context: Context):
    return len(context.users.items())


def find_user(context: Context, username: str, relax=False):
    user = context.users.get(username, None)
    if user is not None:
        return user
    if not relax:
        raise ValueError("No user found matching `%s`." % username)
    return None


def count_polls():
    return db.query(Election).count()


def find_poll(identifier, relax=False):
    try:
        return get_election(db, identifier)
    except errors.NotFoundError:
        if not relax:
            raise ValueError("No poll found matching `%s`." % identifier)
    return None

