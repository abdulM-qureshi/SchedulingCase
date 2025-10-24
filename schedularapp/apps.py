from django.apps import AppConfig

class SchedularappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "schedularapp"
    def ready(self):
        from . import signals  
