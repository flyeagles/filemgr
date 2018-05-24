# filemgr
File manager

This local web app is to collect file information and store them in local SQLite. Then we can browse those files
without visiting the file system.

## Check Duplication with Files on RAID1 Disk

We can set a disk as RAID1 disk. We then can check whether some files in a given folder are duplicated with files on such RAID1 disk, 
and provide options to delete such tripple-duplicated files.

We use a Table in SQLite to record the ID of RAID1 volumes.

# Supporting Technologies

SQLite3 Syntax Link: https://sqlite.org/doclist.html
Django model migration: https://docs.djangoproject.com/en/2.0/topics/migrations/
