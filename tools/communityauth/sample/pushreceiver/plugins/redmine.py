import psycopg2


class ReceiverPlugin:
    def __init__(self, config):
        self.config = config
        self.conn = None

    def __enter__(self):
        # Connect to the db
        self.conn = psycopg2.connect(self.config.get('redmine', 'connstr'))
        self.curs = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            # No exception -> commit
            self.conn.commit()
        else:
            # Any exception at all means we roll back the whole things
            self.conn.rollback()

        self.conn.close()
        self.conn = None

    def push_user(self, user):
        # Redmine keeps the email address in a separate table, which is annoying. So we have to deal with the user and the
        # email separately.
        self.curs.execute("SELECT id, firstname, lastname FROM users WHERE login=%(username)s", {
            'username': user['username'],
        })
        if not self.curs.rowcount:
            # This user didn't exist
            return

        id, firstname, lastname = self.curs.fetchone()

        if firstname != user['firstname'] or lastname != user['lastname']:
            self.curs.execute("UPDATE users SET firstname=%(firstname)s, lastname=%(lastname)s, updated_on=now() WHERE id=%(id)s", {
                'id': id,
                'firstname': user['firstname'],
                'lastname': user['lastname'],
            })
            print("Updated name of user {}".format(user['username']))

        # Now figure out the email. To make things clean, we start by removing all secondary email addresses
        self.curs.execute("DELETE FROM email_addresses WHERE user_id=%(id)s AND NOT is_default", {
            'id': id,
        })

        # There can now either exist or not exist a primary address (in theory more than one, but presumably redmine makes
        # sure this can't happen at the app layer). Since the table lacks a primary key, we can't use INSERT ON CONFLICT,
        # and instead have to read the whole thing back to check.
        self.curs.execute("SELECT id, address FROM email_addresses WHERE user_id=%(id)s", {
            'id': id,
        })
        if self.curs.rowcount == 0:
            # No existing address? So add one!
            self.curs.execute("INSERT INTO email_addresses (user_id, address, is_default, created_on, updated_on) VALUES (%(id)s, %(address)s, true, now(), now())", {
                'id': id,
                'address': user['email'],
            })
            print("Added email address to {}".format(user['username']))
        elif self.curs.rowcount == 1:
            # Existing address that may have changed
            addrid, address = self.curs.fetchone()
            if address != user['email']:
                self.curs.execute("UPDATE email_addresses SET address=%(address)s, updated_on=now() WHERE id=%(addrid)s", {
                    'address': user['email'],
                    'addrid': addrid,
                })
                print("Updated email of {}".format(user['username']))
        else:
            raise Exception("User {} has more than one primary email address!".format(user['username']))
