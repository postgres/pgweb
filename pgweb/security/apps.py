from django.apps import AppConfig
from django.db.models.signals import post_migrate


def do_post_migrate(sender, **kwargs):
    from .loader import load_security_json
    load_security_json()


class SecurityAppConfig(AppConfig):
    name = "pgweb.security"

    def ready(self):
        post_migrate.connect(do_post_migrate, sender=self)
