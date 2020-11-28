default_app_config = 'signal_notification.apps.SignalNotificationConfig'


class NotificationException(Exception):
    pass


class UnknownNotificationHandlerException(NotificationException):
    pass


class UnknownNotificationMediaException(NotificationException):
    pass


class InvalidNotificationMediaArgsException(NotificationException):
    pass
