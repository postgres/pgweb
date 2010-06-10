#!/bin/bash

# This script sucks data over from the old server

if [ "$1" == "" -o "$2" == "" ]; then
   echo "Usage: 0_suck_data.sh <oldconnparams> <newconnparams>"
   exit 1
fi
O=$1
N=$2


(
 echo "BEGIN TRANSACTION;DROP SCHEMA IF EXISTS oldweb CASCADE ; CREATE SCHEMA oldweb; SET search_path='oldweb';"

 cat <<EOF
CREATE FUNCTION news_translation_modified() RETURNS TRIGGER AS \$$ BEGIN END \$$ LANGUAGE 'plpgsql';
CREATE FUNCTION quotes_translation_modified() RETURNS TRIGGER AS \$$ BEGIN END \$$ LANGUAGE 'plpgsql';
CREATE FUNCTION survey_translation_modified() RETURNS TRIGGER AS \$$ BEGIN END \$$ LANGUAGE 'plpgsql';
CREATE FUNCTION event_translation_modified() RETURNS TRIGGER AS \$$ BEGIN END \$$ LANGUAGE 'plpgsql';
CREATE FUNCTION community_login_trigger_sshkey() RETURNS TRIGGER AS \$$ BEGIN END \$$ LANGUAGE 'plpgsql';
EOF

  pg_dump $O -t applications -t comments -t countries -t iptocountry -t developers -t developers_types -t events -t events_location -t events_text -t features_categories -t features_features -t features_groups -t features_matrix -t features_versions -t listgroups -t lists -t mirror -t news -t news_text -t organisations -t product_categories -t products -t profserv -t quotes -t quotes_text -t survey_questions -t surveys -t users -E UTF8 -O -x --no-tablespaces 186_www | sed 's/^SET search_path = public/--&/'
 echo "COMMIT;"
) | psql -v ON_ERROR_STOP=1 $N

