#!/usr/bin/env python

# Script from jrivero: https://gist.github.com/jrivero/1085501

import configparser
import os

config = configparser.ConfigParser()
config.read('../config.ini')
DATABASE = config['PARAMS']['database']
EXTRACTED_DIR = os.path.join(DATABASE, 'extracted')


def split(filehandler, delimiter=',', row_limit=10000,
          output_name_template='output_%s.csv', output_path='.', keep_headers=True):
    """
    Splits a CSV file into multiple pieces.

    A quick bastardization of the Python CSV library.
    Arguments:
        `row_limit`: The number of rows you want in each output file. 10,000 by default.
        `output_name_template`: A %s-style template for the numbered output files.
        `output_path`: Where to stick the output files.
        `keep_headers`: Whether or not to print the headers in each output file.
    Example usage:

        >> from toolbox import csv_splitter;
        >> csv_splitter.split(open('/home/ben/input.csv', 'r'));

    """
    import csv
    reader = csv.reader(filehandler, delimiter=delimiter)
    current_piece = 1
    current_out_path = os.path.join(
        output_path,
        output_name_template % current_piece
    )
    current_out_writer = csv.writer(open(current_out_path, 'w', newline=''), delimiter=delimiter)
    print(current_out_path)
    current_limit = row_limit
    if keep_headers:
        headers = next(reader)
        current_out_writer.writerow(headers)
    for i, row in enumerate(reader):
        if i % 10000 == 0:
            print(i)
        if i + 1 > current_limit:
            current_piece += 1
            current_limit = row_limit * current_piece
            current_out_path = os.path.join(
                output_path,
                output_name_template % current_piece
            )
            current_out_writer = csv.writer(open(current_out_path, 'w', newline=''), delimiter=delimiter)
            print(current_out_path)
            if keep_headers:
                current_out_writer.writerow(headers)
        current_out_writer.writerow(row)


if __name__ == '__main__':
    split(open(os.path.join(EXTRACTED_DIR, 'data.csv'), 'r'), delimiter=',', row_limit=100000,
          output_name_template='data_%s.csv', output_path='D:\\LoLAnalyzerDB\\extracted', keep_headers=False)