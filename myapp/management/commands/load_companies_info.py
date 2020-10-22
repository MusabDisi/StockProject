from myapp.models import Company
from myapp import csv_reader
from django.core.management.base import BaseCommand
from myapp.management.functions import progressBar


# This class is Django's way to implement management commands
# You can run it with python manage.py load_companies_info
# It will run 'handle' function
class Command(BaseCommand):
    def load_csv(self):
        print('reading data from csv ...')
        rows = csv_reader.read_file('files/companies_information.csv')
        print('loading data to db.')
        for row in progressBar(rows, '    Loading', 'Complete'):
            sector_obj = Company(company_symbol=row[0], company_name=row[1], sector_name=row[2], company_desc=row[3])
            sector_obj.save()

    # ** MAIN TASK **
    # Updates the db with data from csv.
    def handle(self, *args, **kwargs):
        self.load_csv()


