from django.core import management
from django.core.management import BaseCommand


class Command(BaseCommand):
    def run_all_commands(self):
        management.call_command('makemigrations')
        management.call_command('migrate')
        management.call_command('stock_manager')
        management.call_command('get_crypto_data')
        management.call_command('load_companies_info')
        management.call_command('createcachetable')  # creates the table defined in settings/CACHES

    def handle(self, *args, **options):
        self.run_all_commands()
