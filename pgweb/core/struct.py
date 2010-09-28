import os
from datetime import datetime

def get_struct():
	yield ('', None)
	yield ('community/', None)

	# Enumerate all the templates that will generate pages
	for root, dirs, files in os.walk('../templates/pages'):
		r=root[19:] # Cut out ../templates/pages
		for f in files:
			if f.endswith('.html'):
				yield (os.path.join(r, f),
					   None)
