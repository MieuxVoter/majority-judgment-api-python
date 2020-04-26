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
