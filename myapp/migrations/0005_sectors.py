# Generated by Django 3.1.1 on 2020-10-12 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sectors',
            fields=[
                ('sector', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('symbol', models.CharField(max_length=12)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
    ]
