from django.shortcuts import render_to_response

from pgweb.util.contexts import NavContext

from models import PUG

def index(request):
	"""
	contains list of PUGs, in country/locale alphabetical order
	"""
	pug_list = []
	for pug in PUG.objects.filter(approved=True).order_by('country__name', 'title').all():
		if pug_list and pug_list[-1].get('country') == pug.country.name:
			pug_list[-1]['pugs'].append(pug)
		else:
			pug_list.append({
				'country': pug.country.name,
				'pugs': [pug]
			})
	return render_to_response('pugs/index.html', {
		'pug_list': pug_list,
	}, NavContext(request, 'community'))
