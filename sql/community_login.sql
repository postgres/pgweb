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
BEGIN
   SELECT
     lower(auth_user.username),
     trim(auth_user.first_name || ' ' || auth_user.last_name),
     auth_user.email,
     '', -- we don't do authorblurbs anymore, but the API has them...
     0, -- we don't do communitydoc_superuser either...
     last_login,
     0 -- nor do we do matrix editor
   INTO userid_p,fullname,email,authorblurb,communitydoc_superuser,_last_login,matrixeditor
   FROM auth_user WHERE
     lower(auth_user.username) = lower(userid_p) AND
     encode(pgcrypto.digest(split_part(auth_user.password, '$', 2) || password_p, 'sha1'), 'hex') =
       split_part(auth_user.password, '$', 3);
   IF FOUND THEN
      success := 1;
      UPDATE auth_user SET last_login=CURRENT_TIMESTAMP WHERE auth_user.username=userid_p;
   ELSE
      success := 0;
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
  OUT matrixeditor integer) 
RETURNS record
AS $$
BEGIN
   SELECT users_old.userid,users_old.fullname,users_old.email,users_old.authorblurb,users_old.communitydoc_superuser,users_old.lastlogin,users_old.matrixeditor
     INTO userid_p,fullname,email,authorblurb,communitydoc_superuser,last_login,matrixeditor
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
