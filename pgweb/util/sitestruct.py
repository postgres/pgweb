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
                if '.apps.' in app:
                    # If the app has a specific appconfig, we still go directly for struct,so remove it
                    app = app[:app.index('.apps.')]
                m = __import__(app + ".struct", {}, {}, method)
            except Exception:
                # Failed to import - probably module didnd't exist
                continue

            if hasattr(m, method):
                for x in getattr(m, method)():
                    yield x
