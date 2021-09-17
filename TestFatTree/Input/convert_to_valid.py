import csv
import sys

if len(sys.argv) != 2:
    exit()

with open(sys.argv[1]) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=' ')
    line_count = 0
    for row in csv_reader:
        if line_count > 0:
            src, dest, fsize, t = row[0], row[1], row[4], row[5]
            print('\t'.join([src, dest, str(int(fsize)*8), t]))
        line_count += 1
