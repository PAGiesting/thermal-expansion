#!/usr/bin/python3

"""Netszch dilatometer themal expansion data extraction routine.
It takes a folder / directory name from command line or asks user,
* then checks folder's archive record against directory contents,
* then archives new data files.
The archive structure:
    JSON files
    metadata stored as key: value pairs
    data stored as key: listing
The json file base name is the same as the processed data file.
"""

import json
import csv
import sys
import os
import codecs
import openpyxl as xlsx
from copy import copy
from collections import defaultdict

# This is a simple text file with one file name per line.
record_file_name = 'th_exp_data.dat'


def select_data_files(file_names):
    """Picks out only .csv and .xlsx files for parsing."""

    new_file_names = []
    for name in file_names:
        if name.endswith('.csv'):
            new_file_names.append(name)
        elif name.endswith('.xlsx'):
            new_file_names.append(name)
        else:
            pass
    return new_file_names

def check_update(folder):
    """Checks the folder for new files not listed in its local record.
    Returns a list of new filenames.
    """
    
    file_names = os.listdir(folder)
    if record_file_name not in file_names:
        with open(folder + record_file_name, 'w') as record_file:
            record_file.writelines(record_file_name + '\n')
        new_file_names = select_data_files(file_names)
    else:
        new_file_names = []
        with open(folder + record_file_name, 'r') as record_file:
            old_file_names = record_file.readlines()
        for name in file_names:
            if name not in old_file_names:
                new_file_names.append(name)
        new_file_names = select_data_files(new_file_names)

    return new_file_names


def archive_data_file(folder, file_name):
    """Reads in a data file, processes it into two dictionaries,
    then dumps it to a JSON file. Returns the new json file name.
    """

    # Routine to check file type and read data.
    # In the Netszch data files, the header line for the actual
    # data starts with a double #, while the metadata lines
    # start with #, and the data lines start with a space.
    # Metadata has a ton of whitespace to strip().

    # Kate tells me that the Netszch csv data files are encoded in
    # ISO-8859-15. The Python documentation is damnably coy on how
    # to set the encoding for the csv reader or file opener, but I
    # eventually tracked it down. The routine leaves the degree symbol
    # as \u00b0 and the letter mu (micro) as \u00b5.
    # There is also a blank line right before the ## line with
    # a NUL byte, which is fixed via the generator replace().
    
    # The xlsx files cannot be coped with via "csv.reader(... dialect
    # = 'excel')" and require openpyxl [as xlsx]. This routine leaves
    # both of the disputed characters as \ufffd.

    if file_name.endswith('.csv'):
        with open(folder + file_name, 'r', encoding='iso_8859_15') \
            as raw_file:
            raw_csv = csv.reader((line.replace('\0','') for line in raw_file),
                                 skipinitialspace=True, delimiter=',')
            raw_data = list(raw_csv)        
    elif file_name.endswith('.xlsx'):
        raw_wb = xlsx.load_workbook(folder + file_name)
        raw_data = []
        for i, row in enumerate(raw_wb.active.values):
            # The weird filter code knocks out the None values that show up
            # in the converted cells that had no value in them.
            # This fixes multiple problems in the data processing loop
            # below. In particular, it means the len = 0 line skips
            # the blank line for both file types, and keeps the main data
            # ingestion code from accidentally trying to eat and parse
            # None values as column headers or data.
            raw_data.append(list(filter(None.__ne__,list(row))))
    else:
        print('Cannot process', file_name)
        return None

    data_dict = {}
    metadata = True
    for row in raw_data:
        # To cope with the blank line.
        # A .csv file generates an empty list there.
        # An .xlsx file generates a line of None values,
        # but those are knocked out by the filter above.
        if len(row) == 0:
            pass
        elif type(row[0]) == str and row[0].startswith('##'):
            metadata = False
            # Slice off the '##' signal characters. 
            row[0] = row[0][2:]
            data_headers = row
            # Initialize the data dictionary to receive values.
            for item in row:
                data_dict[item.strip()] = []
        elif metadata:
            # Slice off the '#' signal character.
            row[0] = row[0][1:]
            if len(row) > 1 and type(row[1]) == str:
                data_dict[row[0].strip()] = row[1].strip()
            elif len(row) > 1:
                data_dict[row[0].strip()] = row[1]
            else:
                data_dict[row[0].strip()] = None
        else:
            for i, item in enumerate(data_headers):
                data_dict[item.strip()].append(float(row[i]))

    # Now we create the new encoded file.
    # At the moment, if there are .csv and .xlsx files with the same base name,
    # one will clobber the other. Could fix this later.
    file_name_split = file_name.split('.')
    json_file_name = file_name_split[0] + '.json'
    with open(folder + json_file_name, 'w') as json_file:
        json.dump(data_dict, json_file)

    return json_file_name


def record_update(folder, new_file_names):
    """After a successful archival action, updates the local record
    with the names of files processed and created.
    """

    with open(folder + record_file_name, 'a') as record_file:
        record_file.write('\n' + '\n'.join(new_file_names))

    return None


try:
    folder_to_check = sys.argv[1]
except:
    folder_to_check = input("""Enter a directory / folder name to scan for
                            new files, then press <Enter>: """)
# Make sure that the folder name has a trailing slash; the processing
# routines implicitly expect this.
if not folder_to_check.endswith('/'):
    folder_to_check = folder_to_check + '/'
files_to_archive = check_update(folder_to_check)
if not files_to_archive:
    print('Folder is up to date.')
else:
    new_file_names = copy(files_to_archive)
    for filename in files_to_archive:
        new_file_names.append(archive_data_file(folder_to_check, filename))
    record_update(folder_to_check, new_file_names)
