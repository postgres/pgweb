Frontend & Backend
==================
The postgresql.org website is designed to run in a frontend/backend
scenario. This is to achieve both load distribution and redundancy for
the case when the main webserver (known as wwwmaster) goes offline or
becomes loaded.

Previous versions of the website used static files on the frontend,
that were spidered at regular intervals and then push-rsynced out to
the frontends. This made the frontends entirely independent of the
backends, and as such very "available". Unfortunately it made a lot of
coding difficult, and had very bad performance (a re-spidering
including documentation and ftp would take more than 6 hours on a fast
machine).

This generation of the website will instead rely on a varnish web
cache running on the frontend servers, configured to cache things for
a long time. It will also run in what's known as "grace mode", which
will have varnish keep serving the content from the cache even if it
has expired in case the backend cannot be contacted.

All forms that require login will be processed directly by the master
server, just like before. These will *always* be processed over SSL,
and as such not sent through varnish at all. They will still be
accessed using the domain www.postgresql.org, which will then simply
proxy the SSL connection to the backend. For the initial deployment
we'll just use HAProxy, but we may switch to a more feature-rich
proxy server in the future - in which case it's important to maintain
the encrypted channel between the frontend and the backend, since
they are normally not in the same datacenter.

Requests that require *up to the second* content but do *not* require
a login, such as a mirror selection, will be sent through the
frontends (and served under the www.postgresql.org name) but without
caching enabled. Note that in most cases, these should actually be
cached for at least 5 or 10 seconds, to cut off any short term high
load effects (aka the slashdot effect).

Normal requests are always cached. There is a default cache expiry
that is set on all pages. There is a longer default policy set for
images, because they are considered never to change. Any view in the
django project can override this default, by specifying the
"Cache-control: s-maxage=xxx" http header on the response. This is
done by using the @cache() decorator on the view method. Caching
should be kept lower for pages that have frequently updating data,
such as the front page or the survey results page.

Any model inheriting from PgModel can define a tuple or a function
called *purge_urls* (if it's a function, it will be called and
should return a tuple or a generator). Each entry is a regular
expression, and this data will be automatically removed from the
frontend caches whenever this object changes. The regular expression
will always be prepended with ^, and should be rooted with /.
It should be made as restrictive as possible (for example, don't
purge "/" since that will remove everything from the cache completely).
This makes it possible to have frontends react instantly to changes,
while maintaining high cacheability.

Finally, there is a form on the admin web interface that lets the
administrator manually purge pages from the caches. This may be
necessary if changes have been made to static pages and/or site
structure that otherwise wouldn't show up until the cache has
expired.
