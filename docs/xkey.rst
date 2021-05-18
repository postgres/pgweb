xkey keys
=========
xkey keys are used to do smart Varnish purging. A single key can be
assigned to multiple pages, and when the key is purged all those pages
are purged at the same time.

The following xkeys are in use (more to come in the future probably)

pgwt_<hash>
  These keys are automatically assigned based on the md5 of the
  template(s) in use on the page. One xkey is added for each template,
  so a typical page has a set of them. This makes purging fully
  automatic when a template is updated -- the system will
  automatically figure out which templates are changed and purge the
  corresponding hashes.
pgdocs_current
  Set on all documentation pages that are in the current version at
  the time of setting.
pgdocs_all
  Set on documentation pages that are cross-version, such as index pages.
pgdocs_<version>
  Set on documentation of the specified version.
pgdocs_pdf
  Set on documentation pages that reference the existance or size of
  documentation PDFs.
