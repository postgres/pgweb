BEGIN;

--
-- Log the user in, using the django auth system
--
CREATE OR REPLACE FUNCTION community_login(INOUT userid_p text, password_p text,
  OUT success integer, OUT fullname text, OUT email text, OUT authorblurb text,
  OUT communitydoc_superuser integer, OUT _last_login timestamp with time zone,
  OUT matrixeditor integer) 
RETURNS record
AS $$
DECLARE
   stored_userid text;
   stored_fullname text;
   stored_email text;
   stored_lastlogin timestamptz;
   stored_pwd text;
BEGIN
   -- Lecagy parameters from previous versions
   authorblurb := '';
   communitydoc_superuser := 0;
   matrixeditor := 0;

   -- Look for user
   SELECT
     lower(auth_user.username),
     trim(auth_user.first_name || ' ' || auth_user.last_name),
     auth_user.email,
     last_login,
     auth_user.password
   INTO stored_userid,stored_fullname,stored_email,stored_lastlogin,stored_pwd
   FROM auth_user WHERE
     lower(auth_user.username) = lower(userid_p);
   IF FOUND THEN
      -- User exists, verify password
     IF encode(pgcrypto.digest(split_part(stored_pwd, '$', 2) || password_p, 'sha1'), 'hex') = split_part(stored_pwd, '$', 3) THEN
         success := 1;
	 userid_p := stored_userid;
	 fullname := stored_fullname;
	 email := stored_email;
	 _last_login := stored_lastlogin;
         UPDATE auth_user SET last_login=CURRENT_TIMESTAMP WHERE auth_user.username=stored_userid;
     ELSE
     -- User exists, but wrong password
        success := 0;
     END IF;
   ELSE
     -- User does not exist, look it up in the old system.
     -- XXX: we don't support migrating users yet, should we? currently
     -- they are only migrated when they log into the main website.
     SELECT users_old.userid,users_old.fullname,users_old.email,users_old.lastlogin
     INTO stored_userid,stored_fullname,stored_email,stored_lastlogin
     FROM users_old WHERE lower(users_old.userid)=lower(userid_p) AND
     substring(users_old.pwdhash, 30) = pgcrypto.crypt(password_p, substring(users_old.pwdhash, 1, 29));
     IF FOUND THEN
         success := 1;
	 userid_p := stored_userid;
	 fullname := stored_fullname;
	 email := stored_email;
	 _last_login := stored_lastlogin;
         UPDATE users_old SET lastlogin=CURRENT_TIMESTAMP WHERE users_old.userid=stored_userid;
     ELSE
        success := 0;
     END IF;
   END IF;
END
$$
LANGUAGE 'plpgsql' SECURITY DEFINER;


--
-- Create new user - not implemented
--
CREATE OR REPLACE FUNCTION community_login_create(_userid text, _password text, _fullname text, _email text)
RETURNS boolean
AS $$
	SELECT 'f'::boolean;
$$ LANGUAGE 'sql';

--
-- Check if a user exists
--
CREATE OR REPLACE FUNCTION community_login_exists(userid text)
RETURNS boolean
AS $$
   SELECT EXISTS (SELECT * FROM auth_user WHERE username=$1);
$$ LANGUAGE 'sql';

--
-- Update user information - not implemented, edits should be through website
--
CREATE OR REPLACE FUNCTION community_login_setinfo(_userid text, _password text,
  _fullname text, _email text, _authorblurb text)
RETURNS boolean
AS $$
   SELECT 'f'::boolean
$$ LANGUAGE 'sql';

--
-- Change user password - not implemented, edits should be through website
--
CREATE OR REPLACE FUNCTION community_login_setpassword(_userid text, _password text)
RETURNS boolean
AS $$
   SELECT 'f'::boolean;
$$ LANGUAGE 'sql';

--
-- Replica of the old login functionality. Only used so we can migreate the user
--
CREATE OR REPLACE FUNCTION community_login_old(INOUT userid_p text, password_p text,
  OUT success integer, OUT fullname text, OUT email text, OUT authorblurb text,
  OUT communitydoc_superuser integer, OUT last_login timestamp with time zone,
  OUT matrixeditor integer, OUT sshkey text) 
RETURNS record
AS $$
BEGIN
   SELECT users_old.userid,users_old.fullname,users_old.email,users_old.authorblurb,users_old.communitydoc_superuser,users_old.lastlogin,users_old.matrixeditor,users_old.sshkey
     INTO userid_p,fullname,email,authorblurb,communitydoc_superuser,last_login,matrixeditor, sshkey
     FROM users_old WHERE lower(users_old.userid)=lower(userid_p) AND
     substring(users_old.pwdhash, 30) = pgcrypto.crypt(password_p, substring(users_old.pwdhash, 1, 29));
-- bf salts are always 29 chars!
   IF FOUND THEN
      success := 1;
   ELSE
      success := 0;
   END IF;
END
$$
LANGUAGE plpgsql SECURITY DEFINER;

--
-- Delete an account from the old system
--
CREATE OR REPLACE FUNCTION community_login_old_delete(userid text)
RETURNS void
AS $$
 DELETE FROM users_old WHERE userid=$1;
$$
LANGUAGE sql;

COMMIT;


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
    AND users_old.sshkey <> ''::text;
