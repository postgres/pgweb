#!/usr/bin/env python3
#
# Script to register with social providers
#
#

from django.core.management.base import BaseCommand
from django.conf import settings

from pgweb.util.socialposter import get_all_providers

allproviders, allprovidernames = get_all_providers(settings, True)


class Command(BaseCommand):
    help = 'Register with social providers'

    def add_arguments(self, parser):
        parser.add_argument('provider', choices=allprovidernames)

    def handle(self, *args, **options):
        for p in allproviders:
            if p.name == options['provider']:
                r = p.register('pgweb')
                if r:
                    print(r)
                else:
                    print("{} already registered.".format(p.name))
                break
        else:
            print("Provider {} not found.".format(p.name))
