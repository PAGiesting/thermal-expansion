#!/usr/bin/python3

"""Collects processed data files from the th_exp_fit script and copies them from
subdirectories of the data directory into the main directory.
"""

import os
import shutil
import json
import datetime

# Task 1: Identify all processed files with c.txt or x.txt endings.
# List all subdirectories. Store "leaf" subdirectory names as keys
# and matching file names in a value list. Skip sapphire standards.
listing = {}
for root, dirs, files in os.walk('data'):
    if dirs != []:
        continue
    listing[root]=list(filter(lambda s: (s.endswith('c.csv') | s.endswith('x.csv'))
        & ('sapph' not in s),files))

# Task 2: Store the current data file listing as a json
today = datetime.date.today()
with open('data/'+str(today.toordinal())+'.dat','w') as datfile:
    json.dump(listing,datfile)

# Task 3: Copy new files up to the main 'data' directory
for subdir in listing.keys():
    for filename in listing[subdir]:
        if os.path.exists('data/'+filename):
            continue
        shutil.copy2(subdir+'/'+filename,'data/'+filename)