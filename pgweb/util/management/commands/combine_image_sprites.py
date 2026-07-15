from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from pgweb.util.sprites import sprites


class Command(BaseCommand):
    help = 'Combine images to sprites'

    def add_arguments(self, parser):
        parser.add_argument('image', type=str, nargs='?', default='all', choices=('books', 'all', ))

    def handle(self, *args, **options):
        if options['image'] == 'all':
            for k, s in sprites.items():
                print("Creating sprite for {}".format(k))
                s.build_sprite_image()
        else:
            sprites[options['image']].build_sprite_image()
