from django.db import models


# Create your models here.
class Stock(models.Model):
    symbol = models.CharField(max_length=12, primary_key=True)
    name = models.CharField(max_length=64)
    top_rank = models.IntegerField(null=True)
    price = models.FloatField()
    change = models.FloatField(null=True)
    change_percent = models.FloatField()
    market_cap = models.FloatField(null=True)
    primary_exchange = models.CharField(null=True, max_length=32)


class Sectors(models.Model):
    sector = models.CharField(max_length=64, primary_key=True)
    symbol = models.CharField(max_length=12)
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.sector
