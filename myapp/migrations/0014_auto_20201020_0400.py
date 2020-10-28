# Generated by Django 3.1.1 on 2020-10-20 01:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import myapp.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0013_track_state'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrackStock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operand', models.IntegerField()),
                ('state', models.IntegerField()),
                ('days', models.IntegerField()),
                ('company_symbol', models.CharField(max_length=12)),
                ('creation_time', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='Track',
        ),
    ]