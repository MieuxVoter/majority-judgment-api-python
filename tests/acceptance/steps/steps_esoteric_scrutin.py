"""
Esoteric (coming from within) steps about polls.
These steps deal with the database directly, and NOT with the REST API.
"""

from behave import given, when, then, step
from hamcrest import assert_that, equal_to
from datetime import datetime as clock, timedelta

from election.models import Election

from tools_nlp import parse_amount, parse_yaml
from tools_dbal import count_polls


###############################################################################


# @given
@step(u"un(?: autre)? scrutin comme suit *:?")
def there_is_a_poll_like_so(context):
    data = parse_yaml(context)
    poll = Election()
    poll.title = data.get('title')
    poll.candidates = data.get('candidates')
    poll.num_grades = data.get('grades', 7)
    poll.finish_at = (timedelta(seconds=data.get('duration', 3600)) + clock.now()).timestamp()
    poll.save()
    context.that_poll = poll


# @then
@step(u"(?:qu')?il(?: ne)? devrait(?: maintenant)? y avoir (?P<amount>.+) scrutins? dans la base de données")
def there_should_be_n_polls(context, amount):
    amount = parse_amount(context, amount)
    assert_that(count_polls(), equal_to(amount))
