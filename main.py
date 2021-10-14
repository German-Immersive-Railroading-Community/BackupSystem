import ftplib as ftp
import hashlib as hl
import json
import os
from zipfile import ZipFile

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
    pass
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
except FileNotFoundError:
    print('The file containing the files and folders that should be backed up has not been found!')
    exit()

#Go trough the files, check if the file/folder exists in backfiles list
#If exist: Check the files for their SHA and add folder/file to the zip
#Else: continue
#Help for os.walk: https://docs.python.org/3/library/os.html#os.walk
def add_zip(dir : str, zip : ZipFile, json_data : dict, backf : list):
    for root, dirs, files in os.walk(dir):
        for f in files:
            if f in backf:
                try:
                    sha = hl.sha256(open(root + '/' + f, 'rb').read()).hexdigest()
                    if sha == json_data['sha'][root + '/' + f]:
                        continue
                    else:
                        json_data['sha'][root + '/' + f] = sha
                        zip.write(root + '/' + f)
                        backf.remove(f)
                except KeyError:
                    json_data['sha'][root + '/' + f] = sha
                    zip.write(root + '/' + f)
                    backf.remove(f)
            else:
                continue
        for d in dirs:
            if d in backf:
                backf.remove(d)
                json_data, backf = add_zip(root + '/' + d, zip, json_data, backf)
    return json_data, backf


zipfile = ZipFile('backup.zip', 'w')
for root, dirs, files in os.walk(config('path')):
    combined = dirs + files
    for f in combined:
        if f in backfiles:
            try:
                sha = hl.sha256(open(root + '/' + f, 'rb').read()).hexdigest()
                if sha == data['sha'][root + '/' + f]:
                    continue
                else:
                    zipfile.write(root + '/' + f)
                    data['sha'][root + '/' + f] = sha
                    backfiles.remove(f)
            except IsADirectoryError:
                data, backfiles = add_zip(root + '/' + f + '/', zipfile, data, backfiles)
                backfiles.remove(f)
            except KeyError:
                data['sha'][root + '/' + f] = sha
                zipfile.write(root + '/' + f)
                backfiles.remove(f)
        else:
            continue
zipfile.close()
with open('files.json', 'w') as outfile:
    json.dump(data, outfile)


#Send the zip File to the Backupserver


print('Backup made.')