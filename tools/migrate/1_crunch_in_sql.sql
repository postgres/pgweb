\set ON_ERROR_STOP 1
BEGIN;

SET CONSTRAINTS ALL DEFERRED;

/* we need a user to map to */
INSERT INTO auth_user (id, username, first_name, last_name, email, password, is_staff, is_active, is_superuser, last_login, date_joined)
SELECT 
	0, '__migrated__', 'Migrated', 'Connection', 'migrated@postgresql.org',
	'$sha1$thereisnopasswordforthisuser', 'f', 'f', 'f', '1900-01-01', '1900-01-01'
WHERE NOT EXISTS (SELECT * FROM auth_user WHERE id=0);

/* feature matrix */
TRUNCATE TABLE featurematrix_featuregroup RESTART IDENTITY CASCADE;

INSERT INTO featurematrix_featuregroup(id, groupname, groupsort)
 SELECT groupid, groupname, groupsort FROM oldweb.features_groups;

/* for each version */
INSERT INTO featurematrix_feature (id, group_id, featurename, featuredescription,
	v74, v80, v81, v82, v83, v84, v85)
 SELECT
  f.featureid, f.groupid, f.featurename, COALESCE(f.featuredescription,''),
  COALESCE(f74.state, 0),
  COALESCE(f80.state, 0),
  COALESCE(f81.state, 0),
  COALESCE(f82.state, 0),
  COALESCE(f83.state, 0),
  COALESCE(f84.state, 0),
  COALESCE(f85.state, 0)
 FROM oldweb.features_features f
 LEFT JOIN oldweb.features_matrix f74 ON (f.featureid = f74.feature AND f74.version=1)
 LEFT JOIN oldweb.features_matrix f80 ON (f.featureid = f80.feature AND f80.version=2)
 LEFT JOIN oldweb.features_matrix f81 ON (f.featureid = f81.feature AND f81.version=3)
 LEFT JOIN oldweb.features_matrix f82 ON (f.featureid = f82.feature AND f82.version=4)
 LEFT JOIN oldweb.features_matrix f83 ON (f.featureid = f83.feature AND f83.version=5)
 LEFT JOIN oldweb.features_matrix f84 ON (f.featureid = f84.feature AND f84.version=6)
 LEFT JOIN oldweb.features_matrix f85 ON (f.featureid = f85.feature AND f85.version=6)
;

SELECT setval('featurematrix_feature_id_seq', max(id)) FROM featurematrix_feature;
SELECT setval('featurematrix_featuregroup_id_seq', max(id)) FROM featurematrix_featuregroup;

-- copy of the users table, we need it to migrate users
CREATE TABLE public.users_old AS SELECT * FROM oldweb.users;

-- stackbuilder!
-- First, let's get the apps, minus dependencies
INSERT INTO downloads_stackbuilderapp (textid, version, platform, name,
	active, description, category, pgversion, edbversion, format,
	installoptions, upgradeoptions, checksum, mirrorpath, alturl, versionkey)
SELECT
	id, version, platform, name,
	active, description, category, pgversion, edbversion, format,
	installoptions, upgradeoptions, checksum, mirrorpath, alturl, versionkey
FROM oldweb.applications;
-- add dependencies. There is only those on edb_apachephp, so hardcode that because
-- it makes life a *lot* easier
INSERT INTO downloads_stackbuilderapp_dependencies (from_stackbuilderapp_id, to_stackbuilderapp_id)
SELECT
  o.id, n.id
FROM oldweb.applications a
inner join downloads_stackbuilderapp o ON (a.id=o.textid AND a.version=o.version AND a.platform=o.platform)
inner join downloads_stackbuilderapp n ON (n.platform=o.platform and n.textid='edb_apachephp')
where not dependencies='{}';



--
-- Document comments
INSERT INTO docs_doccomment (id, version, file, comment, posted_at, submitter_id, approved)
SELECT
 id, version, file, comment, posted_at, 0, approved
FROM oldweb.comments WHERE NOT (processed and not approved);
SELECT setval('docs_doccomment_id_seq', max(id)) FROM docs_doccomment;

-- Clear out all organisations and all attached objects (yes, this clears out a lot of stuff)
TRUNCATE TABLE core_organisation RESTART IDENTITY CASCADE;
TRUNCATE TABLE core_organisationtype RESTART IDENTITY CASCADE;

-- Load the types
COPY core_organisationtype (id, typename) FROM stdin;
1	Open Source Project
2	Individual
3	Not for profit
4	Company
\.
SELECT setval('core_organisationtype_id_seq', 5);

-- Migration record
INSERT INTO core_organisation (id, name, approved, address, url, email, phone, orgtype_id, lastconfirmed)
VALUES (0, '_migrated', 't', '', '', '', '', 4, CURRENT_TIMESTAMP);

-- Existing organisations
INSERT INTO core_organisation (name, approved, address, url, email, phone, orgtype_id, lastconfirmed)
SELECT name, approved, COALESCE(address,''), COALESCE(url,''), COALESCE(email,''), COALESCE(phone,''), 
CASE WHEN orgtype='i' THEN 2 WHEN orgtype='p' THEN 1 WHEN orgtype='c' THEN 4 WHEN orgtype='n' THEN 3 END,
lastconfirmed
FROM oldweb.organisations;

-- Create organisations to map events to!
-- First, we need to clear out any non-organisations to mape them to something
UPDATE oldweb.events SET organisation='' WHERE organisation IS NULL;
INSERT INTO core_organisation (name, approved, address, url, email, phone, orgtype_id, lastconfirmed)
SELECT DISTINCT organisation, 't'::boolean, '', '', '', '', 4, CURRENT_TIMESTAMP FROM oldweb.events
WHERE organisation NOT IN (SELECT name FROM core_organisation);

-- Create professional services entries for organisations
INSERT INTO core_organisation (name, approved, address, url, email, phone, orgtype_id, lastconfirmed)
SELECT name, 't'::boolean, '', max(COALESCE(url,'')), max(COALESCE(email,'')), '', 4, max(lastconfirmed) FROM oldweb.profserv
WHERE name NOT IN (SELECT name FROM core_organisation)
GROUP BY name;

-- Add _migrated as manager of all organisations that don't have one set
INSERT INTO core_organisation_managers (organisation_id, user_id)
SELECT id, 0 FROM core_organisation
WHERE id NOT IN (SELECT organisation_id FROM core_organisation_managers);

-- Add professional services
INSERT INTO profserv_professionalservice (submitter_id, approved, organisation_id, description, employees, locations,
region_africa,region_asia,region_europe,region_northamerica,region_oceania,region_southamerica,
hours,languages,customerexample,experience,contact,url,provides_support,provides_hosting,interfaces)
SELECT 0, approved, (SELECT id FROM core_organisation WHERE core_organisation.name=profserv.name), description, employees, locations,
region_africa,region_asia,region_europe,region_northamerica,region_oceania,region_southamerica,
hours,languages,customerexample,experience,contact,url,provides_support,provides_hosting,interfaces
FROM oldweb.profserv;

-- Add product categories and license types
TRUNCATE TABLE downloads_category RESTART IDENTITY CASCADE;
TRUNCATE TABLE downloads_licencetype RESTART IDENTITY CASCADE;
INSERT INTO downloads_category (catname, blurb) SELECT name,blurb FROM oldweb.product_categories ORDER BY id;
COPY downloads_licencetype (id, typename) FROM stdin;
1	Open source
2	Freeware
3	Commercial
4	Multiple
\.
SELECT setval('downloads_category_id_seq', 5);

-- Add products
INSERT INTO downloads_product (name, approved, publisher_id, url, category_id, licencetype_id, description, price, lastconfirmed)
SELECT products.name, products.approved, 
(SELECT id FROM core_organisation WHERE core_organisation.name=oo.name),
products.url,
(SELECT id FROM downloads_category WHERE downloads_category.catname=oldweb.product_categories.name),
(SELECT id FROM downloads_licencetype WHERE typename=CASE WHEN licence='o' THEN 'Open source' WHEN licence='c' THEN 'Commercial' WHEN licence='f' THEN 'Freeware' WHEN licence='m' THEN 'Multiple' END),
description, COALESCE(price,'') , products.lastconfirmed
FROM oldweb.products
INNER JOIN oldweb.organisations oo ON publisher=oo.id
INNER JOIN oldweb.product_categories ON category=product_categories.id;