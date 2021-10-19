# BackupSystem
The System for making Backups of the GIRC Server.  
The Backupserver will need a folder with the current year-month ('YYYY-mm'). This _can_ be made through Cron (`0 0 1 * * mkdir /path/of/folder/$(date +"%Y-%m")`) or manually.
## The .env file
```
path="<Path of of the folder where the files are in>"
host="<domain.backup.server>"
port="<Port of Backup Server>"
user="<User for FTP connection>"
pass="<Password for the user>"
```
