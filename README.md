## Build the docker image

sudo ./build.sh

## Run the docker container

sudo docker-compose up -d

## Initialize the database

sudo ./makemigrations.

sudo ./migrate.sh

## Run the tests

sudo ./test.sh

## Browse the admin

[http://localhost:8012/admin/](http://localhost:8012/admin/)
