from collections import OrderedDict

from cerberus import Validator
from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string

from signal_notification import UnknownNotificationMediaException, InvalidNotificationMediaArgsException

_registered_medias = None
EMAIL_SCHEMA = {
    'type': 'string', 'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
}
SCHEMA_LIST_OF_EMAILS = {
    'type': 'list', 'empty': False, 'required': True,
    'schema': EMAIL_SCHEMA,
    'meta': {
        'caption': 'Email Recipients',
        'item_caption': 'Email Recipient',
    },
}

SCHEMA_LIST_OF_PHONE_NUMBERS = {
    'type': 'list', 'empty': False, 'required': True,
    'schema': {'type': 'string', },
    'meta': {
        'caption': 'To Recipients',
        'item_caption': 'To',
    },
}


def get_registered_medias():
    global _registered_medias
    if _registered_medias is None:
        media_classes = getattr(settings, 'SIGNAL_NOTIFICATION_MEDIA_CLASSES', None)
        if media_classes is None:
            media_classes = DEFAULT_MEDIA_CLASSES
        medias_dict = OrderedDict()
        for media_cls in media_classes:
            if isinstance(media_cls, str):
                media_cls = import_string(media_cls)
            assert media_cls.name, 'Media class should have specified a "name"'
            assert issubclass(media_cls, NotifyMedia), 'Media should be subclass of NotifyMedia'
            medias_dict[media_cls.name] = media_cls
        _registered_medias = medias_dict
    return _registered_medias


class NotifyMedia(object):
    name = None
    PARAMS_SCHEMA_VALIDATOR = None

    def __init__(self, **kwargs):
        self.kwargs = self.validate_args(kwargs)

    @classmethod
    def validate_args(cls, kwargs):
        args_schema = {}
        for arg_name, arg_schema in (cls.PARAMS_SCHEMA_VALIDATOR or {}).items():
            args_schema[arg_name] = {k: v for k, v in (arg_schema or {}).items() if not k.startswith('_')}

        v = Validator(args_schema, purge_unknown=True)
        if not v.validate(kwargs or {}):
            raise InvalidNotificationMediaArgsException('Invalid Media Params', v.errors)
        return v.document

    def send(self, message, subject=None):
        raise NotImplementedError

    @staticmethod
    def get_class_by_name(name):
        media_cls = get_registered_medias().get(name)
        if not media_cls:
            raise UnknownNotificationMediaException('No Media Notification: "{}"'.format(name))
        return media_cls


class EmailMedia(NotifyMedia):
    name = 'email'
    PARAMS_SCHEMA_VALIDATOR = {
        'recipients': SCHEMA_LIST_OF_EMAILS
    }

    def send(self, message, subject=None):
        from_email = settings.DEFAULT_EMAIL_FROM
        recipients = self.kwargs['recipients']
        if isinstance(recipients, str):
            recipients = [recipients]
        else:
            recipients = list(recipients)
        return send_mail(subject, message, from_email, recipients, html_message=message,
                         fail_silently=False)


class SMSMedia(NotifyMedia):
    name = 'sms'
    PARAMS_SCHEMA_VALIDATOR = {
        'recipients': SCHEMA_LIST_OF_PHONE_NUMBERS
    }

    def send(self, message, subject=None):
        from sendsms import api
        from_ = settings.SMS_DEFAULT_FROM_PHONE
        recipients = self.kwargs['recipients']
        if isinstance(recipients, str):
            recipients = [recipients]
        else:
            recipients = list(recipients)

        return api.send_sms(body=message, from_phone=from_, to=recipients, fail_silently=False)


class RocketchatMedia(NotifyMedia):
    name = 'rocketchat'
    PARAMS_SCHEMA_VALIDATOR = {
        'webhook_url': {'type': 'string', 'empty': False, 'required': True}
    }

    def send(self, message, subject=None):
        import requests

        json_message = {'subject': subject, 'text': message}
        if getattr(settings, 'NOTIFICATION_MEDIA_ROCKETCHAT_MOCK', False):
            print('Sent Rocket chat mock: {}'.format(json_message))
            print(message)
            return
        response = requests.post(self.kwargs['webhook_url'], json=json_message)
        if not response.ok:
            raise Exception('Failed to send message: "{} {}", {}'.format(
                response.status_code, response.reason, response.json())
            )


DEFAULT_MEDIA_CLASSES = [
    EmailMedia, SMSMedia, RocketchatMedia
]
