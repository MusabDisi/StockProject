from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now


# Create your models here.
class Stock(models.Model):
    symbol = models.CharField(max_length=12, primary_key=True)
    name = models.CharField(max_length=64)
    top_rank = models.IntegerField(null=True)
    price = models.FloatField(null=True)
    change = models.FloatField(null=True)
    change_percent = models.FloatField(null=True)
    market_cap = models.FloatField(null=True)
    primary_exchange = models.CharField(null=True, max_length=32)


class CryptoCurrency(models.Model):
    rank = models.IntegerField(null=True)
    symbol = models.CharField(max_length=12, primary_key=True)
    name = models.CharField(max_length=64)
    currency = models.CharField(max_length=64)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    avatar = models.CharField(max_length=100)


class FavoriteStock(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stocks = models.ManyToManyField(Stock)


class Company(models.Model):
    sector_name = models.CharField(max_length=64)
    company_symbol = models.CharField(max_length=12, primary_key=True)
    company_name = models.CharField(max_length=64)
    company_desc = models.CharField(max_length=250)

    def __str__(self):
        return self.company_name


class StockOperation(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.DO_NOTHING)
    stock_number = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    stock_buy_time = models.DateTimeField(default=now)
    stock_price = models.FloatField(null=True)


class UserStock(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    stock_buyied = models.ManyToManyField(StockOperation)
    budget = models.DecimalField(default=0, max_digits=10, decimal_places=2)


class TrackStock(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    operand = models.IntegerField()  # high 1 or low -1
    state = models.IntegerField()  # increasing 1 or decreasing -1
    weeks = models.IntegerField()
    company_symbol = models.CharField(max_length=12)
    creation_time = models.DateField()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    operand = models.CharField(max_length=12)  # high or low ..
    operator = models.CharField(max_length=6)
    value = models.FloatField()
    company_symbol = models.CharField(max_length=12)
    last_checked = models.DateTimeField(default=now)


class NotificationAnalystRec(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    operator = models.CharField(max_length=6)
    value = models.FloatField()
    company_symbol = models.CharField(max_length=12)
    last_checked = models.DateTimeField(default=now)


class ReadyNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    company_symbol = models.CharField(max_length=12)
    description = models.CharField(max_length=120)
    time = models.DateTimeField(default=now)


class StockOperationHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.DO_NOTHING)
    stock_number = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    stock_buy_time = models.DateTimeField(default=now)
    stock_price = models.FloatField(null=True)
    stock_operation = models.BooleanField(default=False)


class UserStockHistory(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    stock_operation_history = models.ManyToManyField(StockOperationHistory)
