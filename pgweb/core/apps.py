from django.apps import AppConfig, apps


class CoreAppConfig(AppConfig):
    name = 'pgweb.core'

    def ready(self):
        from pgweb.util.signals import register_basic_signal_handlers

        register_basic_signal_handlers()
