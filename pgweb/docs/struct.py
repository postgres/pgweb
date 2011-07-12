from datetime import date
from models import DocPage
from core.models import Version

def get_struct():
	now = date.today()
	currentversion = Version.objects.get(current=True)

	for d in DocPage.objects.all().extra(where=['version in (select tree from core_version where supported)']):
		yield ('docs/%s/static/%s' % (d.version, d.file),
			   None)
		#FIXME ^ do something smart with priorities on older
		#versions
		if d.version == currentversion.tree:
			yield ('docs/current/static/%s' % d.file,
				   1.0)
