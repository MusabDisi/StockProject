import csv
from django.contrib.staticfiles.storage import staticfiles_storage


def read_file():
    file = staticfiles_storage.path('files/companies_sectors.csv')
    with open(file) as f:
        rows = list(csv.reader(f))
    return rows
