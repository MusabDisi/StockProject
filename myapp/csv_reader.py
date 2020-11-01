import csv
from django.contrib.staticfiles.storage import staticfiles_storage


def read_file(file_path):
    file = staticfiles_storage.path(file_path)
    with open(file) as f:
        rows = list(csv.reader(f))
    return rows
