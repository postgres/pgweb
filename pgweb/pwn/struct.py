import os
from datetime import date
from models import PwnPost

def get_struct():
	now = date.today()

	yield ('community/weeklynews/', None)
