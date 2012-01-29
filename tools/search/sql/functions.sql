CREATE OR REPLACE FUNCTION archives_search(query text, _lists int, firstdate timestamptz, lastdate timestamptz, startofs int, hitsperpage int, sort char)
RETURNS TABLE (listname text, year int, month int, msgnum int, date timestamptz, subject text, author text, headline text, rank float)
AS $$
DECLARE
   tsq tsquery;
   qry text;
   hits int;
   hit RECORD;
   curs refcursor;
   pagecount int;
   listary int[];
BEGIN
   tsq := plainto_tsquery(query);
   IF numnode(tsq) = 0 THEN
      RETURN QUERY SELECT NULL::text, 0, 0, NULL::int, NULL::timestamptz, NULL::text, NULL::text, NULL::text, NULL:: float;
      RETURN;
   END IF;

   hits := 0;

   IF _lists IS NULL THEN
      SELECT INTO pagecount sum(lists.pagecount) FROM lists;
      IF sort = 'd' THEN
         OPEN curs FOR SELECT m.list,m.year,m.month,m.msgnum,ts_rank_cd(m.fti,tsq) FROM messages m WHERE m.fti @@ tsq AND m.date>COALESCE(firstdate,'1900-01-01') ORDER BY m.date DESC LIMIT 1000;
      ELSE
         OPEN curs FOR SELECT m.list,m.year,m.month,m.msgnum,ts_rank_cd(m.fti,tsq) FROM messages m WHERE m.fti @@ tsq AND m.date>COALESCE(firstdate,'1900-01-01') ORDER BY ts_rank_cd(m.fti,tsq) DESC LIMIT 1000;
      END IF;
   ELSE
      IF _lists < 0 THEN
         SELECT INTO listary ARRAY(SELECT id FROM lists WHERE grp=-_lists);
      ELSE
         listary = ARRAY[_lists];
      END IF;
      SELECT INTO pagecount sum(lists.pagecount) FROM lists WHERE id=ANY(listary);
      IF sort = 'd' THEN
         OPEN curs FOR SELECT m.list,m.year,m.month,m.msgnum,ts_rank_cd(m.fti,tsq) FROM messages m WHERE (m.list=ANY(listary)) AND m.fti @@ tsq AND m.date>COALESCE(firstdate,'1900-01-01') ORDER BY m.date DESC LIMIT 1000;
      ELSE
         OPEN curs FOR SELECT m.list,m.year,m.month,m.msgnum,ts_rank_cd(m.fti,tsq) FROM messages m WHERE (m.list=ANY(listary)) AND m.fti @@ tsq AND m.date>COALESCE(firstdate,'1900-01-01') ORDER BY ts_rank_cd(m.fti,tsq) DESC LIMIT 1000;
      END IF;
   END IF;
   LOOP
      FETCH curs INTO hit;
      IF NOT FOUND THEN
         EXIT;
      END IF;
      hits := hits+1;
      IF (hits < startofs+1) OR (hits > startofs + hitsperpage) THEN
         CONTINUE;
      END IF;
      RETURN QUERY SELECT lists.name::text, hit.year, hit.month, hit.msgnum, messages.date, messages.subject::text, messages.author::text, ts_headline(messages.txt,tsq,'StartSel="[[[[[[",StopSel="]]]]]]"'), hit.ts_rank_cd::float FROM messages INNER JOIN lists ON messages.list=lists.id WHERE messages.list=hit.list AND messages.year=hit.year AND messages.month=hit.month AND messages.msgnum=hit.msgnum;
   END LOOP;

   listname := NULL; msgnum := NULL; date := NULL; subject := NULL; author := NULL; headline := NULL; rank := NULL;
   year=hits;
   month=pagecount;
   RETURN NEXT;
END;
$$
LANGUAGE 'plpgsql';
ALTER FUNCTION archives_search(text, int, timestamptz, timestamptz, int, int, char) SET default_text_search_config = 'public.pg';


CREATE OR REPLACE FUNCTION site_search(query text, startofs int, hitsperpage int, allsites bool, _suburl text)
RETURNS TABLE (siteid int, baseurl text, suburl text, title text, headline text, rank float)
AS $$
DECLARE
    tsq tsquery;
    qry text;
    hits int;
    hit RECORD;
    curs refcursor;
    pagecount int;
BEGIN
    tsq := plainto_tsquery(query);
    IF numnode(tsq) = 0 THEN
        siteid = 0;baseurl=NULL;suburl=NULL;title=NULL;headline=NULL;rank=0;
        RETURN NEXT;
        RETURN;
    END IF;

    hits := 0;

    IF allsites THEN
        SELECT INTO pagecount sum(sites.pagecount) FROM sites;
        OPEN curs FOR SELECT sites.id AS siteid, sites.baseurl, webpages.suburl, ts_rank_cd(fti,tsq) FROM webpages INNER JOIN sites ON webpages.site=sites.id WHERE fti @@ tsq ORDER BY ts_rank_cd(fti,tsq) DESC LIMIT 1000;
    ELSE
        SELECT INTO pagecount sites.pagecount FROM sites WHERE id=1;
        IF _suburl IS NULL THEN
            OPEN curs FOR SELECT sites.id AS siteid, sites.baseurl, webpages.suburl, ts_rank_cd(fti,tsq) FROM webpages INNER JOIN sites ON webpages.site=sites.id WHERE fti @@ tsq AND site=1 ORDER BY ts_rank_cd(fti,tsq) DESC LIMIT 1000;
        ELSE
            OPEN curs FOR SELECT sites.id AS siteid, sites.baseurl, webpages.suburl, ts_rank_cd(fti,tsq) FROM webpages INNER JOIN sites ON webpages.site=sites.id WHERE fti @@ tsq AND site=1 AND webpages.suburl LIKE _suburl||'%' ORDER BY ts_rank_cd(fti,tsq) DESC LIMIT 1000;
        END IF;
    END IF;
    LOOP
       FETCH curs INTO hit;
       IF NOT FOUND THEN
          EXIT;
       END IF;
       hits := hits+1;
       IF (hits < startofs+1) OR (hits > startofs+hitsperpage) THEN
          CONTINUE;
       END IF;
       RETURN QUERY SELECT hit.siteid, hit.baseurl::text, hit.suburl::text, webpages.title::text, ts_headline(webpages.txt,tsq,'StartSel="[[[[[[",StopSel="]]]]]]"'), hit.ts_rank_cd::float FROM webpages WHERE webpages.site=hit.siteid AND webpages.suburl=hit.suburl;
    END LOOP;
    RETURN QUERY SELECT pagecount, NULL::text, NULL::text, NULL::text, NULL::text, pagecount::float;
END;
$$
LANGUAGE 'plpgsql';
ALTER FUNCTION site_search(text, int, int, bool, text) SET default_text_search_config = 'public.pg';