# Majority Judgment App Server in Python

> This is the REST API Backend for the Mieux Voter Online WebApp.

You can use our instance of this at [api.mieuxvoter.fr/](https://api.mieuxvoter.fr/).

This API allows you to create elections, vote and obtain results with [majority judgment](https://en.wikipedia.org/wiki/Majority_judgment).

Since our API relies on OpenAPI, documentation is automatically generated and it is available at [api.mieuxvoter.fr/redoc](api.mieuxvoter.fr/redoc) or [api.mieuxvoter.fr/docs](api.mieuxvoter.fr/docs).


## Installation with Docker

Copy the `.env` into `.env.local` with your own settings.

Then launch the docker services with:

    docker compose --profile all --env-file .env.local up --detach

Note that you can use the `profile` called:
- `core` if you only need the backend and database,
- `dashboard` if you only need Metabase,
- `image` if you only need to store images,
- or `backup` for restic.

You certainly want to apply the database migrations with:

    ./docker/migrate.sh


## Run the tests

    ./docker/test.sh


## Create databases migrations

    sudo ./docker/makemigrations.sh


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

You need to define following variables:
```
POSTGRES_NAME
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_USER
POSTGRES_PASSWORD
```

> (In docker, `DB_*` variables are injected to `POSTGRES_*` variables)

:warning: If you're using `launch.json` on vscode, `.env` creates a conflict.  You need to remove it.

6. Start the server:

```
uvicorn app.main:app --reload --env-file .env.local
```

7. Visit the generated documentation at http://127.0.0.1:8000/redoc

> If you need to alter the database, you can create new migrations using [alembic](https://alembic.sqlalchemy.org/en/latest/index.html).


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
