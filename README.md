## Installation with Docker

`sudo docker-compose up -d`

You certainly want to apply databases migrations after, with:

`sudo docker/migrate.sh`

## Browse the admin

Create a super-user:

```
sudo docker exec -it mvapi_web_1 python ./manage.py createsuperuser
```

Visit the admin page at [http://localhost:8012/admin/](http://localhost:8012/admin/).

## Run the tests

`sudo ./test.sh`

## Create databases migrations

`sudo docker/makemigrations.sh`
