import psycopg2


class ReceiverPlugin:
    def __init__(self, config):
        self.config = config
        self.conn = None

    def __enter__(self):
        self.schema = self.config.get('mediawiki', 'schema')
        # Connect to the db
        self.conn = psycopg2.connect(self.config.get('mediawiki', 'connstr'))
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
        # Update the user if it has changed, ignore it if it's not present
        self.curs.execute("UPDATE {}.mwuser SET user_real_name=%(realname)s, user_email=%(email)s WHERE user_name=%(username)s AND (user_real_name, user_email) IS DISTINCT FROM (%(realname)s, %(email)s)".format(self.schema), {
            'realname': user['firstname'] + ' ' + user['lastname'],
            'email': user['email'],
            'username': user['username'].capitalize(),
        })
        if self.curs.rowcount > 0:
            print("Updated user {}".format(user['username']))
