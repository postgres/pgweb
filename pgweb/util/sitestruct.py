from django.conf import settings


def get_all_pages_struct(method='get_struct'):
    """
    Return an iterator over all distinct pages on the site.
    Each page is returned as a tuple consisting of:
    (url, search weight, last_modified)

    It will do so by looking for the module "struct" in all
    installed applications, and calling the get_struct() function
    in all such modules.
    """
    for app in settings.INSTALLED_APPS:
        if app.startswith('pgweb.'):
            try:
                m = __import__(app + ".struct", {}, {}, method)
            except:
                # Failed to import - probably module didnd't exist
                continue

            if hasattr(m, method):
                for x in getattr(m, method)(): yield x
