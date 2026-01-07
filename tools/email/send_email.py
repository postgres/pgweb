#!/usr/bin/env python3

import argparse
import psycopg2
import smtplib
import sys
import yaml


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Email tester")
    parser.add_argument('db', help='Name of database (looked up in config.yaml) t connect to')
    parser.add_argument('id', type=int, help='ID of email entry to send')
    parser.add_argument('recipient', help='Email address of recipient to send to')

    args = parser.parse_args()

    with open('config.yaml') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    if args.db not in config['db']:
        print("Non-existing db specified")
        sys.exit(1)

    if isinstance(config['mail']['password'], str):
        password = config['mail']['password']
    elif isinstance(config['mail']['password'], dict):
        import secretstorage
        coll = secretstorage.get_default_collection(secretstorage.dbus_init())
        if coll.is_locked():
            coll.unlock()
        r = list(coll.search_items(config['mail']['password']))
        if len(r) == 0:
            print("Could not find password in secret storage.")
            sys.exit(1)
        elif len(r) > 1:
            print("Found more than one password, try again.")
            sys.exit(1)
        password = r[0].get_secret().decode()
    else:
        print("Invalid type for password in configuration")
        sys.exit(1)

    # Connect to db and get message
    dbconn = psycopg2.connect(config['db'][args.db])
    curs = dbconn.cursor()
    curs.execute("SELECT fullmsg FROM mailqueue_queuedmail WHERE id=%(id)s", {
        'id': args.id,
    })
    r = curs.fetchall()
    dbconn.close()

    if len(r) == 0:
        print("Email not found")
        sys.exit(1)

    msg = r[0][0]

    # Now do it!
    smtp = smtplib.SMTP(host=config['mail']['server'], port=config['mail']['port'])
    smtp.starttls()
    smtp.login(user=config['mail']['user'], password=password)

    smtp.sendmail(config['mail']['sender'], args.recipient, msg)

    smtp.quit()

    print("Sent.")
