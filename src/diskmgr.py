import shutil
import argparse

import os, sys
import stat
import re

import sqlite3
import subprocess


import wmi



class DiskError(BaseException):
    def __init__(self, msg):
        self.msg = msg

    def get_msg(self):
        return self.msg


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

    def noselect_plain(self, sql_statement):
        """
        Execute non-select sql statement.
        :param sql_statement: the SQL statement string
        :return:
        """
        cur = self.conn.cursor()
        #cur.execute("SELECT * FROM tasks WHERE priority=?", (priority,))
        cur.execute(sql_statement)


class SystemInformation:
    def __init__(self, in_db):
        self.db_exec = in_db
        self.wmi_conn = wmi.WMI()

        # we need query the system to get all the disks and volumes of the system
        self.disk_to_vol = dict()
        self.hard_disks = self.wmi_conn.Win32_DiskDrive()
        for hard_disk in self.hard_disks:
            self.disk_to_vol[hard_disk.Index] = []
            for part in hard_disk.associators("Win32_DiskDriveToDiskPartition"):
                vols = part.associators("Win32_LogicalDiskToPartition")
                if vols:  # vols is not []
                    self.disk_to_vol[hard_disk.Index] += vols

    def chr_incr(self, in_char, incr):
        return chr(ord(in_char)+incr)


    def save_volumeinfo(self, drive):
        print(drive)
        for disk in self.hard_disks:
            dev_id = self.chr_incr('a', disk.Index)
            # first, add data to diskinfo table
            (alert, smart_info) = self.query_drive_state('hd' + dev_id)
            print(smart_info)

            print(disk.Model)
            '''
                serial_no text,
                model text,
                disk_index integer,
                size integer,
                partitions integer,
                SMART_pass integer,
                SMART_info text,
                machine text,
                media_type text,
                primary key (model)
            '''
            INSERT_SQL = '''insert or replace into
                diskinfo(serial_no, model, disk_index, size, partitions, SMART_pass, SMART_info, machine, media_type)
                values('{sno}','{model}',{did}, {sz},{parts},{pa},'{SMART}', '{mach}', '{media}')
                '''.format(sno=disk.SerialNumber, model=disk.Model, did=int(disk.Index), sz=int(disk.Size), 
                            parts=disk.Partitions,
                            pa=1-alert, SMART=',\n'.join(smart_info),
                            mach=disk.SystemName, media=disk.MediaType)
            self.db_exec.noselect_plain(INSERT_SQL)

            
            for volume in self.disk_to_vol[disk.Index]:
                print(volume)
                if volume.Caption == drive:

                    print(volume.Caption + "=>" + volume.VolumeSerialNumber)
                    print(volume)

                    intval = int(volume.VolumeSerialNumber, 16)

                    '''
                        id integer, -- value of volume serial number
                        volume_name text,
                        size integer,
                        size_free integer,
                        disk_no text,
                    '''
                    INSERT_SQL = '''insert or replace into
                        volumeinfo(id, volume_name, size, size_free, disk_no)
                        values({id},'{vname}',{sz},{szfree},'{dm}')
                        '''.format(id=intval, vname=volume.VolumeName, sz=int(volume.Size),
                                   szfree=int(volume.FreeSpace), dm=disk.SerialNumber)
                    self.db_exec.noselect_plain(INSERT_SQL)

                    return intval

        raise DiskError("Cannot find drive " + drive)


    def query_drive_state(self, drive_id):
        p = subprocess.Popen(["smartctl", "-a", "/dev/" + drive_id], 
                            stdout=subprocess.PIPE)
        (output, err) = p.communicate()

        drive_results = []
        alert = 0

        for line in output.splitlines():
            line = str(line)
            # 'Device Model:     SAMSUNG MZMTD256HAGM-000L1'
            if "Device Model" in line:
                value = re.search(r":\s+(\S.+?)'", line).group(1)
                drive_results.append("Device Model: " + str(value))
            elif "Model Family" in line:
                value = re.search(r":\s+(\S.+?)'", line).group(1)
                drive_results.append("Model Family: " + str(value))
            elif "Rotation Rate" in line:
                value = re.search(r":\s+(\S.+?)'", line).group(1)
                drive_results.append("Rotation Rate: " + str(value))
            elif "Form Factor" in line:
                value = re.search(r":\s+(\S.+?)'", line).group(1)
                drive_results.append("Form Factor: " + str(value))
            elif "Reallocated_Sector_Ct" in line:
                value = re.search(r" - (.+?)'", line).group(1)
                drive_results.append("Reallocated sector count: " + str(int(value)))
                if int(value) > 0:
                    alert = 1
            elif "Power_On_Hours" in line:
                value = re.search(r" - (.+?)'", line).group(1)
                drive_results.append("Power_On_Hours: " + str(int(value)))
            elif "Airflow_Temperature_Cel" in line:
                value = re.search(r" - (.+?)'", line).group(1)
                drive_results.append("Airflow_Temperature_Cel: " + str(value))  # eg. 34 (Min/Max 30/43)
            elif "Wear_Leveling_Count" in line:
                value = re.search(r" - (.+?)'", line).group(1)
                drive_results.append("Wear leveling count: " + str(int(value)))
            elif "Reallocated_Event_Count" in line:
                value = re.search(r" - (.+?)'", line).group(1)

                # try-except is needed in case Rll_Ev_Ct value is messed up
                skip = False
                try:
                    value = int(value)
                except Exception:
                    skip = True
                    drive_results.append("Reallocated event count*: " + value)

                if skip is False:
                    if value > 0:
                        alert = 1
                    drive_results.append("Reallocated event count*: " + str(int(value)))
            elif "Current_Pending_Sector" in line:
                value = re.search(" - (.+?)'", line).group(1)
                drive_results.append("Current pending sector*: " + str(int(value)))
                if int(value) > 0:
                    alert = 1
            elif "Offline_Uncorrectable" in line:
                value = re.search(" - (.+?)'", line).group(1)
                drive_results.append("Offline uncorrectable: " + str(int(value)))
                if int(value) > 0:
                    alert = 1
            elif "Media_Wearout_Indicator" in line:
                value = re.search(" - (.+?)'", line).group(1)
                drive_results.append("Media wearout indicator: " + str(int(value)))

        return (alert, drive_results)

def top_collect_fileinfo(top, dbexec, in_vol_id, callback):
    '''recursively descend the directory tree rooted at top,
       calling the callback function for each regular file'''

    # need clean up existing records in fileinfo table for this folder
    delete_sql = '''delete from fileinfo
        where folder like '{fold}%'  and vol_id = '{vid}'
    '''.format(fold=top[2:], vid=in_vol_id)    # need remove "D:" from start of string
    dbexec.noselect_plain(delete_sql)

    file_type = 'fold'
    statdata = os.stat(top)
    (top_fold, diritem) = os.path.split(top)
    insert_file_row(dbexec, diritem, statdata, file_type, top_fold, in_vol_id)

    return collect_fileinfo(top, DB_EXEC, in_vol_id, callback)


def insert_file_row(dbexec, diritem, statdata, file_type, top, in_vol_id):
    '''
        fname text,
        size integer,
        file_type text,
        mod_time integer,
        folder text,
        fullname text
        disk_id integer,
    '''
    insert_sql = '''insert or replace into fileinfo
        (fname, size, file_type, mod_time, folder, fullname, vol_id)
        values('{fn}', {sz},'{ft}',{mtime},'{fold}','{fullname}',{did})
    '''.format(fn=diritem,sz=statdata[stat.ST_SIZE],
            ft=file_type,mtime=statdata[stat.ST_MTIME],fold=top[2:],
            fullname=os.path.join(top[2:], diritem),did=in_vol_id)
    dbexec.noselect_plain(insert_sql)



def collect_fileinfo(top, dbexec, in_vol_id, callback):
    '''recursively descend the directory tree rooted at top,
       calling the callback function for each regular file'''

    print("\nCheck folder " + top)

    for diritem in os.listdir(top):
        pathname = os.path.join(top, diritem)
        statdata = os.stat(pathname)
        mode = statdata.st_mode
        if stat.S_ISDIR(mode):
            file_type = 'fold'
            insert_file_row(dbexec, diritem, statdata, file_type, top, in_vol_id)

            # It's a directory, recurse into it
            collect_fileinfo(pathname, dbexec, in_vol_id, callback)

        elif stat.S_ISREG(mode):
            # It's a file, call the callback function
            callback(pathname)
            dotpos = pathname.rfind('.')
            file_type = ''
            if dotpos > -1:
                file_type = pathname[dotpos+1:].upper()

            insert_file_row(dbexec, diritem, statdata, file_type, top, in_vol_id)
        else:
            # Unknown file type, print a message
            print('Skipping %s' % pathname)


def visitfile(file):
    #print('visiting ', file)
    print('.', end="")




def find_duplicates(in_db):
    select_sql = "select fname, folder, vol_id, size from fileinfo order by fname asc, size asc, folder asc"
    all_files_list = in_db.select_plain(select_sql)
    file_count =len(all_files_list)
    pos1 = 0
    pos2 = 1
    while ( pos2 < file_count):
        if all_files_list[pos1][0] == all_files_list[pos2][0] and all_files_list[pos1][3] == all_files_list[pos2][3]:
            print(all_files_list[pos1])
            print(all_files_list[pos2])

            '''
            create table duplication
            (
                fname text,
                size integer,
                folder1 text,
                disk1 integer,
                folder2 text,
                disk2 integer,

            '''
            insert_sql = '''insert or ignore into duplication(fname, size, folder1, vol1, folder2, vol2)
                values('{fn}', {sz}, '{fd1}', {d1}, '{fd2}', {d2})
            '''.format(fn=all_files_list[pos1][0], sz=all_files_list[pos1][3],
                       fd1=all_files_list[pos1][1], d1=all_files_list[pos1][2],
                       fd2=all_files_list[pos2][1], d2=all_files_list[pos2][2])

            in_db.noselect_plain(insert_sql)

        pos1 += 1
        pos2 += 1
    
    print("\nFinish all rows")

def find_all_root_folders(in_db):
    select_sql = '''
        select fullname, vol_id from fileinfo f1 
        where folder not in 
        (select fullname from fileinfo  f2 where f2.vol_id = f1.vol_id)
    '''
    return in_db.select_plain(select_sql)

def find_all_disks(in_db):
    select_sql = '''
        select * from diskinfo'''
    return in_db.select_plain(select_sql)


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Collect file information.')
    argparser.add_argument("--root", dest='folder_root', metavar='Folder-root',
                           type=str, default=None,
                           help='root of the folder to scan')

    args = argparser.parse_args()

    # print(args.accumulate(args.folder_root))
    print(args.folder_root)

    DB_FILE = "..\\data\\diskmgr.db"

    # create a database connection
    DB_EXEC = DatabaseExecutor(DB_FILE)

    with DB_EXEC:
        systeminfo = SystemInformation(DB_EXEC)

        if args.folder_root:
            root_abspath = os.path.abspath(args.folder_root)
            print(root_abspath)
            disk_id = systeminfo.save_volumeinfo(root_abspath[:2].upper())
            top_collect_fileinfo(root_abspath, DB_EXEC, disk_id, visitfile)

            find_duplicates(DB_EXEC)

        disk_table = find_all_disks(DB_EXEC)
        for row in disk_table:
            print(row)

        root_table = find_all_root_folders(DB_EXEC)
        for row in root_table:
            print(row)

        

    # argparser.add_argument('folder_root', metavar='Folder-root', type=str, nargs="+",
    '''
    argparser.add_argument('--sum', dest='accumulate', action='store_const',
                    const=int, default=len,
                    help='sum the integers (default: find the max)')
    '''
    '''
    print(shutil.disk_usage("/").free)
    print(shutil.disk_usage("/").total)
    print(shutil.disk_usage("U:\\").used)

    '''
