import os
from datetime import date
from models import Event

def get_struct():
	now = date.today()

	for n in Event.objects.filter(approved=True):
		yearsold = (now - n.startdate).days / 365
		if yearsold > 4:
			yearsold = 4
		yield ('about/events/%s/' % n.id,
			   0.5-(yearsold/10.0))
