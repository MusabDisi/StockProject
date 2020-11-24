from django.core.management.base import BaseCommand

from myapp import stock_api
from myapp.management.functions import progressBar
from myapp.models import Stock, CryptoCurrency


# This class is Django's way to implement management commands
# You can run it with python manage.py stock_manager
# It will run 'handle' function
class Command(BaseCommand):
    def update_top_stocks(self):
        print('requesting stocks from api ...')
        top_stocks = stock_api._get_top_stocks()
        print('requesting crypto from api ...')
        top_crypto = stock_api.get_top_crypto()

        print('Writing to django DB')
        Command.add_stocks(top_stocks)
        Command.add_crypto(top_crypto)
        print('You are all set!')

    # ** MAIN TASK **
    # Updates the db according to the IEX console stock API.
    def handle(self, *args, **kwargs):
        self.update_top_stocks()

    def add_stocks(top_stocks):
        index = 1
        for stock in progressBar(top_stocks, '\tLoading stocks', 'Complete'):
            # This searches for a stock with the given 'symbol' (the primary key)
            # and updates/create it with the values specified in the 'defaults' parameter
            stock_model, created = Stock.objects.update_or_create(symbol=stock['symbol'], defaults={
                'name': stock['companyName'],
                'top_rank': index,
                'price': stock['latestPrice'],
                'change': stock['change'],
                'change_percent': stock['changePercent'],
                'market_cap': stock['marketCap'],
                'primary_exchange': stock['primaryExchange'],
            })
            stock_model.save()
            index += 1

    def add_crypto(top_crypto):
        index = 1
        for crypto in progressBar(top_crypto, '\tLoading crypto', 'Complete'):
            crypto_model, created = CryptoCurrency.objects.update_or_create(
                rank=index,
                symbol=crypto['symbol'],
                name=crypto['name'],
                currency=crypto['currency']
            )
            crypto_model.save()
            index += 1
