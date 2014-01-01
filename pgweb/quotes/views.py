from django.shortcuts import render_to_response

from pgweb.util.contexts import NavContext

from models import Quote

def allquotes(request):
	quotes = Quote.objects.filter(approved=True)
	return render_to_response('quotes/quotelist.html', {
		'quotes': quotes,
	}, NavContext(request, 'about'))
