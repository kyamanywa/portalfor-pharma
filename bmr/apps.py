from django.apps import AppConfig


class BmrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bmr'
    
    def ready(self):
        """Import signals when app is ready"""
        import bmr.signals  # noqa
