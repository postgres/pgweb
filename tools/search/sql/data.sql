INSERT INTO sites (id, hostname, description, pagecount)
 VALUES (1, 'www.postgresql.org', 'Main PostgreSQL Website', 0);

INSERT INTO sites (id, hostname, description, pagecount)
 VALUES (2, 'www.pgadmin.org','pgAdmin III', 0);

INSERT INTO sites (id, hostname, description, pagecount)
 VALUES (3, 'jdbc.postgresql.org','JDBC driver', 0);


INSERT INTO site_excludes VALUES (2,'^/archives');
INSERT INTO site_excludes VALUES (2,'^/docs/dev');
INSERT INTO site_excludes VALUES (2,'^/docs/1.4');
INSERT INTO site_excludes VALUES (2,'^/docs/[^/]+/pg');
INSERT INTO site_excludes VALUES (2,'^/snapshots');
INSERT INTO site_excludes VALUES (3,'^/development');
INSERT INTO site_excludes VALUES (3,'^/\.\./');
INSERT INTO site_excludes VALUES (3,'\.tar\.');
INSERT INTO site_excludes VALUES (3,'\.jar');
INSERT INTO site_excludes VALUES (3,'\.tgz');
