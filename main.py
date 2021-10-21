import ftplib as ftp
import hashlib as hl
import json
import os
from datetime import datetime as dt
from zipfile import ZipFile

import paramiko as pk
from decouple import config

# Load/Setup the json
data = {}


def implement(json, data):
    for key, value in json.items():
        if type(value) == dict and key in data:
            data[key] = implement(value, data[key])
        else:
            data[key] = value
    return data


try:
    implement(json.load(open('data.json')), data)
except FileNotFoundError:
    pass
except json.JSONDecodeError:
    pass
if not 'sha' in data.keys():
    data['sha'] = {}
if not 'last' in data.keys():
    data['last'] = '1999-12-01'


# Scan the txt containing the files/folders to backup and put files into list
backfiles = []
try:
    for line in open('backfiles.txt'):
        backfiles.append(line.replace('\n', ''))
except FileNotFoundError:
    print('The file containing the files and folders that should be backed up (backfiles.txt) has not been found!')
    exit()


# Go trough the files, check if the file/folder exists in backfiles list
# If exist: Check the files for their SHA and add folder/file to the zip
# Else: continue
# Help for os.walk: https://docs.python.org/3/library/os.html#os.walk
def add_zip(dir: str, zip: ZipFile, json_data: dict, backf: list):
    for root, dirs, files in os.walk(dir):
        for f in files:
            if f in backf:
                try:
                    filepath = str(root + '/' + f).replace('//', '/')
                    sha = hl.sha256(open(filepath, 'rb').read()).hexdigest()
                    if sha == json_data['sha'][filepath]:
                        backf.remove(f)
                        continue
                    else:
                        json_data['sha'][filepath] = sha
                        zip.write(filepath)
                        backf.remove(f)
                except KeyError:
                    json_data['sha'][filepath] = sha
                    zip.write(filepath)
                    backf.remove(f)
            else:
                continue
        for d in dirs:
            if d in backf:
                backf.remove(d)
                json_data, backf = add_zip(
                    root + '/' + d, zip, json_data, backf)
    return json_data, backf


today = dt.today().strftime('%Y-%m-%d')
if data['last'] == today:
    zipname = input(
        'There already ran a update today!\nWhat should be the name of the file (with .zip, empty for overwrite)?> ')
    if len(zipname) < 5:
        zipname = today + ".zip"
else:
    zipname = today + ".zip"
    data['last'] = today
zipfile = ZipFile(zipname, 'w')
for root, dirs, files in os.walk(config('path')):
    combined = dirs + files
    for f in combined:
        if f in backfiles:
            try:
                filepath = str(root + '/' + f).replace('//', '/')
                sha = hl.sha256(open(filepath, 'rb').read()).hexdigest()
                if sha == data['sha'][filepath]:
                    backfiles.remove(f)
                    continue
                else:
                    zipfile.write(filepath)
                    data['sha'][filepath] = sha
                    backfiles.remove(f)
            except IsADirectoryError:
                data, backfiles = add_zip(
                    filepath + '/', zipfile, data, backfiles)
                backfiles.remove(f)
            except KeyError:
                data['sha'][filepath] = sha
                zipfile.write(filepath)
                backfiles.remove(f)
        else:
            continue
zipfile.close()
if len(backfiles) > 0:
    missing_files = ""
    for i in backfiles:
        missing_files += f'{i}, '
    print(f'Some files/folders have not been found: {missing_files}')
with open('data.json', 'w') as outfile:
    json.dump(data, outfile)


# Send the zip File to the Backupserver and delete it after
ftp = pk.Transport((config('host'), int(config('port'))))
ftp.connect(username=config('user'), password=config('pass'))
sftp = pk.SFTPClient.from_transport(ftp)
sftp.put(f'./{zipname}', 'backups/' +
         dt.today().strftime('%Y-%m') + f'/{zipname}')
sftp.close()
ftp.close()
os.remove(zipname)

print('Backup made.')
