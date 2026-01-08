from django.apps import AppConfig


class RafflesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.raffles'
    verbose_name = 'Rifas'

    def ready(self):
        # Import signals to register them
        import apps.raffles.signals  # noqa: F401
