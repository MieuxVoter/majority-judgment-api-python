#!/usr/bin/env bash
DIR=$(dirname "$(readlink -f "$0")")
echo $DIR
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
