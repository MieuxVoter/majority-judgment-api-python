# API for Mieux Voter

This API allows you to create elections, vote and obtain results with [majority judgment](https://en.wikipedia.org/wiki/Majority_judgment).

You can use our server at [demo.mieuxvoter.fr/api/](demo.mieuxvoter.fr/api/).


## Installation with Docker

Edit the `.env` with your own settings. A secret key can be generated in Python REPL:

```
>>> from django.core.management.utils import get_random_secret_key
>>> get_random_secret_key()
```
Create a `.env.local` with :

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_PORT=587
EMAIL_HOST_USER= address of a gmail account
EMAIL_HOST_PASSWORD=gmail account password
```

For the gmail account, it is better to create one specially for this.
In "Manage your google account" / "security" activated the option "Less secure access of applications"


Then launch the dockers with:

`sudo docker-compose up -d`

You certainly want to apply databases migrations with:

`sudo docker/migrate.sh`

## Browse the admin

Create a super-user:

```
sudo docker exec -it mvapi_web_1 python ./manage.py createsuperuser
```

Visit the admin page at [http://localhost:8012/admin/](http://localhost:8012/admin/).

## Run the tests

`sudo docker/test.sh`

## Create databases migrations

`sudo docker/makemigrations.sh`



## Local development

1. Install [postgresql](https://www.postgresql.org/download/).
2. Install `virtualenv`:

```bash
pip install virtualenv
```

3. Create a new virtual environment and activate it:


```bash
virtualenv --python python3.11 .venv
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

5. Edit a `.env` with environment variables: 

```
# All variables are described in app/settings.py
POSTGRES_PASSWORD=
POSTGRES_DB=mv
POSTGRES_NAME=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

6. Start the server:

```
uvicorn app.main:app --reload
```

7. Visit the generated documentation:

```
http://127.0.0.1:8000/redoc
```



## API

POST elections: creation election
  --> return a JWT token for administration
  --> and the election link
  --> and eventually a series of JWT tokens for voting
GET elections/[election-id] get all data about a specific election. Might need a JWT token
PUT elections/[election-id] get all data about a specific election. Might need a JWT token
    --> might return new invites
GET elections/[election-id]/proposals: only get the proposals. Might need a JWT token
GET elections/[election-id]/candidates: only get the candidates. Might need a JWT token
GET elections/[election-id]/votes: only get the votes. Might need a JWT token
POST elections/[election-id]/votes: to vote. Might need a JWT token


GET /metrics a few metrics, among them the number of elections, number of voters and number of votes.

## TODO

[] Clean up nginx.conf
