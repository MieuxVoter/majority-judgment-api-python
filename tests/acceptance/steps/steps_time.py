"""
Basic control of time.
"""

from behave import step
from time import sleep


from tools_nlp import parse_amount


@step(u"j'attends (?P<amount>.+) secondes")
def i_wait_for_seconds(context, amount):
    amount = parse_amount(context, amount)
    sleep(amount)
