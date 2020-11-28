from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import user_logged_in, user_login_failed, get_user_model
from django.db.models.signals import post_save
from django.template import TemplateDoesNotExist, Template, Context
from django.template.loader import render_to_string
from django.utils.module_loading import import_string

from signal_notification import UnknownNotificationHandlerException
from signal_notification.notify_media import NotifyMedia

_registered_handlers = None


def get_registered_handlers():
    global _registered_handlers
    if _registered_handlers is None:
        handler_classes = getattr(settings, 'SIGNAL_NOTIFICATION_HANDLER_CLASSES', None) or []
        handlers_dict = OrderedDict()
        for h in handler_classes:
            handler_cls = import_string(h)
            assert issubclass(handler_cls, NotifyHandler), 'Handler should be subclass of NotifyHandler'
            assert handler_cls.name, 'Handler class should have specified a "name"'
            assert handler_cls.signal, 'Handler class should have specified a "signal"'
            handlers_dict[handler_cls.name] = handler_cls
        _registered_handlers = handlers_dict
    return _registered_handlers


class NotifyHandler(object):
    name = None  # every child class should define name property
    MESSAGE_TEMPLATE_PATH_PATTERNS = [
        'signal_notification/{notification}/message-{media}.html',
        'signal_notification/{notification}/message.html'
    ]
    SUBJECT_TEMPLATE_PATH_PATTERNS = [
        'signal_notification/{notification}/subject-{media}.html',
        'signal_notification/{notification}/subject.html'
    ]
    subject_template = None
    message_template = None
    signal = None
    signal_receiver = None
    signal_sender = None

    def __init__(self, notification_setting):
        assert notification_setting is not None, 'notification_setting cannot be None'
        self.notification_setting = notification_setting

    @classmethod
    def signal_handler(cls, sender, **kwargs):
        # notification_args = {k: kwargs.get(k) for k in cls.signal.providing_args}
        notification_args = kwargs
        assert cls.signal_receiver is not None, 'not connected signal!'
        cls.signal_receiver(cls, notification_args)

    @classmethod
    def connect_signal(cls, signal_receiver):
        cls.signal_receiver = signal_receiver
        cls.signal.connect(cls.signal_handler, sender=cls.signal_sender)

    @property
    def message_template_path(self):
        templates = self.MESSAGE_TEMPLATE_PATH_PATTERNS
        if isinstance(templates, str):
            templates = [templates]

        return [t.format(notification=self.name, media=self.notification_setting.media_name) for t in templates]

    @property
    def subject_template_path(self):
        templates = self.SUBJECT_TEMPLATE_PATH_PATTERNS
        if isinstance(templates, str):
            templates = [templates]

        return [t.format(notification=self.name, media=self.notification_setting.media_name) for t in templates]

    def get_rendered_subject(self, context):
        try:
            return render_to_string(self.subject_template_path, context)
        except TemplateDoesNotExist:
            t = Template(self.subject_template or '')
            return t.render(Context(context))

    def get_rendered_message(self, context):
        try:
            return render_to_string(self.message_template_path, context)
        except TemplateDoesNotExist as e:
            if not self.message_template:
                raise e
            t = Template(self.message_template or '')
            return t.render(Context(context))

    def is_triggered(self, notification_args):
        # TODO: we should process the rules here!
        return True

    def get_template_context(self, notification_args):
        return notification_args

    def handle(self, notification_args):
        media_cls = NotifyMedia.get_class_by_name(self.notification_setting.media_name)
        media = media_cls(**(self.notification_setting.media_params or {}))
        context = self.get_template_context(notification_args)
        subject = self.get_rendered_subject(context)
        message = self.get_rendered_message(context)
        media.send(message, subject)

    @staticmethod
    def get_class_by_name(name):
        handler_cls = get_registered_handlers().get(name)
        if not handler_cls:
            raise UnknownNotificationHandlerException('No Handler Notification: "{}"'.format(name))
        return handler_cls


class UserLoggedInHandler(NotifyHandler):
    """Sample Handler to notify when a user logged in in system"""

    signal = user_logged_in
    name = 'user_logged_in'
    subject_template = 'New Login'
    message_template = 'User "{{user}}" Logged In.'


class UserLoginFailedHandler(NotifyHandler):
    """Sample Handler to notify when a login attempt failed in system"""

    def get_template_context(self, notification_args):
        request = notification_args.get('request')
        ip = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
        ctx = {'remote_ip': ip}
        ctx.update(notification_args)
        return ctx

    signal = user_login_failed
    name = 'user_login_failed'
    subject_template = 'Login Failed'
    message_template = 'Failed login for "{{credentials.username}}" username! Remote ip: {{remote_ip}}'


User = get_user_model()


class NewUserHandler(NotifyHandler):
    signal = post_save
    signal_sender = User
    name = 'new_user'
    subject_template = 'New User'
    message_template = 'New User added to system. username: "{{instance.username}}"'

    def is_triggered(self, notification_args):
        created = notification_args.get('created')
        if not created:
            return False
        return super().is_triggered(notification_args)
