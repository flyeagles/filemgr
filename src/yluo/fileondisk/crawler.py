import os, sys
import stat
import re

import subprocess
import datetime

from django.db import connection

import wmi
import pythoncom


from . import models
from . import systeminfo
from . import fodconfigs

def printt(text, end="\n"):
    print(str(datetime.datetime.now()) + ': ' + text, end)



class SystemInformation(systeminfo.RawSystemInformation):
    def __init__(self):
        super().__init__()

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
                            
            disk_instance = models.Disk(serial_no=disk.SerialNumber,
                                        disk_model=disk.Model, disk_index=int(disk.Index),
                                        size=int(disk.Size),
                                        partitions=disk.Partitions,
                                        SMART_pass=1 - alert,
                                        SMART_info=',\n'.join(smart_info),
                                        machine=disk.SystemName, media_type=disk.MediaType)
            disk_instance.save()

            
            for volume in self.disk_to_vol[disk.Index]:
                print(volume)
                if volume.Caption == drive:

                    print(volume.Caption + "=>" + volume.VolumeSerialNumber)
                    print(volume)

                    intval = int(volume.VolumeSerialNumber, 16)

                    volume_instance = models.Volume(id=intval,
                                                   volume_name=volume.VolumeName,
                                                   size=int(volume.Size),
                                                   size_free=int(volume.FreeSpace),
                                                   disk=disk_instance)
                    volume_instance.save()

                    return volume_instance

        raise DiskError("Cannot find drive " + drive)


    def query_drive_state(self, drive_id):
        p = subprocess.Popen(["smartctl", "-a", "/dev/" + drive_id], 
                            stdout=subprocess.PIPE)
        (output, err) = p.communicate()

        print("Raw SMART data")
        print(output)
        print("==========End of Raw SMART data")
        drive_results = []
        alert = 0

        for line in output.splitlines():
            line = line.decode('utf-8')
            print(line)
            # 'Device Model:     SAMSUNG MZMTD256HAGM-000L1'
            if "Device Model" in line:
                value = re.search(r":\s+(\S.+?)$", line).group(1)
                drive_results.append("Device Model: " + str(value))
            elif "Model Family" in line:
                value = re.search(r":\s+(\S.+?)$", line).group(1)
                drive_results.append("Model Family: " + str(value))
            elif "Rotation Rate" in line:
                value = re.search(r":\s+(\S.+?)", line).group(1)
                drive_results.append("Rotation Rate: " + str(value))
            elif "Form Factor" in line:
                value = re.search(r":\s+(\S.+?)", line).group(1)
                drive_results.append("Form Factor: " + str(value))
            elif "Reallocated_Sector_Ct" in line:
                value = re.search(r" -\s+(\d+)", line).group(1)
                drive_results.append("Reallocated sector count: " + str(int(value)))
                if int(value) > 0:
                    alert = 1
            elif "Power_On_Hours" in line:
                print(line)
                value = re.search(r" -\s+(\d+)", line).group(1)
                #value = re.search(r" -\s+(\d\d\d)", line).group(1)
                print(value)
                drive_results.append("Power_On_Hours: " + str(int(value)))
            elif "Power_Cycle_Count" in line:
                value = re.search(r" -\s+(\d+)", line).group(1)
                drive_results.append("Power_Cycle_Count: " + str(int(value)))
            elif "Airflow_Temperature_Cel" in line:
                value = re.search(r" -\s+(\d+)", line).group(1)
                drive_results.append("Airflow_Temperature_Cel: " + str(value))  # eg. 34 (Min/Max 30/43)
            elif "Wear_Leveling_Count" in line:
                value = re.search(r" - (.+?)", line).group(1)
                drive_results.append("Wear leveling count: " + str(int(value)))
            elif "Reallocated_Event_Count" in line:
                value = re.search(r" - (.+?)", line).group(1)
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
                value = re.search(" -\s+(\d+)", line).group(1)
                drive_results.append("Current pending sector*: " + str(int(value)))
                if int(value) > 0:
                    alert = 1
            elif "Offline_Uncorrectable" in line:
                value = re.search(" -\s+(\d+)", line).group(1)
                drive_results.append("Offline uncorrectable: " + str(int(value)))
                if int(value) > 0:
                    alert = 1
            elif "Media_Wearout_Indicator" in line:
                value = re.search(" -\s+(\d+)", line).group(1)
                drive_results.append("Media wearout indicator: " + str(int(value)))

        return (alert, drive_results)

class FileCrawler():
    '''
        class to crawl specific folder and store file and folder information in database.
    '''
    def __init__(self):
        with connection.cursor() as cur:
            cur.execute("PRAGMA cache_size = -40960")  # cache of 40MB
            cur.execute("PRAGMA journal_mode = MEMORY")
        # self.cursor = connection.cursor()
        
        self.file_info_list = []
        self.list_len = 0
        self.folder_cnt = 0
        self.file_info_cnt = 0

    def top_collect_fileinfo(self, top, in_volume, callback):
        '''recursively descend the directory tree rooted at top,
        calling the callback function for each regular file'''

        # need clean up existing records in fileinfo table for this folder
        '''
        delete_sql = '' 'delete from fileinfo
            where folder like '{fold}%'  and vol_id = '{vid}'
        '' '.format(fold=top[2:], vid=in_vol_id)    # need remove "D:" from start of string
        dbexec.noselect_plain(delete_sql)
        '''

        # now folder starts with volume ID. Need add that to the filter
        printt("========== Start crawling "+top)
        fullfolder = "\\".join([str(in_volume.id), top[2:]]).replace("\\\\", "\\")
        print(fullfolder)
        cnt = models.FileInfo.objects.all().filter(folder__startswith=fullfolder).delete()
        cnt2 = models.FileInfo.objects.all().filter(fullvolpath__exact=fullfolder).delete()
        print("Deleted " + str(cnt+cnt2) + " records under the target folder.")

        # remove existing roots that are the subtree of current folder.
        delcnt = models.CrawlRoot.objects.filter(folder__contains=fullfolder).delete()
        print("Delete {cnt} records from crawlroot that is child of crawl folder {f}".format(cnt=delcnt, f=fullfolder))

        # check if current folder is subtree of existing root
        existing_root_list = list(models.CrawlRoot.objects.filter(volume_id__exact=in_volume.id).values_list('fullvolpath',flat=True))
        need_insert_root = True
        for existing_root in existing_root_list:
            if existing_root in fullfolder:  
                # this crawl root is already covered by existing root. Should not insert at all.
                # this is true when existing_root == fullfolder
                need_insert_root = False
                break

        (top_fold, diritem) = os.path.split(top)

        if need_insert_root:
            print("insert this folder to crawlroot: {fd}".format(fd=fullfolder))
            with connection.cursor() as cur:
                cur.executemany('''INSERT INTO fileondisk_crawlroot
                (fname, folder, fullvolpath, volume_id)
                values(?,?,?,?)''', [(diritem, "\\".join([str(in_volume.id), top_fold[2:]]).replace("\\\\", "\\"), fullfolder,
                    in_volume.id, )])


        file_type = 'fold'
        statdata = os.stat(top)
        self.insert_file_row(diritem, statdata, file_type, top_fold, in_volume)

        self.collect_fileinfo(top, in_volume, callback)
        self.flush_rows()
        return self.file_info_cnt


    def insert_file_row(self, diritem, statdata, file_type, top, in_volume):
        '''
            fname text,
            size integer,
            file_type text,
            mod_time integer,
            folder text,
            fullname text
            disk_id integer,
        '' '
        insert_sql = ' ''insert or replace into fileinfo
            (fname, size, file_type, mod_time, folder, fullname, vol_id)
            values('{fn}', {sz},'{ft}',{mtime},'{fold}','{fullname}',{did})
        '' '.format(fn=,sz=,
                ft=,mtime=,fold=,
                fullname=,did=in_vol_id)
        dbexec.noselect_plain(insert_sql)

        fileinfo = models.FileInfo(fname=diritem, size=statdata[stat.ST_SIZE], file_type=file_type,
                                mod_time=statdata[stat.ST_MTIME], 
                                folder=str(in_volume.id) + top[2:],
                                fullname=os.path.join(top[2:], diritem),
                                fullvolpath=str(in_volume.id) + os.path.join(top[2:], diritem),
                                volume=in_volume)
        fileinfo.save()
        '''
        self.file_info_cnt += 1
        self.file_info_list.append((diritem, statdata[stat.ST_SIZE], file_type,
                                statdata[stat.ST_MTIME], 
                                str(in_volume.id) + top[2:],
                                # fullname = os.path.join(top[2:], diritem),
                                str(in_volume.id) + os.path.join(top[2:], diritem),
                                in_volume.id,))
        self.list_len += 1
        if self.list_len >= 3000:
            self.flush_rows()

    def flush_rows(self):
        with connection.cursor() as cur:
            cur.executemany('''INSERT INTO fileondisk_fileinfo
            (fname, size, file_type, mod_time, folder, fullvolpath, volume_id)
            values(?,?,?,?,?,?,?)''', self.file_info_list)
        self.file_info_list = []
        printt("Finish flushing {row} rows.".format(row=self.list_len))
        self.list_len = 0
        

    def collect_fileinfo(self, top, in_volume, callback):
        '''recursively descend the directory tree rooted at top,
        calling the callback function for each regular file'''

        self.folder_cnt += 1
        if self.folder_cnt % 100 == 0:
            printt("\nProcessed " + str(self.file_info_cnt) + " records. Check " + top + ": ", end="")

        try:
            for diritem in os.listdir(top):
                pathname = os.path.join(top, diritem)
                
                try:
                    statdata = os.stat(pathname)
                except FileNotFoundError as file_err:
                    print(file_err)
                    print("Skip file " + pathname)
                    continue

                mode = statdata.st_mode
                if stat.S_ISDIR(mode):
                    file_type = 'fold'
                    self.insert_file_row(diritem, statdata, file_type, top, in_volume)

                    # It's a directory, recurse into it
                    self.collect_fileinfo(pathname, in_volume, callback)
                elif stat.S_ISREG(mode):
                    # It's a file, call the callback function
                    callback(pathname)
                    dotpos = pathname.rfind('.')
                    file_type = ''
                    if dotpos > -1:
                        file_type = pathname[dotpos+1:].upper()

                    self.insert_file_row(diritem, statdata, file_type, top, in_volume)
                else:
                    # Unknown file type, print a message
                    print('Skipping %s' % pathname)
        except PermissionError as permit_err:
            print('Skipping {dir} due to permission error:'.format(dir=top))
            print(permit_err)


def visitfile(file):
    #print('visiting ', file)
    # print('.', end="")
    pass



def crawl_folder(folder_root):
    start_time = datetime.datetime.now()

    print(os.getcwd())

    originalfile = fodconfigs.get_original_folder()

    systeminfo = SystemInformation()

    root_abspath = os.path.abspath(folder_root)
    print(root_abspath)
    volume = systeminfo.save_volumeinfo(root_abspath[:2].upper())
    filecrawler = FileCrawler()
    file_count = filecrawler.top_collect_fileinfo(root_abspath, volume, visitfile)
    printt("========== Finish crawling "+ root_abspath)
    print("Total time spent is " + str( datetime.datetime.now() - start_time))
    print("Processed {cnt} file records.".format(cnt=file_count))
    
    if originalfile:
        print("Copy RAM db back to original db file " + originalfile)
        os.system("copy db.sqlite3 " + originalfile)