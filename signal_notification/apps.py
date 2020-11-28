from django.apps import AppConfig


class SignalNotificationConfig(AppConfig):
    name = 'signal_notification'

    def ready(self):
        from signal_notification.notify_manager import get_registered_notify_manager, get_registered_handlers
        get_registered_handlers()
        get_registered_notify_manager()

