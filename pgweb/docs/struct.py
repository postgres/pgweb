from django.db import connection
from pgweb.core.models import Version

def get_struct():
	currentversion = Version.objects.get(current=True)

	# Can't use a model here, because we don't (for some reason) have a
	# hard link to the versions table here
	# Make sure we exclude the /devel/ docs because they are blocked by
	# robots.txt, and thus will cause tohusands of warnings in search
	# engines.
	curs = connection.cursor()
	curs.execute("SELECT d.version, d.file, v.docsloaded, v.testing FROM docs d INNER JOIN core_version v ON v.tree=d.version WHERE version > 0 ORDER BY d.version DESC")

	# Start priority is higher than average but lower than what we assign
	# to the current version of the docs.
	docprio = 0.8
	lastversion = None

	for version, filename, loaded, testing in curs.fetchall():
		# Decrease the priority with 0.1 for every version of the docs
		# we move back in time, until we reach 0.1. At 0.1 it's unlikely
		# to show up in a general search, but still possible to reach
		# through version specific searching for example.
		if lastversion != version:
			if docprio > 0.2:
				docprio -= 0.1
			lastversion = version

		yield ('docs/%s/static/%s' % (version, filename),
			   testing and 0.1 or docprio, # beta/rc versions always get 0.1 in prio
			   loaded)

		# Also yield the current version urls, with the highest
		# possible priority
		if version == currentversion.tree:
			yield ('docs/current/static/%s' % filename,
				   1.0, loaded)

# For our internal sitemap (used only by our own search engine),
# include the devel version of the docs (and only those, since the
# other versions are already included)
def get_internal_struct():
	curs = connection.cursor()
	curs.execute("SELECT d.file, v.docsloaded FROM docs d INNER JOIN core_version v ON v.tree=d.version WHERE version = 0")

	for filename, loaded in curs.fetchall():
		yield ('docs/devel/static/%s' % (filename, ),
			   0.1,
			   loaded)
