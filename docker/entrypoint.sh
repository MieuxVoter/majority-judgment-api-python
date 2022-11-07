#!/bin/bash
nginx
gunicorn --bind unix:mj_api.sock wsgi:app --access-logfile -
