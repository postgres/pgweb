import os
from datetime import date
from models import NewsArticle

def get_struct():
	now = date.today()

	for n in NewsArticle.objects.filter(approved=True):
		yearsold = (now - n.date).days / 365
		if yearsold > 4:
			yearsold = 4
		yield ('about/news/%s/' % n.id,
			   0.5-(yearsold/10.0))
