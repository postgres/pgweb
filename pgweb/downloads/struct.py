import os
import pickle
from datetime import date

from django.conf import settings

from models import Product

def get_struct():
	# Products
	for p in Product.objects.filter(approved=True):
		yield ('download/products/%s/' % p.category_id,
			   0.3)

	# FTP browser
	f = open(settings.FTP_PICKLE, "rb")
	allnodes = pickle.load(f)
	f.close()

	for d in allnodes.keys():
		yield ('ftp/%s' % d, None)
