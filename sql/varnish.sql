BEGIN;

--
-- Create a function to purge from varnish cache
-- By default this adds the object to a pgq queue,
-- but this function can be replaced with a void one
-- when running a development version.
--

CREATE OR REPLACE FUNCTION varnish_purge(url text)
RETURNS bigint
AS $$
   SELECT pgq.insert_event('varnish', 'P', $1);
$$ LANGUAGE 'sql';

CREATE OR REPLACE FUNCTION varnish_purge_expr(expr text)
RETURNS bigint
AS $$
  SELECT pgq.insert_event('varnish', 'X', $1);
$$ LANGUAGE 'sql';
COMMIT;