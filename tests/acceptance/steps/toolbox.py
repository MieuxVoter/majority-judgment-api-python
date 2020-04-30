"""
The intent is for toolbox to be a sort of shortcut, providing most tools.
Not sure this is the python way.
"""

from django.test import Client


# Keep these, it is used by those who import toolbox
from tools_dbal import *
from tools_nlp import *


class Actor(object):
    """
    Light wrapper around HTTP clients, where we can put our nitty-gritty.
    """

    def __init__(self, name=None) -> None:
        super().__init__()
        self.name = name
        self.client = Client()
        self.last_response = None

    def adjust_path(self, path):
        if path.startswith('/'):
            path = path[1:]
        return "/api/election/%s" % path

    def handle_possible_failure(self, method, path, response):
        # FIXME: I18N
        if response.status_code >= 400:
            print("%s %s (%d)\n" % (method, path, response.status_code))
            print(response.content)
            raise AssertionError("Request should succeed.")
        return response

    def post(self, path, data, safe_to_fail=False):
        path = self.adjust_path(path)
        response = self.client.post(path=path, data=data)
        self.last_response = response

        if not safe_to_fail:
            self.handle_possible_failure('POST', path, response)


def parse_actor(context, actor_name):
    if 'actors' not in context:
        context.actors = dict()
    if actor_name not in context.actors:
        context.actors[actor_name] = Actor(name=actor_name)
    return context.actors[actor_name]
