# Generated by Django 3.1.1 on 2020-11-08 08:15

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0018_favoritestock_stockoperation_userstock'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockoperation',
            name='stock_buy_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='stockoperation',
            name='stock_price',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='stockoperation',
            name='stock',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='myapp.stock'),
        ),
    ]
