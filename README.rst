The PostgreSQL website
======================

The code in this repository is what backs the website at www.postgresql.org.

The authoritative repository for this code is on git.postgresql.org, but it's
free to be mirrored anywhere.

Technology
----------
The website code is written in `Python <http://www.python.org>`_ using
the `Django <http://www.djangoproject.com/>`_ framework. Not surprisingly,
`PostgreSQL <http://www.postgresql.org>`_ is used as the database. Further details
about the code and technology can be found in the different documents in the
docs directory.

Content
-------
A fair amount of the content pages of the website are just static HTML templates.
If you wish to edit these, you only need to look at the templates/pages/
subdirectory. The content in here is simple HTML, and can be edited as such.

Contributing
------------
We appreciate all (most?) contributions to this project. If you wish to
contribute, be sure to sign up to the `pgsql-www <https://www.postgresql.org/list/>`_
mailinglist for any discussions, and post any suggested patches there. If you
want to make any major changes, be sure to have discussed those on the list first.

Licence
-------
The code for the website is licensed under
`The PostgreSQL Licence <http://www.opensource.org/licenses/postgresql>`_, which is
closely related to the BSD licence.
