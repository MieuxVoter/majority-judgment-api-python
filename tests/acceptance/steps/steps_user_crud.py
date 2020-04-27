###############################################################################
# from behave import given, when, then
# Pycharm 2020.1 won't understand the above, but it understands `step`.
from behave import step
# Swap to usage of `given`, `when`, `then` when relevant
###############################################################################


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
@step(u"(?:qu')?il ne devrait y avoir aucun citoyen dans la base de données")
def there_should_not_be_any_user(context):
    assert(count_users() == 0)


# @then
@step(u"(?:qu')?il devrait y avoir (?P<amount>.+) citoyen(?:[⋅.-]?ne?|)s? dans la base de données")
def there_should_be_n_users(context, amount):
    amount = parse_amount(context, amount)
    assert(count_users() == amount)
