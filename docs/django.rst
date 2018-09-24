Django implementation
======================

The pgweb application is a fairly simple django application, since
there is no requirement for advanced logic anywhere on the site.

Actual coding practices are, as usual, not fully documented here. When
developing new functionality, please look at an existing application
in the pgweb/ directory that does something similar, and use the
coding practices used there.

Functions and classes should be documented in-line, through comments
or docstrings.

The site is currently deployed on Django 1.4 (being the standard version
in Debian Wheezy), so all testing should be done against this version.

Database access
---------------
In all places where database access is simple, the django ORM is used
to access the data. In the few places where more advanced queries are
necessary, direct queries to the database are used. There is no
intention to keep the database structure independent of database
used - it's all designed to use PostgreSQL. Therefore, using PostgreSQL
specific syntax in these direct queries is not a problem.

Module split
------------
The module split is not particularly strict, and there is a lot of
cross-referencing between the modules. This is expected...

Settings
--------
All settings should be listed including their default values in the
shipped settings.py. Modifications should always be made in the
settings_local.py file (which is in .gitignore) to make sure they're
not accidentally committed to the main repository, or cause merge conflicts.

Forms
-----
here are some special things to consider when dealing with forms. For
any objects that are going to be moderated, the Model that is used
should set the send_notification attribute to True. This will cause
the system to automatically send out notifications to the NOTIFICATION_EMAIL
address whenever a new object is created or an existing one is modified.

If the form contains any text fields that accept markdown, the
attribute markdown_fields should be set to a tuple containing a list
of these fields. This will cause the system to automatically generate
preview boxes both in the admin interface (provided it's properly
registered) and on the regular forms.

If the model contains a field for "submitter", it will automatically
be filled in with the current user - be sure to exclude it from the
form itself.

Utilities
---------
The util/ subdirectory represents a set of utility functions and
classes, rather than an actual application. This is where common code
is put, that may be used between multiple modules.

pgweb.util.admin
++++++++++++++++
This module contains functionality to help simplify the admin.py
files. In particular, it contains a MarkdownPreviewAdmin class and a
register_markdown function, which are used to register a model to the
admin interface in a way that will make all text fields that are
listed as markdown capable have a preview box in the admin interface.

auth.py
+++++++
This module implements the community login provider for logging into
both the website itself and the admin interface.

contexts.py
+++++++++++
This module implements custom contexts, which is used to implement the
site navigation.

decorators.py
+++++++++++++
This module implements custom decorators used to change view
behavior. This includes decorator ssl_required that makes a view
require an SSL connection to work, and also nocache and cache
decorators that control how long a page can be cached by the frontend
servers.

helpers.py
++++++++++
This module implements helper functions and classes wrapping standard
django functionality to make for less coding, such as form, template
and XML management.

middleware.py
+++++++++++++
This module implements a custom django middleware, that will take care
of redirecting requests to SSL when required (this is controlled by
the decorator @require_ssl). It will also enable "standard" django
workarounds for getting access to the user who is currently executing
the request as part of thread local storage.

misc.py
+++++++
This module implements misc functions, for things like formatting
strings and sending email.

moderation.py
+++++++++++++
This module implements functions related to the moderation of
different objects in the system (objects that are submitted by
end-users and need to be approved before we show them on the website).
