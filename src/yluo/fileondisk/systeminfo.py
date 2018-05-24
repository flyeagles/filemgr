import wmi
import pythoncom


class DiskError(BaseException):
    def __init__(self, msg):
        self.msg = msg

    def get_msg(self):
        return self.msg


class HardDiskInformation:
    def __init__(self):
        pythoncom.CoInitialize()
        self.wmi_conn = wmi.WMI()

        # we need query the system to get all the disks and volumes of the system
        self.disk_to_vol = dict()
        self.hard_disks = self.wmi_conn.Win32_DiskDrive()
    
    def get_hd_serial_no_list(self):
        return [hd.SerialNumber for hd in self.hard_disks]


class RawSystemInformation:
    def __init__(self):
        pythoncom.CoInitialize()
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

    def get_drive(self, volume_id):
        for disk in self.hard_disks:
            for volume in self.disk_to_vol[disk.Index]:
                if int(volume.VolumeSerialNumber, 16) == volume_id:
                    return volume.Caption
        
        return None
        

    def get_volume_id(self, drive):
        for disk in self.hard_disks:
            for volume in self.disk_to_vol[disk.Index]:
                if volume.Caption == drive:
                    return int(volume.VolumeSerialNumber, 16)
       
        return None
