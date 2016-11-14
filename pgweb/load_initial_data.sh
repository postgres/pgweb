#!/bin/bash

# We keep this in a separate script because using initial_data.xxx in django will overwrite
# critical data in the database when running a 'syncdb'. We'd like to keep the ability to
# run syncdb on updates...

echo WARNING: this may overwrite some data in the database with an initial set of data.
echo 'Are you sure you want this (answer "yes" to overwrite)'
read R

if [ "$R" == "yes" ]; then
   find . -name data.yaml | xargs ../manage.py loaddata
fi
