from datetime import date
from django.db import connection
from core.models import Version

def get_struct():
	now = date.today()
	currentversion = Version.objects.get(current=True)

	# Can't use a model here, because we don't (for some reason) have a
	# hard link to the versions table here
	curs = connection.cursor()
	curs.execute("SELECT d.version, d.file, v.docsloaded FROM docs d INNER JOIN core_version v ON v.tree=d.version WHERE v.supported")
	for version, filename, loaded in curs.fetchall():
		yield ('docs/%s/static/%s' % (version, filename),
			   None, loaded)
		#FIXME ^ do something smart with priorities on older
		#versions
		if version == currentversion.tree:
			yield ('docs/current/static/%s' % filename,
				   1.0, loaded)
