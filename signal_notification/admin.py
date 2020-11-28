from django.contrib import admin
from django.forms import ModelForm, Select, forms

from signal_notification import InvalidNotificationMediaArgsException
from signal_notification.notify_media import get_registered_medias
from .models import NotificationSetting


class NotificationSettingAdminForm(ModelForm):
    class Meta:
        model = NotificationSetting
        exclude = ['notification_rules']
        widgets = {
            'notification_name': Select(
                choices=((None, '--- All ---'),) + NotificationSetting.get_notification_name_choices()),
            'media_name': Select(choices=NotificationSetting.get_media_name_choices()),
        }
        labels = {
            'media_name': 'Send By (Media Name)',
        }

    def clean_media_params(self):
        media_name = self.cleaned_data['media_name']
        media_params = self.cleaned_data['media_params']
        media_cls = get_registered_medias().get(media_name)
        if not media_cls:
            return media_params

        try:
            media_params = media_cls.validate_args(media_params)
        except InvalidNotificationMediaArgsException as e:
            raise forms.ValidationError(str(e.args[1]))
        return media_params


def notification_enable_action(modeladmin, request, queryset):
    queryset.update(enabled=True)


notification_enable_action.short_description = "Enable selected notification settings"


def notification_disable_action(modeladmin, request, queryset):
    queryset.update(enabled=False)


notification_disable_action.short_description = "Disable selected notification settings"


class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = (
        'get_notification_name_display', 'get_media_name_display', 'enabled', 'update_by', 'update_datetime',
    )
    form = NotificationSettingAdminForm
    actions = [notification_enable_action, notification_disable_action]

    def get_notification_name_display(self, obj):
        return obj.notification_name_display

    get_notification_name_display.short_description = 'Notification Name'

    def get_media_name_display(self, obj):
        return obj.media_name_display

    get_media_name_display.short_description = 'Media Name'

    def save_model(self, request, obj, form, change):
        obj.update_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(NotificationSetting, NotificationSettingAdmin)
