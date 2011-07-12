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

	# FTP browser
	f = open(settings.FTP_PICKLE, "rb")
	allnodes = pickle.load(f)
	f.close()

	for d in allnodes.keys():
		yield ('ftp/%s' % d, None)
