create table  if not exists fileondisk_disk
(
    serial_no text,
    model text,
    disk_index integer,   -- index: used to locate SMART record. Add it to "hda" to get device
    size integer,
    partitions integer,
    SMART_pass integer,
    SMART_info text,
    machine text,
    media_type text,
    is_raid1 integer, -- value 1 means this disk is RAID1, thus offer replication automatically. value 0 means no duplication.
    primary key (serial_no)
) ;

create table if not exists fileondisk_volume
(
    id integer, -- value of volume serial number
    volume_name text,
    size integer,
    size_free integer,
    disk_no text,
    primary key(id),
    foreign key (disk_no) references diskinfo(serial_no) 
);

create table if not exists fileinfo
(
    fname text,
    size integer,
    file_type text,
    mod_time integer,
    folder text,
    fullname text,
    vol_id integer,
    primary key(fname, folder, vol_id),
    foreign key (vol_id) references volumeinfo(id)
);

create table if not exists duplication
(
    fname text,
    size integer,
    folder1 text,
    vol1 integer,
    folder2 text,
    vol2 integer,
    primary key(fname, folder1, vol1, folder2, vol2),
    foreign key (fname, folder1, vol1) references fileinfo(fname, folder, vol_id) on delete cascade,
    foreign key (fname, folder2, vol2) references fileinfo(fname, folder, vol_id) on delete cascade ,
    check(folder1 < folder2)
) ;


pragma foreign_keys = on;  -- turn on foreign key constraint

select fname, vol_id from fileinfo f1 where folder not in
 (select fullname from fileinfo  f2 where f2.vol_id = f1.vol_id)


.headers on 
.tables
