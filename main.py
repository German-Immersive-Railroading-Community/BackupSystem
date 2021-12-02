import argparse as ap
import ftplib as ftp
import hashlib as hl
import json
import logging as lg
import os
import time
from datetime import datetime as dt
from zipfile import ZipFile

import paramiko as pk
from decouple import config

parser = ap.ArgumentParser('Parses arguments')
parser.add_argument('--unattended', type=bool, default=True,
                    help='Enables/Disables the unattended mode (Default: True)')
args = vars(parser.parse_args())
unattended = args['unattended']

today = dt.today().strftime('%Y-%m-%d')
now = dt.now()
current_time = now.strftime('%H%M%S')
logname = 'logs/' + today + '.log'

if not os.path.exists('./logs/'):
    os.mkdir('./logs/')

open(logname, 'a').close()


log_level = str(config('log_level')).upper()
lg.basicConfig(filename=logname, level=log_level,
               format='%(asctime)s : %(message)s', datefmt='%I:%M:%S')

lg.info('Preparing...')
# Load/Setup the json
data = {}


def implement(json, data):
    lg.info('Reading data from data.json')
    for key, value in json.items():
        if type(value) == dict and key in data:
            data[key] = implement(value, data[key])
        else:
            data[key] = value
    return data


try:
    implement(json.load(open(config('data_path'))), data)
except FileNotFoundError:
    lg.warning('data.json not found; creating...')
except json.JSONDecodeError:
    lg.warning('There was something wrong with the data.json; fixing...')
if not 'sha' in data.keys():
    data['sha'] = {}
if not 'last' in data.keys():
    lg.warning('No last update date found; setting standard')
    data['last'] = '1999-12-01'


# Scan the txt containing the files/folders to backup and put files into list
backfiles = []
try:
    lg.info('Reading backfiles.txt...')
    for line in open(config('backfiles')):
        if list(line)[0] == '#':
            continue
        else:
            lg.debug(line)
            backfiles.append(line.replace('\n', ''))
except FileNotFoundError:
    lg.critical(
        'The file containing the files and folders that should be backed up (backfiles.txt) has not been found!')
    exit()
lg.info('Done reading backfiles.txt')

# Go trough the files, check if the file/folder exists in backfiles list
# If exist: Check the files for their SHA and add folder/file to the zip
# Else: continue
# Help for os.walk: https://docs.python.org/3/library/os.html#os.walk


def add_zip(dir: str, zip: ZipFile, json_data: dict, backf: list, include_all: bool = True):
    for root, dirs, files in os.walk(dir):
        for f in files:
            if include_all:
                filepath = str(root + '/' + f).replace('//', '/')
                lg.debug(f'''"Include all" is true; backing up {filepath} ''')
                filepath_local = filepath.replace(config('path'), '')
                json_data['sha'][filepath_local] = hl.sha256(
                    open(filepath, 'rb').read()).hexdigest()
                zip.write(filepath, filepath_local)
            else:
                if f in backf:
                    lg.debug(f'{f} has been found in backfiles; backing up')
                    try:
                        filepath = str(root + '/' + f).replace('//', '/')
                        sha = hl.sha256(
                            open(filepath, 'rb').read()).hexdigest()
                        if sha == json_data['sha'][filepath_local]:
                            lg.debug('''SHA didn't change; ignoring ''')
                            backf.remove(f)
                            continue
                        else:
                            lg.debug('SHA changed; adding to zip')
                            json_data['sha'][filepath_local] = sha
                            zip.write(filepath, filepath_local)
                            backf.remove(f)
                    except KeyError:
                        lg.debug('No old SHA found; adding')
                        json_data['sha'][filepath_local] = sha
                        zip.write(filepath, filepath_local)
                        backf.remove(f)
                else:
                    lg.debug(f'{f} not found in backfiles; ignoring')
                    continue
        for d in dirs:
            lg.debug(f'Backing up the folders in {dir}')
            if d in backf:
                backf.remove(d)
                json_data, backf = add_zip(
                    root + '/' + d, zip, json_data, backf)
    return json_data, backf


if data['last'] == today:
    lg.info('Detected that there already ran an update today; asking for new name...')
    if unattended:
        lg.info('Program running in unattended mode; adding time to name')
        zipname = f'{today}({current_time}).zip'
    else:
        zipname = input(
            'There already ran a update today!\nWhat should be the name of the file (with .zip, empty for overwrite)?> ')
        if len(zipname) < 5:
            zipname = today + ".zip"
            lg.info('No name given; overwriting...')
else:
    lg.info('No update ran today.')
    zipname = today + ".zip"
    data['last'] = today
    lg.info(f'Zip name: {zipname}')
zipfile = ZipFile(zipname, 'w')
lg.info(f'Done preparing; start writing to {zipname}')
start_time = time.time()
for root, dirs, files in os.walk(config('path')):
    combined = dirs + files
    lg.debug(f'Found dirs/files: {combined}')
    for f in combined:
        if f in backfiles:
            lg.debug(f'{f} has been found in backfiles; backing up')
            try:
                filepath = str(root + '/' + f).replace('//', '/')
                filepath_local = filepath.replace(config('path'), '')
                lg.debug('Getting SHA')
                sha = hl.sha256(open(filepath, 'rb').read()).hexdigest()
                if sha == data['sha'][filepath_local]:
                    lg.debug('''SHA didn't change; ignoring ''')
                    backfiles.remove(f)
                    continue
                else:
                    lg.debug('SHA changed; adding to zip')
                    zipfile.write(filepath, filepath_local)
                    data['sha'][filepath_local] = sha
                    backfiles.remove(f)
            except IsADirectoryError:
                lg.debug(f'{f} is a directory; backing up')
                data, backfiles = add_zip(
                    filepath + '/', zipfile, data, backfiles)
                backfiles.remove(f)
            except KeyError:
                lg.debug('No old SHA found; adding')
                data['sha'][filepath_local] = sha
                zipfile.write(filepath, filepath_local)
                backfiles.remove(f)
        else:
            lg.debug(f'{f} not found in backfiles; ignoring')
            continue
zipfile.close()
runtime = time.time() - start_time
lg.info(f'Done writing to {zipname}; took {runtime} seconds.')
if len(backfiles) > 0:
    missing_files = ""
    for i in backfiles:
        missing_files += f'{i}, '
    lg.warning(f'Some files/folders have not been found: {missing_files}')
lg.info('Updating data.json')
with open(config('data_path'), 'w') as outfile:
    json.dump(data, outfile)


# Send the zip File to the Backupserver and delete it after
lg.info('Starting transfer')
start_time = time.time()
ftp = pk.Transport((config('host'), int(config('port'))))
lg.debug('Set up FTP object')
ftp.connect(username=config('user'), password=config('pass'))
sftp = pk.SFTPClient.from_transport(ftp)
lg.info(f'Sending {zipname}...')
sftp.put(f'./{zipname}', 'backups/' +
         dt.today().strftime('%Y-%m') + f'/{zipname}')
lg.info(f'Done sending {zipname}')
sftp.close()
ftp.close()
runtime = time.time() - start_time
lg.info(f'Done transfering; took {runtime} seconds.')
os.remove(zipname)
lg.info(f'Deleted {zipname}')

lg.info('Backup made.')
