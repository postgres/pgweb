from django.apps import AppConfig
from django.db.models.signals import post_migrate


def do_post_migrate(sender, **kwargs):
    from .migrate import do_migrate
    do_migrate()


class ReleaseAppConfig(AppConfig):
    name = "pgweb.release"

    def ready(self):
        post_migrate.connect(do_post_migrate, sender=self)
