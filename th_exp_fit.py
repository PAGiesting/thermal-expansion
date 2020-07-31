#!/usr/bin/python3

"""Netszch dilatometer themal expansion data extraction and fitting routine.
* It takes a folder / directory name from command line or asks user
* then checks folder's archive record against directory contents
* then processes new data and archives it.
"""

import csv
import sys
import os
import codecs
import openpyxl as xlsx
from copy import copy
from collections import defaultdict
import pickle
import pandas as pd
import numpy as np
from numpy.polynomial import Polynomial

# Degree of polynomial fits
deg = 4
# Simple text file listing of processed directory contents
# with one file name per line.
record_file_name = 'th_exp_data.dat'
# File name for certificate polynomial
cert_file = 'cert_poly.pkl'
# File extension for standard polynomial
stan_file = '_stan_poly.pkl'

def check_update(folder):
    """Checks the folder for new files not listed in its local record.
    Returns a list of new filenames.
    """
    file_names = os.listdir(folder)
    if record_file_name not in file_names:
        with open(folder + record_file_name, 'w') as record_file:
            record_file.write(record_file_name + '\n')
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

def standard_poly(folder,file_names):
    """Checks the list of new file names for a new sapphire standard.
    If none, passes back the existing pickled polynomial.
    If there is one, passes the file to the parser, gets dataframe,
    fits the polynomial, pickles it, and passes it back.
    """
    new_standard = ''
    for name in file_names:
        if 'sapph' in name:
            new_standard = name
    if new_standard == '':
        with open(stan_file,'rb') as cellar:
            stan4 = pickle.load(cellar)
    else:
        st_file_name, stdf = parse_file(folder,new_standard)
        stan4 = Polynomial.fit(stdf.iloc[:,0],stdf['dL/Lo'],deg)
        st_name_split = st_file_name.split('.')
        with open(folder+st_name_split[0]+stan_file,'wb') as cellar:
            pickle.dump(stan4,cellar)
    return stan4

def process_directory(folder, file_names):
    """Loads certificate polynomial from parent folder.
    Calls standard_poly to create or load standard polynomial.
    Calls process_file on each data file to process and archive.
    """
    with open(folder+'../'+cert_file,'rb') as cellar:
        cert4 = pickle.load(cellar)
    stan4 = standard_poly(folder,file_names)
    new_file_names = []
    for name in file_names:
        if 'sapph' not in name:
            new_file_names.extend(process_file(folder, name, cert4, stan4))
    return new_file_names

def parse_file(folder, file_name):
    """Reads in a data file, processes it into a string and a dataframe,
    then dumps the string to a text file and returns the dataframe.
    """
    # Routine to check file type and read data.
    # In the Netszch data files, the header line for the actual
    # data starts with a double #, while the metadata lines
    # start with #, and the data lines start with a space.
    # Metadata has a ton of whitespace to strip().
    #
    # Kate tells me that the Netszch csv data files are encoded in
    # ISO-8859-15. The Python documentation is damnably coy on how
    # to set the encoding for the csv reader or file opener, but I
    # eventually tracked it down. The routine leaves the degree symbol
    # as \u00b0 and the letter mu (micro) as \u00b5.
    # There is also a blank line right before the ## line with
    # a NUL byte, which is fixed via the generator replace().
    #
    # The xlsx files cannot be coped with via "csv.reader(... dialect
    # = 'excel')" and require openpyxl [as xlsx]. This routine leaves
    # both of the disputed characters as \ufffd.
    print(file_name)
    if file_name.endswith('.csv'):
        with open(folder + file_name,'r',encoding='iso_8859_15',errors='ignore') \
            as raw_file:
            raw_csv = csv.reader((line.replace('\0','') for line in raw_file),
                                 skipinitialspace=True, delimiter=',')
            raw_data = list(raw_csv)        
    elif file_name.endswith('.xlsx'):
        raw_wb = xlsx.load_workbook(folder + file_name)
        raw_data = []
        for row in raw_wb.active.values:
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
    metadata_text = []
    metadata = True
    for row in raw_data:
        # To cope with the blank line.
        # A .csv file generates an empty list there.
        # An .xlsx file would generate a line of None values,
        # but those are knocked out by the filter above.
        if len(row) == 0:
            pass
        elif type(row[0]) == str and row[0].startswith('##'):
            metadata = False
            print(row)
            # Slice off the '##' signal characters. 
            row[0] = row[0][2:]
            # Initialize the dataframe to receive values.
            # Only take the first three columns. Any fourth columns are alphas
            # calculated by the instrument software and Anne does not regard
            # them as reliable.
            df = pd.DataFrame(columns=row[0:3])
        elif metadata:
            # Slice off the '#' signal character.
            row[0] = row[0][1:]
            if len(row) > 1 and type(row[1]) == str:
                metadata_text.append(row[0].strip()+' '+row[1].strip())
            elif len(row) > 1:
                metadata_text.append(row[0].strip()+' '+str(row[1]))
            else:
                metadata_text.append(row[0].strip())
        else:
            newdata = np.array([float(row[0]),float(row[1]),float(row[2])])
            newline = pd.DataFrame(newdata.reshape(1,3),columns=df.columns)
            df = df.append(newline)
    # Now we create the new text file.
    # To avoid clobbering, if the original file was a csv, suffix 'c' to
    # the base file name, 'x' for xlsx.
    file_name_split = file_name.split('.')
    if file_name_split[-1] == 'xlsx':
        suffix = 'x.txt'
    else:
        suffix = 'c.txt'
    text_file_name = file_name_split[0] + suffix
    with open(folder+text_file_name,'w',encoding='utf-8',errors='ignore') as text_file:
        text_file.write('\n'.join(metadata_text))
    return text_file_name, df

def process_file(folder, file_name, cert4, stan4):
    """Passes file name to parse_file to archive metadata and retrieve data.
    Add column of corrected data with certificate and standard to dataframe.
    Calculate delta T and averaged / engineering alpha.
    Fit the corrected data with a polynomial.
    Calculate derivative = alpha at each temperature.
    Dump corrected dataframe to csv.
    Pass back the metadata and data file names."""
    text_file_name, ddf = parse_file(folder, file_name)
    # Note that the Temp/oC column is passed as iloc[:,0]
    # because of the special degree character I don't want to deal with.
    ddf['Certificate'] = cert4(ddf.iloc[:,0])
    ddf['Standard'] = stan4(ddf.iloc[:,0])
    ddf['Corrected'] = ddf['dL/Lo']+ddf['Certificate']-ddf['Standard']
    ddf['delT'] = ddf.iloc[:,0].apply(lambda x: x - ddf.iloc[0,0])
    ddf['EngAlpha'] = ddf['Corrected'] / ddf['delT']
    data4 = Polynomial.fit(ddf.iloc[:,0],ddf['Corrected'],deg)
    ddf['Fitted'] = data4(ddf.iloc[:,0])
    alpha3 = data4.deriv()
    ddf['Alpha'] = alpha3(ddf.iloc[:,0])
    file_name_split = text_file_name.split('.')
    csv_file_name = file_name_split[0]+'.csv'
    ddf.to_csv(folder+csv_file_name)
    # not sure whether it's better to pass back as two entities
    # or a two entity list
    return [text_file_name, csv_file_name]

def record_update(folder, new_file_names):
    """After a successful archival action, updates the local record
    with the names of files processed and created.
    """
    with open(folder + record_file_name, 'a') as record_file:
        record_file.write('\n'.join(new_file_names))
    return None

# Take a folder / directory name from command line or ask user
try:
    folder_to_check = sys.argv[1]
except:
    folder_to_check = input("""Enter a directory / folder name to scan for
                            new files, then press <Enter>: """)
# Make sure that the folder name has a trailing slash; the processing
# routines implicitly expect this.
if not folder_to_check.endswith('/'):
    folder_to_check = folder_to_check + '/'

# Check folder's archive record against directory contents
files_to_archive = check_update(folder_to_check)
if not files_to_archive:
    print('Folder is up to date.')
else:
# Process new data and archive it.
# Processing steps:
# <root function process_directory>
# * Import certificate polynomial from data/ directory (root)
# * If there is a new standard file in this directory, fit a polynomial to it.
#    Dump this polynomial to a pickle file.
# * If there is not a new standard file, load the old standard polynomial.
# * For each new data file:
# <secondary function process_file>
#    * Parse the metadata.
#    * Control for clobbering: add a suffix to indicate csv or xlsx input.
#    * Dump metadata to a text file.
#    * Read in the data to a new pandas dataframe.
#    * Use certificate and standard to correct data at each temperature point.
#    * Calculate delta-T and average (engineering) alpha at each temperature.
#    * Fit polynomial to the corrected data.
#    * Store instantaneous alpha (derivative) at each temperature point.
#    * Dump dataframe to a CSV file.
#    * File base names are the same as the input data file.
    new_file_names = process_directory(folder_to_check,files_to_archive)
# Update the record file.
    record_update(folder_to_check,new_file_names)