# Generated by Django 3.1.1 on 2020-10-15 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_readynotification_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('sector_name', models.CharField(max_length=64)),
                ('company_symbol', models.CharField(max_length=12, primary_key=True, serialize=False)),
                ('company_name', models.CharField(max_length=64)),
                ('company_desc', models.CharField(max_length=250)),
            ],
        ),
        migrations.DeleteModel(
            name='Sector',
        ),
    ]
