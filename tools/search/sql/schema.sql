CREATE TABLE lists (
   id int NOT NULL PRIMARY KEY,
   name varchar(64) NOT NULL,
   active bool NOT NULL,
   pagecount int NOT NULL
);

CREATE TABLE messages (
   list int NOT NULL REFERENCES lists(id) ON DELETE CASCADE,
   year int NOT NULL,
   month int NOT NULL,
   msgnum int NOT NULL,
   date timestamptz NOT NULL,
   subject varchar(128) NOT NULL,
   author varchar(128) NOT NULL,
   txt text NOT NULL,
   fti tsvector NOT NULL
);
ALTER TABLE messages ADD CONSTRAINT pk_messages PRIMARY KEY (list,year,month,msgnum);


CREATE TABLE sites (
   id int NOT NULL PRIMARY KEY,
   hostname text NOT NULL UNIQUE,
   description text NOT NULL,
   pagecount int NOT NULL
);

CREATE TABLE webpages (
   site int NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
   suburl varchar(512) NOT NULL,
   title varchar(128) NOT NULL,
   relprio float NOT NULL DEFAULT 0.5,
   lastscanned timestamptz NULL,
   txt text NOT NULL,
   fti tsvector NOT NULL
);
ALTER TABLE webpages ADD CONSTRAINT pk_webpages PRIMARY KEY (site, suburl);

CREATE TABLE site_excludes (
   site int NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
   suburlre varchar(512) NOT NULL
);
ALTER TABLE site_excludes ADD CONSTRAINT pk_site_excludes PRIMARY KEY (site,suburlre);

