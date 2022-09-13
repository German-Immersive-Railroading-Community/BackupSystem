import argparse as ap
import configparser as cp
import ftplib as ftp
import hashlib as hl
import json
import logging as lg
import os
import time
from datetime import datetime as dt
from zipfile import ZipFile

import paramiko as pk

# Parse the CLAs
parser = ap.ArgumentParser('Parses arguments')
parser.add_argument('--unattended', type=bool, default=True,
                    help='Enables/Disables the unattended mode (Default: True)')
args = vars(parser.parse_args())
unattended = args['unattended']

# Setting up and reading the config
config = cp.ConfigParser()
config.read("config.ini")
config_variables = config["VARIABLES"]
config_options = config["OPTIONS"]
sha_check = config_options.getboolean('sha_check')

# Set some time variables
today = dt.today().strftime('%Y-%m-%d')
now = dt.now()
current_time = now.strftime('%H:%M:%S')

# Prepare the logging
logname = f'logs/{today}({current_time}).log'
if not os.path.exists('./logs/'):
    os.mkdir('./logs/')
open(logname, 'a').close()

# Set up logging
log_level = str(config_variables["log_level"]).upper()
lg.basicConfig(filename=logname, level=log_level,
               format='%(asctime)s : %(message)s', datefmt='%I:%M:%S')

lg.info('Preparing...')

# Load/Setup the json
data = {}


def implement(json, data):
    """Loads data from a JSON"""
    lg.info('Reading data from data.json')
    for key, value in json.items():
        if type(value) == dict and key in data:
            data[key] = implement(value, data[key])
        else:
            data[key] = value
    return data


try:
    implement(json.load(open(config_variables["data_path"])), data)
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
    for line in open(config_variables["backfiles"]):
        if list(line)[0] == '#':
            continue
        else:
            lg.debug(line)
            os.path.normpath(path=line)
            backfiles.append(line.replace('\n', ''))
except FileNotFoundError:
    lg.critical(
        'The file containing the files and folders that should be backed up (backfiles.txt) has not been found!')
    exit()
lg.info('Done reading backfiles.txt')

if data['last'] == today:
    lg.info('Detected that there already ran an update today; asking for new name...')
    if unattended:
        lg.info('Program running in unattended mode; adding time to name')
        zipname = f'{today}({current_time}).'
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

# Go trough the files, check if the file/folder exists in backfiles list
# If exist: Check the files for their SHA (or not, depending on the option)
# and add folder/file to the zip
# Else: continue
# Help for os.walk: https://docs.python.org/3/library/os.html#os.walk


def add_folder_to_zip(zip_file: ZipFile, folder):
    """Adds a whole folder to a zip file"""
    for root, dirs, files in os.walk(folder):
        for file in files:
            zip_file.write(os.path.join(root, file))
        for directory in dirs:
            add_folder_to_zip(zip_file, os.path.join(root, directory))


def add_files_to_zip(zip_file: ZipFile, folder):
    """Adds all files in a folder to a zip file when conditions are met"""
    for root, dirs, files in os.walk(folder):
        for file in files:
            file_with_path = os.path.join(root, file)
            if file_with_path in backfiles:
                if sha_check:
                    with open(file_with_path, 'rb') as f:
                        sha = hl.sha256(f.read()).hexdigest()
                    if file_with_path not in data['sha'].keys():
                        data['sha'][file_with_path] = sha
                        lg.debug(f'Adding {file_with_path} to the sha list')
                        zip_file.write(file_with_path)
                        lg.info(f'Added {file_with_path} to the zip')
                    elif sha != data['sha'][file_with_path]:
                        zip_file.write(file_with_path)
                        lg.info(f'Added {file_with_path} to the zip')
                    else:
                        lg.info(
                            f'{file_with_path} has not been changed since last backup')
                else:
                    lg.debug(f'Adding {file} to zip')
                    zip_file.write(file_with_path)
        for directory in dirs:
            if os.path.join(root, directory) in backfiles:
                add_folder_to_zip(zip_file, os.path.join(root, directory))
            else:
                add_files_to_zip(zip_file, os.path.join(root, directory))


lg.info('Starting to zip files...')
start_time = time.time()
with ZipFile(zipname, 'w') as ZIP_FILE:
    add_files_to_zip(ZIP_FILE, config_variables["root_path"])

runtime = time.time() - start_time
lg.info(f'Done writing to {zipname}; took {runtime} seconds.')
lg.info('Updating data.json')
with open(config_variables["data_path"], 'w') as outfile:
    json.dump(data, outfile)


# Send the zip File to the Backupserver and delete it after
lg.info('Starting transfer')
start_time = time.time()
ftp = pk.Transport((config_variables["host"], int(config_variables["port"])))
lg.debug('Set up FTP object')
ftp.connect(username=config_variables["user"],
            password=config_variables["pass"])
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
