The PostgreSQL website
======================

The code in this repository is what backs the website at www.postgresql.org.

The authoritative repository for this code is on git.postgresql.org, but it's
free to be mirrored anywhere.

Technology
----------
The website code is written in `Python <https://www.python.org>`_ using
the `Django <https://www.djangoproject.com/>`_ framework. Not surprisingly,
`PostgreSQL <https://www.postgresql.org>`_ is used as the database. Further details
about the code and technology can be found in the different documents in the
docs directory.

The website also uses the `Bootstrap <https://getbootstrap.com/>`_ CSS framework
as well as the `Font Awesome <https://fontawesome.com/>`_ icon library.

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
`The PostgreSQL Licence <https://www.opensource.org/licenses/postgresql>`_, which is
closely related to the BSD licence.

Django is released under its `BSD Licence <https://github.com/django/django/blob/master/LICENSE>`_.

Bootstrap is released under the `MIT Licence <https://github.com/twbs/bootstrap/blob/master/LICENSE>`_.
and includes the following software as well:

- jQuery & jQuery UI under the `MIT Licence <https://jquery.org/license/>`_
- Popper under the `MIT Licence <https://github.com/FezVrasta/popper.js/blob/master/LICENSE.md>`_

Font Awesome has a `combination of licences <https://fontawesome.com/license>`_:

The code of Font Awesome is released under the `MIT Licence <https://opensource.org/licenses/MIT>`_.
The icons of Font Awesome are released under the `CC BY 4.0 Licence <https://creativecommons.org/licenses/by/4.0/>`_.
The fonts of Font Awesome are released under the `SIL OFL 1.1 License <http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL>`_.

jQuery.matchHeight.js uses the `MIT Licence <https://github.com/liabru/jquery-match-height/blob/master/LICENSE>`_
normalize.css uses the `MIT License <https://github.com/necolas/normalize.css/blob/master/LICENSE.md>`_
