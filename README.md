## Build the docker image

`sudo ./build.sh`

## Run the docker container

`sudo docker-compose up -d`

## Initialize the database

`sudo ./makemigrations.sh`

`sudo ./migrate.sh`

## Run the tests

`sudo ./test.sh`

## Create a super-user

`sudo docker exec -it mvapi_web_1 python ./manage.py createsuperuser`

## Browse the admin

[http://localhost:8012/admin/](http://localhost:8012/admin/)
