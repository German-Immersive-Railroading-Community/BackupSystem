**Table of Contents:**
- [1. BackupSystem](#1-backupsystem)
  - [1.1. Requirements](#11-requirements)
  - [1.2. The Files](#12-the-files)
    - [1.2.1. backfiles.txt](#121-backfilestxt)
    - [1.2.2. data.json](#122-datajson)
    - [1.2.3. config.ini](#123-configini)
    - [1.2.4. The ZIP](#124-the-zip)
  - [1.3. File transfer](#13-file-transfer)
  - [1.4. Command line arguments](#14-command-line-arguments)
  - [1.5. Future features](#15-future-features)
# 1. BackupSystem
A universal system for making Backups of the GIRC Server. It packs all the files/folders that need to be backed up into a zip-file and sends it to a Backupserver over SFTP (not FTPS!). If there are any questions or bugs feel free to open an issue.

## 1.1. Requirements
The Backupserver will need a folder with the current year-month ('YYYY-mm'). This _can_ be made through Cron or manually.  
The files that are needed are:  
- [backfiles.txt](#121-backfilestxt)
- [data.json](#122-datajson)
- [config.ini](#123-configini)

What the contents of these are and where they are saved is listed below.  

## 1.2. The Files
### 1.2.1. backfiles.txt
This file holds the files and folders that should be backed up by the program. Every file/folder needs to be written on a seperate line with its exact name, without it's root folder (`./testfolder/testfile.txt > testfile.txt` or `./testfolder/testfolder2 > testfolder2`). You can use a '#' at the first character on a line to make the line a comment and therefore ignored. It can be anywhere, but the path needs to be specified in the [config.ini](#123-configini).

### 1.2.2. data.json
You can either create this file in the program rundirectory and leave it alone or let the program do it. It stores the SHA256 of all files that have ever been backed up and the last time the backup ran. If you want to backup a file that hasn't changed, delete the corresponding entry in the json or turn off the SHA-Check in the [config](#123-configini) (DISCLAIMER: This will backup all files, no matter if new/changed or not).  

### 1.2.3. config.ini
An example can be found [in the Repo](config.ini). It's pretty self-explanatory.

### 1.2.4. The ZIP
The name of the zip is in the following pattern: `YYYY-mm-dd.zip`. By default (changeable in the [config](#123-configini)), it contains only files that have changed, in order to keep the size and therefore the tranfer time small. If there already ran an update that day, the user will be asked to give the zip a name. That's made so the previous file will not be overwritten. If the [unattended mode](#14-command-line-arguments) is turned on, the program will handle this situation itself.
## 1.3. File transfer
The zip-file is transfered over SFTP (SSH-FTP). Therefore the Backupserver needs to support SFTP. The Library used is [Paramiko](https://www.paramiko.org/ "Paramiko Website").

## 1.4. Command line arguments  
There currently is only one CLA: The unattended mode. In this mode, which is default on, the program will not take user input (when required) and handle these situations itself so the program can make it's backup. When there already ran updates, it will add the time of the backup to the name of the ZIP.

## 1.5. Future features  
A list of what should come can be found on [Trello](https://trello.com/b/MbPKL9sD/backupsystem). If you like, you're invited to help integrate these features or make new suggestions. For that, please create an Issue here on GitHub.
