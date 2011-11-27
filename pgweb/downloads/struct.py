import os
import pickle
from datetime import date

from django.conf import settings

from models import Category

def get_struct():
	# Products
	for c in Category.objects.all():
		yield ('download/products/%s/' % c.id,
			   0.3)

	# Don't index the ftp browser for now - it doesn't really contain
	# anything useful to search
