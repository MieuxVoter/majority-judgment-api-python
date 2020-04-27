
## Install using Docker

> see root README

---

## Install using virtualenv

> It's usually less painful to install using Docker instead.


### Install the required packages


#### Ubuntu & Debian


    sudo apt install python3 python3-dev virtualenv
    sudo apt install postgresql-server-dev-all


### Set up a virtualenv

    virtualenv .venv --python=python3
    source .venv/bin/activate


### Install Python dependencies

    pip install -r requirements.txt


### Configure your instance

    cp .env .env.local
    nano .env.local
    …
    source .env.local


### Bootstrap PostgreSQL Database

    sudo -u postgres psql
    postgres=# ALTER USER postgres PASSWORD 'MyNotSoSecretPassword';
    postgres=# CREATE DATABASE mvapi;
    python manage.py migrate


### Create an Admin user

    python manage.py createsuperuser


### Develop 

To run each time you're setting up your shell.

    source .venv/bin/activate
    source env.local
    python manage.py runserver

Visit http://localhost:8000/admin


### Test

    python manage.py behave
