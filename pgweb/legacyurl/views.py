from django.http import HttpResponseRedirect


def mailpref(request, listname):
    # Just redirect to the homepage of pglister, don't try specific lists
    return HttpResponseRedirect("https://lists.postgresql.org/")
