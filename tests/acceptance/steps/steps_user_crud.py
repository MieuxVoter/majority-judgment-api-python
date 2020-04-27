###############################################################################
# from behave import given, when, then
# Pycharm 2020.1 won't understand the above, but it understands `step`.
from behave import step
# Swap to usage of `given`, `when`, `then` when relevant
###############################################################################

from hamcrest import assert_that, equal_to

from tools_nlp import parse_amount
from tools_db import count_users


###############################################################################

# Aliases?
# ⋅e = (?:[⋅.-]?e|)
# ⋅ne = (?:[⋅.-]?ne|)
# ⋅nes = (?:[⋅.-]?ne|)s?

###############################################################################


# @given
@step(u"un(?:[⋅.-]?e|) citoyen(?:[⋅.-]?ne|) nommé(?:[⋅.-]?e|) (?P<name>.+)")
def create_citizen_named(context, name):
    print("Creating citizen named `%s'…" % name)
    from django.contrib.auth.models import User
    _user = User.objects.create_user(
        username=name,
        email='user@test.mieuxvoter.fr',
        password=name
    )


# @then
@step(u"(?:qu')?il(?: ne)? devrait y avoir (?P<amount>.+) citoyen(?:[⋅.-]?ne?|)s? dans la base de données")
def there_should_be_n_users(context, amount):
    amount = parse_amount(context, amount)
    assert_that(count_users(), equal_to(amount))
