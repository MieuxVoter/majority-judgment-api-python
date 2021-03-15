#!/usr/bin/env bash
DIR=$(dirname "$(readlink -f "$0")")
python manage.py runserver 0.0.0.0:8000
django-admin makemessages -a
django-admin compilemessages
