import os

def get_struct():
	yield ('', None)
	yield ('community/', None)
	yield ('support/versioning', None)

	# Enumerate all the templates that will generate pages
	pages_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates/pages/'))
	for root, dirs, files in os.walk(pages_dir):
		# Cut out the reference to the absolute root path
		r = '' if root == pages_dir else os.path.relpath(root, pages_dir)
		for f in files:
			if f.endswith('.html'):
				yield (os.path.join(r, f)[:-5] + "/",
					   None)
