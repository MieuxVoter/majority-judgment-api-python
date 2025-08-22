"""
Esoteric (coming from within) steps about polls.
These steps deal with the database directly, and NOT with the REST API.
"""

from behave import given, when, then, step
from fastapi import Depends
from hamcrest import assert_that, equal_to
from datetime import datetime as clock, timedelta

from sqlalchemy.orm import Session
# from sqlalchemy.testing import db

from app import schemas
from app.crud import create_election, create_candidate
# from app.database import get_db, db_session
from app.models import Grade
# from app.models import Election, Candidate

from tools_nlp import parse_amount, parse_yaml
from tools_dbal import count_polls


# db: Session = Depends(get_db)


# @given
@step(u"un(?: autre)? scrutin comme suit *:?")
def there_is_a_poll_like_so(context):
    data = parse_yaml(context)
    # db: Session = Depends(get_db)
    poll = create_election(
        db=db,
        election=schemas.ElectionCreate(
            name=data.get('title'),
            candidates=data.get('candidates'),
            grades=data.get('grades', [
                Grade(name="Excellent", description="", value=6),
                Grade(name="Très Bien", description="", value=5),
                Grade(name="Bien", description="", value=4),
                Grade(name="Assez Bien", description="", value=3),
                Grade(name="Passable", description="", value=2),
                Grade(name="Insuffisant", description="", value=1),
                Grade(name="À Rejeter", description="", value=0),
            ]),
        ),
    )
    context.that_poll = poll


# @then
@step(u"(?:qu')?il(?: ne)? devrait(?: maintenant)? y avoir (?P<amount>.+) scrutins? dans la base de données")
def there_should_be_n_polls(context, amount):
    amount = parse_amount(context, amount)
    assert_that(count_polls(), equal_to(amount))
