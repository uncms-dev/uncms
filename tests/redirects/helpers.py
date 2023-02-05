import csv
from io import StringIO


def generate_csv(lines):
    """
    Helper to generate a file object with a CSV file as data. Takes a list of
    tuples, returns a StringIO.
    """
    io = StringIO()
    writer = csv.writer(io)
    for line in lines:
        writer.writerow(line)
    io.seek(0)
    io.name = 'example.csv'
    return io
