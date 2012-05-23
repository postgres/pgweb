--
-- tables created for compatibility with migration from old system.
-- Once we drop migration support they can be removed, but for now
-- dummies are required for functions to work.
--
CREATE TABLE users_old (
    userid character varying(16),
    fullname character varying(128),
    authorblurb text,
    email character varying(128),
    communitydoc_superuser integer,
    created timestamp with time zone,
    lastlogin timestamp with time zone,
    matrixeditor integer,
    pwdhash text,
    resethash text,
    resethashtime timestamp with time zone,
    sshkey text,
    sshkey_last_update timestamp with time zone
);
