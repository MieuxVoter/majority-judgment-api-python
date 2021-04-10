"""
Add voters to a started election.
"""
from typing import List, Dict
import os
import pathlib
import argparse
import django


def load_mvapi():
    import os
    import sys
    sys.path.append('../')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mvapi.settings")
    django.setup()

load_mvapi()
from election.models import Election, Vote, Token


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--election_id", type=str)
    parser.add_argument("--num_tokens", type=int)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    print(args)

    try:
        election = Election.objects.get(id=args.election_id)
    except Election.DoesNotExist:
        raise ValueError(f"The election {election} does not exist")

    tokens = []
    for email in range(args.num_tokens):
        token = Token.objects.create(election=election)
        tokens.append(token.id)
        # print(token)
        # send_mail_invitation(email, election, token.id)

    with open(args.output, "w") as fid:
        fid.write("\n".join([f"https://app.mieuxvoter.fr/vote/{args.election_id}/?token={t}" for t in tokens]))
