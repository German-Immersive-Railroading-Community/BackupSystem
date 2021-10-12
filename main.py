import ftplib as ftp
import hashlib as hl
import json

from decouple import config

#Load/Setup the json
data = {}
try:
    with open('files.json', 'r') as json_file:
        j = json.loads(json_file)
        for key, value in j.items():
            if type(value) == dict and key in data:
                data[key] = implement(value, data[key])
            else:
                data[key] = value
except FileNotFoundError:
    print('Json file not found!')
    exit()

#Scan the txt containing the files/folders to backup and put files into list
backfiles = []
try:
    for line in open('backfiles.txt'):
        backfiles.append(line.replace('\n', ''))
except FileNotFoundError:
    print('The file containing the files and folders that should be backed up has not been found!')
    exit()

#Go trough the files, check if the file/folder exists in a list
#If exist: Check the files for their SHA and add folder/file to another list with full path for later zipping
#Else: continue
#Help for os.walk: https://docs.python.org/3/library/os.html#os.walk
testlist = []
for root, dirs, files in os.walk(config('path')):
    print(dirs)
    print(files)

#Send the zip File to the Backupserver
