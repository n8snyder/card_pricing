import logging
logging.basicConfig(level=logging.INFO)
import sys, django, os
sys.path.append(os.path.realpath(__file__))
sys.path.append(os.environ['PATH_TO_PRICING'])

django.setup()
import csv

from rules_parser import update_csv_row

def write_updated_file():
    print('Updating inventory...')
    with open('tcg_inventory.csv', 'r') as csvfile:
        file = csv.DictReader(csvfile)
        with open('tcg_updated_inventory.csv', 'w') as new_csvfile:
            writer = csv.DictWriter(new_csvfile, fieldnames=file.fieldnames)
            writer.writeheader()
            for row in file:
                if 'Foil' in row['Condition']:
                    finish = 'Foil'
                else:
                    finish = 'Regular'
                if not 'Near Mint' in row['Condition']:
                    continue

                row = update_csv_row(row, finish=finish)
                if row:
                    writer.writerow(row)

if __name__ == "__main__":
    write_updated_file()
