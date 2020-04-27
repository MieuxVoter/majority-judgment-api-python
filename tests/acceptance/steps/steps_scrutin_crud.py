###############################################################################
# from behave import given, when, then
# Pycharm 2020.1 won't understand the above, but it understands `step`.
from behave import step
from yaml import safe_load
# Swap to usage of `given`, `when`, `then` when relevant
###############################################################################


from tools_nlp import parse_amount, parse_yaml
from tools_db import count_polls


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
    assert(count_polls() == amount)
