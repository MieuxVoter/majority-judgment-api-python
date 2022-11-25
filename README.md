# API for Mieux Voter

This API allows you to create elections, vote and obtain results with [majority judgment](https://en.wikipedia.org/wiki/Majority_judgment).

You can use our server at [api.mieuxvoter.fr/](api.mieuxvoter.fr/).

Since our API relies on OpenAPI, documentation is automatically generated and it is available at [api.mieuxvoter.fr/redoc](api.mieuxvoter.fr/redoc) or [api.mieuxvoter.fr/docs](api.mieuxvoter.fr/docs).


## Installation with Docker

Copy the `.env` into `.env.local` with your own settings.

Then launch the dockers with:

`docker compose --profile all --env-file .env.local up -d`

Note that you can use the `profile` called `dashboard` if you only need Metabase, `image` if you only need to store images, or `backup` for restic.

You certainly want to apply databases migrations with:

`docker/migrate.sh`


## Run the tests

`docker/test.sh`

## Create databases migrations

`sudo docker/makemigrations.sh`



## Local development

1. Install [postgresql](https://www.postgresql.org/download/).

2. Install python 3.11.

3. Create a new virtual environment and activate it:


```bash
venv .venv
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

5. Copy `.env` into `.env.local` and edit environment variables


6. Start the server:

```
uvicorn app.main:app --reload --env-file .env.local
```

7. Visit the generated documentation:

```
http://127.0.0.1:8000/redoc
```



## TODO

POST elections: creation election
  --> return a JWT token for administration
  --> and the election link
  --> and eventually a series of JWT tokens for voting
PUT elections/[election-id] get all data about a specific election. Might need a JWT token
    --> might return new invites
GET grades/[election-id]: only get the grades related to an election. Might need a JWT token
GET candidates/[election-id]: only get the candidates related to an election. Might need a JWT token
GET votes/[election-id]: only get the votes. Might need a JWT token
POST elections/[election-id]/votes: to vote. Might need a JWT token


GET /metrics a few metrics, among them the number of elections, number of voters and number of votes.
