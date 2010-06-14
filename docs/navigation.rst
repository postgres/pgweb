Navigation
==========
The navigation system is based on a django context called NavContext,
implemented in pgweb.util.contexts.NavContext. This means that all the
menu links in the system are defined in this file
(pgweb/utils/contexts.py). Each django view needs to specify the
NavContext in it's call to template rendering, and this will make the
correct nav menu show up.

This is one of the parts of the system that can probably be made a lot
easier, leaving much room for future improvement :-)
