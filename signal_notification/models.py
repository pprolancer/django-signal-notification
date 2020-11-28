import jsonfield
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from signal_notification import InvalidNotificationMediaArgsException
from signal_notification.notify_handlers import get_registered_handlers
from signal_notification.notify_media import get_registered_medias

# Create your models here.

User = get_user_model()


class NotificationSetting(models.Model):
    notification_name = models.CharField(max_length=128, null=True, blank=True)
    notification_rules = jsonfield.JSONField(null=True, blank=True)
    media_name = models.CharField(max_length=32)
    media_params = jsonfield.JSONField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    create_datetime = models.DateTimeField(auto_now_add=True)
    update_datetime = models.DateTimeField(auto_now=True)
    update_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)

    @classmethod
    def get_notification_name_choices(cls):
        choices = getattr(cls, '_notification_name_choices', None)
        if choices is None:
            cls._notification_name_choices = choices = tuple(
                (n, n.replace('_', ' ').capitalize()) for n in get_registered_handlers()
            )
        return choices

    @classmethod
    def get_media_name_choices(cls):
        choices = getattr(cls, '_media_name_choices', None)
        if choices is None:
            cls._media_name_choices = choices = tuple(
                (n, n.replace('_', ' ').capitalize()) for n in get_registered_medias()
            )
        return choices

    @property
    def media_cls(self):
        return get_registered_medias().get(self.media_name)

    def validate_media_params(self):
        self.media_params = self.media_cls.validate_args(self.media_params)

    def save(self, *args, **kwargs):
        if not self.notification_name:
            self.notification_name = None
        else:
            assert self.notification_name in get_registered_handlers(), \
                'notification_name should be in this choices: {}'.format(self.get_notification_name_choices())
        assert self.media_name in get_registered_medias(), \
            'media_name should be in this choices: {}'.format(self.get_media_name_choices())
        try:
            self.validate_media_params()
        except InvalidNotificationMediaArgsException as e:
            raise ValidationError({'media_params': e.args})
        super().save(*args, **kwargs)

    @property
    def notification_name_display(self):
        return dict(self.get_notification_name_choices()).get(self.notification_name) or \
               self.notification_name or '--- ALL ---'

    @property
    def media_name_display(self):
        return dict(self.get_media_name_choices()).get(self.media_name) or self.media_name

    def __str__(self):
        return self.notification_name_display
