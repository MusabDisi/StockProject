# Generated by Django 3.1.1 on 2020-10-12 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_auto_20201013_0103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sector',
            name='company_symbol',
            field=models.CharField(max_length=12, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='sector',
            name='sector_name',
            field=models.CharField(max_length=64),
        ),
    ]
