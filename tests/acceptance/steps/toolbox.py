from django.test import Client

from tools_nlp import *


class Actor(object):

    def __init__(self, name=None) -> None:
        super().__init__()
        self.name = name
        self.client = Client()

    def adjust_path(self, path):
        if path.startswith('/'):
            path = path[1:]
        return "/api/election/%s" % path

    def handle_possible_failure(self, method, path, response):
        if response.status_code >= 400:
            print("%s %s (%d)" % (method, path, response.status_code))
            print(response.content)
        return response

    def post(self, path, data, safe_to_fail=False):
        path = self.adjust_path(path)
        response = self.client.post(path=path, data=data)
        # response = self.client.generic(path=path, method="POST", data=data)

        if not safe_to_fail:
            self.handle_possible_failure('POST', path, response)


def parse_actor(context, actor_name):
    if 'actors' not in context:
        context.actors = dict()
    if actor_name not in context.actors:
        context.actors[actor_name] = Actor(name=actor_name)
    return context.actors[actor_name]
