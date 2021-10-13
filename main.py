import ftplib as ftp
import hashlib as hl
import json
import os

from decouple import config

#Load/Setup the json
data = {}
try:
    j = json.load(open('files.json'))
    for key, value in j.items():
        if type(value) == dict and key in data:
            data[key] = implement(value, data[key])
        else:
            data[key] = value
except FileNotFoundError:
    print('Json file not found!')
    exit()
except json.JSONDecodeError:
    print('The JSON is empty!')
    exit()
if not 'sha' in data.keys():
    data['sha'] = {}

#Scan the txt containing the files/folders to backup and put files into list
backfiles = []
try:
    for line in open('backfiles.txt'):
        backfiles.append(line.replace('\n', ''))
        print(backfiles)
except FileNotFoundError:
    print('The file containing the files and folders that should be backed up has not been found!')
    exit()

#Go trough the files, check if the file/folder exists in backfiles list
#If exist: Check the files for their SHA and add folder/file to another list with full path for later zipping
#Else: continue
#Help for os.walk: https://docs.python.org/3/library/os.html#os.walk
ziplist = []
for root, dirs, files in os.walk(config('path')):
    combined = dirs + files
    for f in combined:
        if f in backfiles:
            try:
                _file = open(root + '/' + f, 'rb').read()
                sha = hl.sha256(_file).hexdigest()
                if sha == data['sha'][f]:
                    continue
                else:
                    ziplist.append(root + '/' + f)
                    data['sha'][f] = sha
                    backfiles.remove(f)
            except IsADirectoryError:
                ziplist.append(root + '/' + f + '/')
                backfiles.remove(f)
            except KeyError:
                data['sha'][f] = sha
                ziplist.append(root + '/' + f)
                backfiles.remove(f)
        else:
            continue
print(ziplist)

with open('files.json', 'w') as outfile:
    json.dump(data, outfile)
#Send the zip File to the Backupserver
