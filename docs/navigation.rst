Navigation
==========
The navigation system is based on a django function called render_pgweb,
implemented in pgweb.util.contexts. This means that all the
menu links in the system are defined in this file
(pgweb/utils/contexts.py). Each django view needs to use render_pgweb()
instead of render(), and this will make the correct nav menu show up.

This is one of the parts of the system that can probably be made a lot
easier, leaving much room for future improvement :-)
