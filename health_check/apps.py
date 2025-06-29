from django.apps import AppConfig


class HealthCheckConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "health_check"
    verbose_name = "Health Monitoring"

    def ready(self):
        """
        Import signals when the app is ready
        """
        try:
            # Register any signal handlers
            # import health_check.signals
            pass
        except ImportError:
            pass
