#!/bin/bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn django_app.wsgi --bind 0.0.0.0:$PORT