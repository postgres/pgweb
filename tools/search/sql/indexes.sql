DROP INDEX IF EXISTS messages_date_idx;
CREATE INDEX messages_date_idx ON messages(date);

DROP INDEX IF EXISTS webpages_fti_idx;
CREATE INDEX webpages_fti_idx ON webpages USING gin(fti);
ANALYZE webpages;

DROP INDEX IF EXISTS messages_fti_idx;
CREATE INDEX messages_fti_idx ON messages USING gin(fti);
ANALYZE messages;
