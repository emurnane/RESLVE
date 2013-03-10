# -*- coding: utf-8 -*-
import csv
def query_csv_for_rows(csv_path, exclude_headers=True):
    rows = []
    row_num = 0
    for row in csv.reader(open(csv_path, 'rU')):
        try:
            if not exclude_headers or row_num!=0: # row 0 is header
                rows.append(row)
            row_num = row_num+1    
        except:
            continue # just ignore a problematic row
    return rows