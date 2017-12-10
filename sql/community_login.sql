--
-- View that shows the ssh keys, used by services that need them
-- (currently just git)
-- We know we can't have the same user in both the old and the new
-- table, so not doing any magic around that works fine.
--
CREATE OR REPLACE VIEW users_keys AS
    SELECT auth_user.username AS userid,
    	   core_userprofile.sshkey,
	   core_userprofile.lastmodified AS sshkey_last_update
    FROM auth_user
    JOIN core_userprofile ON auth_user.id = core_userprofile.user_id 
    WHERE core_userprofile.sshkey <> ''::text
    UNION
    SELECT users_old.userid,
    	   users_old.sshkey,
	   users_old.sshkey_last_update
    FROM users_old
    WHERE users_old.sshkey IS NOT NULL
    AND users_old.sshkey <> ''::text
    AND NOT EXISTS (SELECT * FROM auth_user a WHERE a.username=users_old.userid)
;
