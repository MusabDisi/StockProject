from django.core.exceptions import ValidationError

from myapp.models import Sector
from myapp import csv_reader
from django.core.management.base import BaseCommand


# This class is Django's way to implement management commands
# You can run it with python manage.py load_sectors_csv
# It will run 'handle' function
class Command(BaseCommand):
    def load_csv(self):
        rows = csv_reader.read_file()
        for row in rows:
            sector_obj = Sector(company_symbol=row[0], company_name=row[1], sector_name=row[2])
            sector_obj.save()

    # ** MAIN TASK **
    # Updates the db with data from csv.
    def handle(self, *args, **kwargs):
        self.load_csv()
