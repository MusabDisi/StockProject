# Generated by Django 3.1.1 on 2020-10-12 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_sectors'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sector',
            fields=[
                ('sector_name', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('company_symbol', models.CharField(max_length=12)),
                ('company_name', models.CharField(max_length=64)),
            ],
        ),
        migrations.DeleteModel(
            name='Sectors',
        ),
    ]
