import os
from datetime import date
from models import PwnPost

def get_struct():
	now = date.today()

	yield ('community/weeklynews/', None)
	for p in PwnPost.objects.all():
		yearsold = (now - p.date).days / 365
		if yearsold > 4:
			yearsold = 4
		yield ('community/weeklynews/pwn%s' % p.date.strftime("%Y%m%d"),
			   0.5-(yearsold/10.0))
