"""
Esoteric (coming from within) steps about users.
These steps deal with the database directly, and NOT with the REST API.
"""

from behave import given, when, then, step
from hamcrest import assert_that, equal_to

from tools_nlp import parse_amount
from tools_dbal import count_users


###############################################################################

# Aliases?
# ⋅e = (?:[⋅.-]?e|)
# ⋅ne = (?:[⋅.-]?ne|)
# ⋅nes = (?:[⋅.-]?ne|)s?

###############################################################################


# @given
@step(u"un(?:[⋅.-]?e|) citoyen(?:[⋅.-]?ne|) nommé(?:[⋅.-]?e|) (?P<name>.+)")
def create_citizen_named(context, name):
    print("Creating citizen named `%s'…\n" % name)
    from django.contrib.auth.models import User
    user = User.objects.create_user(
        username=name,
        email='user@test.mieuxvoter.fr',
        password=name
    )
    context.that_user = user


# @then
@step(u"(?:qu')?il(?: ne)? devrait y avoir (?P<amount>.+) citoyen(?:[⋅.-]?ne?|)s? dans la base de données")
def there_should_be_n_users(context, amount):
    amount = parse_amount(context, amount)
    assert_that(count_users(), equal_to(amount))
