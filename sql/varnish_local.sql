BEGIN;

--
-- "cheating" version of the varnish_purge() function
-- that can be used on a local installation that doesn't
-- have any frontends.
--

CREATE OR REPLACE FUNCTION varnish_purge(url text)
RETURNS bigint
AS $$
   SELECT 1::bigint;
$$ LANGUAGE 'sql';

CREATE OR REPLACE FUNCTION varnish_purge_expr(url text)
RETURNS bigint
AS $$
   SELECT 1::bigint;
$$ LANGUAGE 'sql';

COMMIT;