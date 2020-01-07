## Installation with Docker

Edit the `.env` with your own settings. A secret key can be generated in Python REPL:

```
>>> from django.core.management.utils import get_random_secret_key
>>> get_random_secret_key()
```

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
