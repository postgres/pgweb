#!/usr/bin/env bash

# Pull the git repo. uwsgi will automatically restart the
# application as necessary.

# Get to our root directory
UPDDIR=$(dirname $0)
cd $UPDDIR

# Unconditionally update the static content (we don't need to reload
# lighttpd for this, so there is no need to actually check for last
# updates or anything like that)
cd $UPDDIR/../../../pgweb-static
git pull -q >/dev/null 2>&1


# Now pull the main repo
cd $UPDDIR

# Sleep 10 seconds to avoid interfering with the automirror scripts that
# also run exactly on the minute.
sleep 10

# Pull changes from the git repo
git pull --rebase -q >/dev/null 2>&1
