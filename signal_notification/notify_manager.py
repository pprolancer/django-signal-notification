import traceback

from django.conf import settings
from django.db.models import Q
from django.utils.module_loading import import_string

from .notify_handlers import get_registered_handlers


class NotifyManager(object):

    __singleton = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls.__singleton is None:
            cls(*args, **kwargs)
        return cls.__singleton

    def __init__(self, *args, **kwargs):
        if NotifyManager.__singleton is not None:
            raise Exception("This class is a singleton!")
        else:
            NotifyManager.__singleton = self
        self.connect_handlers()

    def connect_handlers(self):
        if getattr(settings, 'SIGNAL_NOTIFICATION_DISABLED', False):
            print('Notification Manager is disabled.')
            return

        for handler_name, handler in get_registered_handlers().items():
            assert handler.signal, 'No Signal defined for "{}" handler'.format(handler_name)
            handler.connect_signal(self.handle_notification)

    @classmethod
    def handle_notification(cls, handler_cls, notification_args):
        return cls._handle_notification(handler_cls, notification_args)

    @staticmethod
    def _handle_notification(handler_cls, notification_args):
        from .models import NotificationSetting

        notification_name = handler_cls.name

        notification_settings = NotificationSetting.objects.filter(
            Q(notification_name=notification_name) | Q(notification_name__isnull=True)).filter(enabled=True)

        for ns in notification_settings:
            print("+++ Handling Notification Setting #{}".format(ns.pk))
            handler = handler_cls(ns)
            if not handler.is_triggered(notification_args):
                print("!!! Not triggering notification: {}".format(notification_args))
                continue
            try:
                print("***** Running handler: {}".format(handler))
                handler.handle(notification_args)
            except Exception:
                traceback.print_exc()


def get_registered_notify_manager():
    manager_cls = getattr(settings, 'SIGNAL_NOTIFICATION_MANAGER_CLASS', None) or NotifyManager
    if isinstance(manager_cls, str):
        manager_cls = import_string(manager_cls)
    return manager_cls.get_instance()
