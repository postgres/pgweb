#!/bin/bash

# Run this script to refresh the contents of the fixtures based on data currently in the database.

./manage.py dumpdata --indent 1 --format json core.version core.importedrssfeed core.country core.organisationtype > pgweb/core/fixtures/data.json
./manage.py dumpdata --indent 1 --format json contributors.contributortype > pgweb/contributors/fixtures/data.json
./manage.py dumpdata --indent 1 --format json docs.docpagealias docs.docpageredirect > pgweb/docs/fixtures/data.json
./manage.py dumpdata --indent 1 --format json downloads.category downloads.licencetype > pgweb/downloads/fixtures/data.json
./manage.py dumpdata --indent 1 --format json featurematrix.featuregroup featurematrix.feature > pgweb/featurematrix/fixtures/data.json
./manage.py dumpdata --indent 1 --format json lists.mailinglistgroup > pgweb/lists/fixtures/data.json
./manage.py dumpdata --indent 1 --format json sponsors.sponsortype > pgweb/sponsors/fixtures/data.json
