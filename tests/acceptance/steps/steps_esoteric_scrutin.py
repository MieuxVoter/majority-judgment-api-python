"""
Esoteric (coming from within) steps about polls.
These steps deal with the database directly, and NOT with the REST API.
"""

from behave import given, when, then, step
from hamcrest import assert_that, equal_to

from tools_nlp import parse_amount, parse_yaml
from tools_dbal import count_polls


###############################################################################


# @given
@step(u"un(?: autre)? scrutin comme suit:?")
def there_is_a_poll_like_so(context):
    data = parse_yaml(context)
    from election.models import Election
    election = Election()
    election.title = data.get('title')
    election.candidates = data.get('candidates')
    election.num_grades = data.get('grades', 7)
    election.save()


# @then
@step(u"(?:qu')?il(?: ne)? devrait(?: maintenant)? y avoir (?P<amount>.+) scrutins? dans la base de données")
def there_should_be_n_polls(context, amount):
    amount = parse_amount(context, amount)
    assert_that(count_polls(), equal_to(amount))
