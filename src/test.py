import wmi
c = wmi.WMI()


print(chr(ord('a') + 1))
print( 'hd' + 'a')
exit()


for hd in c.Win32_LogicalDisk():
    print(hd)

for hd in c.Win32_DiskDrive():
    print(hd)
    for part in hd.associators("Win32_DiskDriveToDiskPartition"):
        for disk in part.associators("Win32_LogicalDiskToPartition"):
            print(disk)
            pass

