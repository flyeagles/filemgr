import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import watchdog.events
import os
import stat
import sqlite3

import wmi
import pythoncom

from fileondisk.systeminfo import HardDiskInformation, RawSystemInformation
from fileondisk import fodconfigs


db_file_name = ".\\db.sqlite3"
hd_list = HardDiskInformation()
vol_list = RawSystemInformation()


'''
with connection.cursor() as cur:
    cur.executemany('' 'INSERT INTO fileondisk_fileinfo
    (fname, size, file_type, mod_time, folder, fullvolpath, volume_id)
    values(?,?,?,?,?,?,?)'' ', self.file_info_list)
'''

class DatabaseExecutor:
    def __init__(self, db_file):
        """ create a database connection to the SQLite database
            specified by the db_file
        :param db_file: database file
        """
        try:
            self.conn = sqlite3.connect(db_file)

            # enforce foreign key constraint
            cur = self.conn.cursor()
            cur.execute("pragma foreign_keys = on")
        except sqlite3.Error as dberror:
            print(dberror)
            raise
    
    def __enter__(self):
        return self.conn.__enter__()

    def __exit__(self, in_p1, in_p2, in_p3):
        return self.conn.__exit__(in_p1, in_p2, in_p3)

    def get_connectio(self):
        return self.conn

    def select_plain(self, sql_statement):
        """
        Execute select sql statement and return result
        :param sql_statement: the SQL statement string
        :return: result table, a list of tuples of fields.
        """
        cur = self.conn.cursor()
        #cur.execute("SELECT * FROM tasks WHERE priority=?", (priority,))
        cur.execute(sql_statement)
        rows = cur.fetchall()
        return rows

    def execute(self, sql_statement):
        """
        Execute non-select sql statement.
        :param sql_statement: the SQL statement string
        :return:
        """
        cur = self.conn.cursor()
        #cur.execute("SELECT * FROM tasks WHERE priority=?", (priority,))
        cur.execute(sql_statement)

    def executemany(self, sql_statement, params):
        """
        Execute non-select sql statement.
        :param sql_statement: the SQL statement string
        :return:
        """
        cur = self.conn.cursor()
        #cur.execute("SELECT * FROM tasks WHERE priority=?", (priority,))
        cur.executemany(sql_statement, params)

'''
fname=diritem, size=statdata[stat.ST_SIZE], file_type=file_type,
                                mod_time=statdata[stat.ST_MTIME], 
                                folder=str(in_volume.id) + top[2:],
                                fullvolpath=str(in_volume.id) + os.path.join(top[2:], diritem),
                                volume_id=in_volume)
'''

class FODFileSystemEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, dbfile):
        self.dbfile = dbfile

    def deleteitem(self, path):
        volume_id = vol_list.get_volume_id(path[:2].upper())

        db_exec = DatabaseExecutor(db_file_name)
        with db_exec:
            delete_sql = '''delete from fileondisk_fileinfo where fullvolpath like '{fvp}%' '''.format(fvp=str(volume_id)+path[2:])
            db_exec.execute(delete_sql)
        

    def modifyitem(self, path, is_dir):
        try:
            statdata = os.stat(path)
        except FileNotFoundError as err:
            print(err)
            print("Skip missing file: {fn}".format(fn=path))
            return

        if is_dir:
            file_type = 'fold'
        else:
            dotpos = path.rfind('.')
            file_type = ''
            if dotpos > -1:
                file_type = path[dotpos+1:].upper()
            
        (topf, diritem) = os.path.split(path)
        if 'db.sqlite' in diritem:
            return

        volume_id = vol_list.get_volume_id(path[:2].upper())

        fullvolpath = str(volume_id) + path[2:]

        db_exec = DatabaseExecutor(db_file_name)
        with db_exec:
            delete_sql = '''delete from fileondisk_fileinfo where fullvolpath = '{fvp}' '''.format(fvp=fullvolpath)
            db_exec.execute(delete_sql)
            insert_sql = '''insert into fileondisk_fileinfo(fname, size, file_type, mod_time, folder, fullvolpath, volume_id)
                values(?,?,?,?,?,?,?)'''
            db_exec.executemany(insert_sql, [(diritem, statdata[stat.ST_SIZE], file_type, statdata[stat.ST_MTIME], 
                            str(volume_id) + topf[2:],
                            fullvolpath,  volume_id, )])

        print("Finish modification")
        


    def on_created(self, event):
        print("created " + str(event))
        print(event.src_path)
        
        self.modifyitem(event.src_path, event.is_directory)
        
    def on_deleted(self, event):
        print("deleted " + str(event))
        print(event.src_path)
        self.deleteitem(event.src_path)


    def on_modified(self, event):
        print("modified " + str(event))
        print(event.src_path)

        self.modifyitem(event.src_path, event.is_directory)


    def on_moved(self, event):
        print("moved " + str(event))
        print(event.src_path)

        self.deleteitem(event.src_path)
        self.modifyitem(event.dest_path, event.is_directory)


if __name__ == "__main__":

    print(os.getcwd())


    '''
    select * from fileondisk_crawlroot fc  join fileondisk_volume fv
    where fc.volume_id = fv.id 
     and fv.disk_id in ('2020202020202020202020203357323752574638', '202020202020202020202020335732374258484e')
    '''
    db_exec = DatabaseExecutor(db_file_name)
    with db_exec:
        select_sql = '''select fullvolpath from fileondisk_crawlroot fc  join fileondisk_volume fv
            where fc.volume_id = fv.id 
            and fv.disk_id in ('{cent}')'''.format(cent="','".join(hd_list.get_hd_serial_no_list()))
        path_table = db_exec.select_plain(select_sql)
        path_list = [row[0] for row in path_table]

    monitor_folders = []
    for path in path_list:
        split_list = path.split('\\')
        vol_id = split_list[0]
        otherpath = split_list[1:]
        monitor_folders.append(os.path.join(vol_list.get_drive(int(vol_id)), '\\', '\\'.join(otherpath)))

    print(monitor_folders)

    '''
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    '''
    event_handler = FODFileSystemEventHandler(None)
    observer = Observer()
    for path in monitor_folders:
        print("Observing {fd}".format(fd=path))
        observer.schedule(event_handler, path, recursive=True)

    observer.start()
    #    observer_list.append(observer)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

    print(os.getcwd())
    originalfile = fodconfigs.get_original_folder()
    if originalfile:
        print("Copy RAM db back to original db file " + originalfile)
        os.system("copy db.sqlite3 " + originalfile)

    # dummy comment
