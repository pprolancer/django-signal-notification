# Django Signal Notification
a django app to send any notifications(sms, email, rocketchat and any media) after triggered a signal.
you can add new "media" and new "handler".
also you can customize your template messages directly in python handler class or in a django template file.

# Setup

## Requirements

- Python >= 3.4
- Django >= 2.0

## Installation

1. Install django-signal-notifier by pip:
    ```
    $ pip install django-signal-notification
    ```
1. Add "signal_notification" at the end of INSTALLED_APPS setting like this
    ```
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        ...
        'signal_notification',
    ]
    ```
1. ```python manage.py migrate```
1. goto admin panel to add new NotificationSetting records.

## Settings
```python
# Disable signal notification completely if set as True
SIGNAL_NOTIFICATION_DISABLED = False 

# Add your custom media classes path here.
SIGNAL_NOTIFICATION_MEDIA_CLASSES = [
    'signal_notification.notify_media.EmailMedia',
    'signal_notification.notify_media.SMSMedia',
]

# set your custom NotifyManager class path here
SIGNAL_NOTIFICATION_MANAGER_CLASS = 'signal_notification.notify_manager.NotifyManager'

# Add your handlers class path here.
SIGNAL_NOTIFICATION_HANDLER_CLASSES = [
    'signal_notification.notify_handlers.UserLoggedInHandler',
    'signal_notification.notify_handlers.UserLoginFailedHandler',
    'signal_notification.notify_handlers.NewUserHandler',
]

```

# Add new Media class
- You should add a new class inherited from "signal_notification.notify_media.NotifyMedia".
- set unique "name" field of that class 
- override and implement the "send" method
- set PARAMS_SCHEMA_VALIDATOR field for that class
```python
from signal_notification.notify_media import NotifyMedia
class NewMedia(NotifyMedia):
    name = 'new_media'
    PARAMS_SCHEMA_VALIDATOR = {
        'to': {'type': 'string', 'nullable': False, 'required': True, 'empty': False}
    }
    def send(self, message, subject=None):
        to = self.kwargs['to']
        # ...
```
- append path of this class to "SIGNAL_NOTIFICATION_MEDIA_CLASSES" setting
```
SIGNAL_NOTIFICATION_MEDIA_CLASSES = [
    ...
    'foo.bar.NewMedia'
]
```

# Add new Handler class
- You should add a new class inherited from "signal_notification.notify_handlers.NotifyHandler".
- set unique "name" field of that class
- set subject and message templates(directly in class or as a django templates file)
```python
from django.contrib.auth import user_logged_out
from signal_notification.notify_handlers import NotifyHandler
class StaffUserLoggedOut(NotifyHandler):
    """Send a notification when an Staff user logged out"""
    name = 'staff_user_logged_out'
    signal = user_logged_out
    subject_template = 'User Exited'
    message_template = 'Staff User "{{user}}" Logged out.'

    def is_triggered(self, notification_args):
        """Using this method to ignore notification by checking some conditions"""
        user = notification_args.get('user')
        if not user.is_staff:
            return False
        return super().is_triggered(notification_args)

```
- append path of this class to "SIGNAL_NOTIFICATION_HANDLER_CLASSES" setting
```
SIGNAL_NOTIFICATION_HANDLER_CLASSES = [
    ...
    'foo.bar.StaffUserLoggedOut'
]
```

# How to customize the message template of handler?

You have 2 options:

1. define subject and message directly in Handler class by setting this fields of class:
    - subject_template
    - message_template
1. define subject and message in templates path as a django template file.
    - add a subject file in this templates path:
        - signal_notification/<handler_name>/subject-<media_name>.html  # this is for specific media
        - signal_notification/<handler_name>/subject.html  # this is for all media
    - add a message file in this templates path:
        - signal_notification/<handler_name>/message-<media_name>.html  # this is for specific media
        - signal_notification/<handler_name>/message.html  # this is for all media

Notice: the priorities for templates are:
1. media template: signal_notification/<handler_name>/message-<media_name>.html
1. general template: signal_notification/<handler_name>/message.html
1. class template fields: message_template

# Signals
- You can use predefined django signals(like, post_save, pre_save, ..)
- You can add your signals and use that in Handler
```python
# in foo/bar/signals.py
from django.dispatch import Signal
test_signal = Signal()

```

# add Custom NotifyManager

some times you want to have your custom manger. for example you want notifications be handled in a background task using celery, apscheduler, huey.
  
1. You need to add a new class inherited from signal_notification.notify_manager.NotifyManager
1. override the "handle_notification" class method.(use "_handle_notification" in your method as a final endpoint of handler method)
```python
import traceback
from signal_notification.notify_manager import NotifyManager

class APSchedulerNotifyManager(NotifyManager):

    @classmethod
    def handle_notification(cls, handler_cls, notification_args):
        apscheduler_client = '<apscheduler_client object>'  
        try:
            apscheduler_client.root.add_job(
                'foo.bar:APSchedulerNotifyManager._handle_notification', 'date',
                args=(handler_cls, notification_args)
            )
        except Exception:
            traceback.print_exc()

```
1. set path of this class for SIGNAL_NOTIFICATION_MANAGER_CLASS setting
```python
SIGNAL_NOTIFICATION_MANAGER_CLASS = 'foo.bar.APSchedulerNotifyManager'
```

# Demo

1. ```cd django_signal_notification/demo```
1. ```python manage.py migrate```
1. ```python manage.py createsuperuser```
1. ```python manage.py runserver```
1. goto http://127.0.0.1:8000/admin
1. navigate to /admin/signal_notification/notificationsetting/ and add your NotificationSettings records
