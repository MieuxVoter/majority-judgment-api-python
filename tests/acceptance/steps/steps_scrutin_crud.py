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
@step(u"un scrutin comme suit:?")
def there_is_a_poll_like_so(context):
    data = parse_yaml(context)
    from election.models import Election
    election = Election()
    election.title = data['title']
    election.candidates = data['candidates']
    election.num_grades = 7
    election.save()


# @then
@step(u"(?:qu')?il ne devrait y avoir aucun scrutin dans la base de données")
def there_should_not_be_any_poll(context):
    assert(count_polls() == 0)


# @then
@step(u"(?:qu')?il devrait y avoir (?P<amount>.+) scrutins? dans la base de données")
def there_should_be_n_polls(context, amount):
    amount = parse_amount(context, amount)
    assert(count_polls() == amount)
