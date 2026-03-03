# Dump interesting information out of django sessions
#
# (This is particarly interesting when digging through old stack trace emails..)
#
from django.core.management.base import BaseCommand, CommandError

import base64
from urllib.parse import parse_qs

from Cryptodome.Cipher import AES

from pgweb.account.models import CommunityAuthSite


class Command(BaseCommand):
    help = 'Decrypt a community authentication session'

    def add_arguments(self, parser):
        parser.add_argument('siteid', help='Community auth site id')
        parser.add_argument('querystring', help='Query string, including d=')

    def handle(self, *args, **options):
        cs = CommunityAuthSite.objects.get(pk=options['siteid'])
        reqvars = parse_qs(options['querystring'].lstrip('?'))

        decryptor = AES.new(base64.b64decode(cs.cryptkey), AES.MODE_SIV, base64.urlsafe_b64decode(reqvars['n'][0]))
        r = decryptor.decrypt_and_verify(base64.urlsafe_b64decode(reqvars['d'][0]), base64.urlsafe_b64decode(reqvars['t'][0])).decode()
        vals = parse_qs(r)

        print("User: {}".format(vals['u'][0]))
        print("Firstname: {}".format(vals['f'][0]))
        print("Lastname: {}".format(vals['l'][0]))
        print("Email: {}".format(vals['e'][0]))
