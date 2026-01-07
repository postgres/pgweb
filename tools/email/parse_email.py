#!/usr/bin/env python3

import argparse
import email
import email.policy
import psycopg2
import sys
import yaml


def print_message(msg, level=0):
    def _out(t):
        print("{}{}".format('  ' * level, t))

    _out(msg.get_content_type())
    if msg.is_multipart():
        for p in msg.iter_parts():
            print_message(p, level + 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Print email MIME structure")
    parser.add_argument('db', help='Name of database (looked up in config.yaml) t connect to')
    parser.add_argument('id', type=int, help='ID of email entry to send')

    args = parser.parse_args()

    with open('config.yaml') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    if args.db not in config['db']:
        print("Non-existing db specified")
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

    msg = email.message_from_string(r[0][0], policy=email.policy.default)

    print_message(msg)
