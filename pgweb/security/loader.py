from django.db import connection, transaction

import json
import os
import glob


@transaction.atomic
def load_security_json():
    combined_json = list(_load_all_cve_json())
    with open('/tmp/cna/full.json', 'w') as f:
        json.dump(combined_json, f)
    curs = connection.cursor()
    curs.execute("""WITH t AS (
SELECT (regexp_match(cveid, '^CVE-(\\d{4}-\\d{4,5})$'))[1] AS cve, title, description, vector, fixed, component
FROM JSON_TABLE(%(j)s::json, '$[*]' COLUMNS (
  cveid text PATH '$.cveMetadata.cveId' ERROR ON EMPTY ERROR ON ERROR,
  title text PATH '$.containers.cna.title' ERROR ON EMPTY ERROR ON ERROR,
  description text PATH '$.containers.cna.descriptions[*] ? (@.lang == "en").value' ERROR ON EMPTY ERROR ON ERROR,
  vector text PATH '$.containers.cna.metrics[*] ? (exists(@.cvssV3_1)).cvssV3_1.vectorString' ERROR ON EMPTY ERROR ON ERROR,
  fixed text[] PATH '$.containers.cna.affected.versions[*].lessThan.number()' WITH ARRAY WRAPPER ERROR ON EMPTY ERROR ON ERROR,
  component text PATH '$.containers.cna.x_postgresql.component' DEFAULT 'core server' ON EMPTY ERROR ON ERROR
)) jt
),
cveload AS (
  MERGE INTO security_securitypatch p
  USING t ON t.cve=p.cve
  WHEN NOT MATCHED THEN
    INSERT (cve, description, details, component, public, detailslink, legacyscore, vector)
    VALUES (cve, title, description, component, true, '', 0, vector)
  WHEN MATCHED AND (p.description != title OR p.details != t.description OR p.component != t.component) THEN
    UPDATE SET description = t.title, details = t.description, component=t.component
  WHEN NOT MATCHED BY SOURCE AND cve > '2025-' THEN
    DELETE
  RETURNING p.cve, merge_action() AS action, id
),
allversions AS (
  SELECT t.cve, version, core_version.id AS versionid, tree, split_part(version, '.', 2)::int AS fixedminor, COALESCE(p.id, cveload.id) AS patchid
  FROM t
  INNER JOIN LATERAL unnest(fixed) version ON true
  INNER JOIN core_version ON core_version.tree=split_part(version, '.', 1)::int
  LEFT JOIN security_securitypatch p ON t.cve=p.cve
  LEFT JOIN cveload ON t.cve=cveload.cve
),
versionload AS (
  MERGE INTO security_securitypatchversion pv
  USING allversions ON patchid=patch_id AND versionid=version_id
  WHEN MATCHED AND (fixedminor != fixed_minor) THEN
    UPDATE SET fixed_minor=fixedminor
  WHEN NOT MATCHED THEN
    INSERT (patch_id, version_id, fixed_minor)
    VALUES (patchid, versionid, fixedminor)
  WHEN NOT MATCHED BY SOURCE AND patch_id > (SELECT min(id) FROM security_securitypatch WHERE cvenumber > 202500000) THEN
    DELETE
  RETURNING COALESCE(cve, (SELECT cve FROM security_securitypatch WHERE id=patch_id)) AS cve,
            merge_action() AS action,
            CASE WHEN merge_action() = 'DELETE' THEN (SELECT tree::int::text FROM core_version WHERE id=version_id) ELSE tree::int::text END AS tree,
            fixed_minor
),
varnishpurge AS (
  SELECT '/support/security/CVE-' || cve || '/' AS url FROM cveload
  UNION
  SELECT '/support/security/CVE-' || cve || '/' FROM versionload
  UNION
  SELECT '/support/security/' || tree::text || '/' FROM versionload
),
summary AS (
  SELECT cve, action || ' CVE' AS what FROM cveload
  UNION ALL
  SELECT cve, action || ' version ' || tree || '.' || fixed_minor FROM versionload
  UNION ALL
  SELECT 'Purged', n|| ' urls' FROM (SELECT count(*) AS n FROM (SELECT varnish_purge(url) FROM varnishpurge)) WHERE n > 0
)
SELECT cve, array_agg(what ORDER BY what)
FROM summary
GROUP BY cve
ORDER BY 1
""", {'j': json.dumps(combined_json)})
    for cve, what in curs.fetchall():
        print("CVE-{}".format(cve))
        for w in what:
            print("   {}".format(w))


def _load_all_cve_json():
    for fn in glob.glob(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/security/cve/CVE-*.json'))):
        with open(fn) as f:
            # We should only have PostgreSQL entries here, but filter to be sure
            j = json.load(f)
            if j['containers']['cna']['affected'][0]['product'] == 'PostgreSQL':
                yield j
            else:
                print("File {} is not for PostgreSQL, it's for {}".format(fn, j['containers']['cna']['affected'][0]['product']))
