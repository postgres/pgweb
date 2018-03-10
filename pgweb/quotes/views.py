from pgweb.util.contexts import render_pgweb

from models import Quote

def allquotes(request):
	quotes = Quote.objects.filter(approved=True)
	return render_pgweb(request, 'about', 'quotes/quotelist.html', {
		'quotes': quotes,
	})
