from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_name', models.CharField(blank=True, max_length=128, null=True)),
                ('notification_rules', jsonfield.fields.JSONField(blank=True, null=True)),
                ('media_name', models.CharField(max_length=32)),
                ('media_params', jsonfield.fields.JSONField(blank=True, null=True)),
                ('enabled', models.BooleanField(default=True)),
                ('create_datetime', models.DateTimeField(auto_now_add=True)),
                ('update_datetime', models.DateTimeField(auto_now=True)),
                ('update_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
