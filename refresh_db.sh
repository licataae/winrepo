#!/bin/bash

rm db-dev.sqlite3
rm profiles/migrations/0*_*.py

source /Users/licata/Documents/winrepo_webdev/demo/webenv/bin #source my webenv
python3.10 manage.py makemigrations
python3.10 manage.py migrate
python3.10 manage.py refresh_fixtures --profiles=1000
