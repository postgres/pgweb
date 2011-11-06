#!/usr/bin/env bash

#
# The idea:
#  * git-pull the repository
#  * if the repository has changed, kill off the django servers causing the app to restart
#
# Would be even better if we could touch it only after actual code files have changed,
# but this will do fine for now.

# Get to our root directory
UPDDIR=$(dirname $0)
cd $UPDDIR

# Pull changes from the it repo
git pull -q|grep -v "up to date"

# Figure out if something changed
git log -n1 --pretty=oneline > /tmp/pgweb.update
if [ -f "lastupdate" ]; then
   cmp lastupdate /tmp/pgweb.update
   if [ "$?" == "0" ]; then
      # No change, so don't reload
      rm -f /tmp/pgweb.update
      exit
   fi
fi

# Cause reload
echo Reloading website due to updates
pkill -f pgweb/manage.py

# Update the file listing the latest update
mv -f /tmp/pgweb.update lastupdate

