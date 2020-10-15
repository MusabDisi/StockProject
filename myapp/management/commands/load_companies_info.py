from myapp.models import Company
from myapp import csv_reader
from django.core.management.base import BaseCommand


# This class is Django's way to implement management commands
# You can run it with python manage.py load_companies_info
# It will run 'handle' function
class Command(BaseCommand):
    def load_csv(self):
        rows = csv_reader.read_file('files/companies_information.csv')
        print('loading data to db ...')
        for row in progressBar(rows, 'Progress', 'Complete'):
            sector_obj = Company(company_symbol=row[0], company_name=row[1], sector_name=row[2], company_desc=row[3])
            sector_obj.save()

    # ** MAIN TASK **
    # Updates the db with data from csv.
    def handle(self, *args, **kwargs):
        self.load_csv()


# from stack overflow https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def progressBar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)

    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()
