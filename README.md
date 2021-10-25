**Table of Contents:**
- [1. BackupSystem](#1-backupsystem)
  - [1.1. Requirements](#11-requirements)
  - [1.2. The Files](#12-the-files)
    - [1.2.1. backfiles.txt](#121-backfilestxt)
    - [1.2.2. data.json](#122-datajson)
    - [1.2.3. .env](#123-env)
    - [1.2.4. The ZIP](#124-the-zip)
  - [1.3. File transfer](#13-file-transfer)
# 1. BackupSystem
The System for making Backups of the GIRC Server. It packs all the files/folders that need to be backed up into a zip-file and sends it to a Backupserver over SFTP (not FTPS!). I there are any questions or bugs feel free to open a issue.

## 1.1. Requirements
The Backupserver will need a folder with the current year-month ('YYYY-mm'). This _can_ be made through Cron (`0 0 1 * * mkdir /path/of/folder/$(date +"%Y-%m")`) or manually.  
The files that are needed in the root of the program are:  
- backfiles.txt
- data.json
- .env  

What the contents of these should be is listed below.  

## 1.2. The Files
### 1.2.1. backfiles.txt
This file holds the files and folders that should be backed up by the program. Every file/folder needs to be written on a seperate line with its exact name, without it's root folder (`./testfolder/testfile.txt > testfile.txt` or `./testfolder/testfolder2 > testfolder2`). You can use a '#' at the first character on a line to make the line a comment and therefore ignored.  

### 1.2.2. data.json
You can either create this file and leave it alone or let the program do it. It stores the SHA256 of all files that have ever been backed up and the last time the backup ran. If you want to backup a file that hasn't changed, delete the corresponding entry in the json.  

### 1.2.3. .env
```
path=<Path of of the folder where the files are in>
host=<domain.backup.server>
port=<Port of Backup Server>
user=<User for FTP connection>
pass=<Password for the user>
```

### 1.2.4. The ZIP
The name of the zip is in the following pattern: `YYYY-mm-dd.zip`. It contains only files that have changed, in order to keep the size and therefore the tranfer time small. If there already ran an update that day, the user will be asked to give the zip a name. That's made so the previous file will not be overwritten. 
## 1.3. File transfer
The zip-file is transfered over SFTP (SSH-FTP). Therefore the Backupserver needs to support SFTP. The Library used is [Paramiko](https://www.paramiko.org/ "Paramiko Website").
