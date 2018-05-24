from django.db import models

from django.utils import timezone
import datetime

# Create your models here.


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text

class Disk(models.Model):
    '''
        serial_no text,
        disk_model text,
        disk_index integer,   -- index: used to locate SMART record. Add it to "hda" to get device
        size integer,
        partitions integer,
        SMART_pass integer,
        SMART_info text,
        machine text,
        media_type text,
        is_raid1 integer, -- 1 means RAID1, 0 means no-raid.
        primary key (serial_no)
    '''
    serial_no = models.TextField(primary_key=True)
    disk_model = models.TextField()
    disk_index = models.IntegerField()
    size = models.IntegerField()
    partitions = models.IntegerField()
    SMART_pass = models.IntegerField()
    SMART_info = models.TextField()
    machine = models.TextField()
    media_type = models.TextField()
    is_raid1 = models.IntegerField(default=0)

    def __str__(self):
        return self.disk_model

class Volume(models.Model):
    '''
        id integer, -- value of volume serial number
        volume_name text,
        size integer,
        size_free integer,
        disk_no text,
        primary key(id),
        foreign key (disk_no) references diskinfo(serial_no) 
    '''
    id = models.IntegerField(primary_key=True)
    volume_name = models.TextField()
    size = models.IntegerField()
    size_free = models.IntegerField()

    disk = models.ForeignKey('Disk', on_delete=models.PROTECT)


class CrawlRoot(models.Model):
    '''
        fname text,
        folder text,
        fullvolpath text,
        volume_id integer,
        foreign key (volume_id) references volumeinfo(id)
    '''
    fname = models.TextField()
    folder = models.TextField()    # should include volumeID
    fullvolpath = models.TextField()   # use default int ID, that proably is faster.

    volume = models.ForeignKey('Volume', on_delete=models.PROTECT)


class FileInfo(models.Model):
    '''
        fname text,
        size integer,
        file_type text,
        mod_time integer,
        folder text,
        fullname text,
        fullvolpath text,
        vol_id integer,
        primary key(fname, folder, vol_id),
        foreign key (vol_id) references volumeinfo(id)
    '''
    fname = models.TextField()
    size = models.IntegerField()
    file_type = models.TextField()
    mod_time = models.IntegerField()
    folder = models.TextField()    # should include volumeID
    # fullname = models.TextField()  
    fullvolpath = models.TextField()   # use default int ID, that proably is faster.
    
    volume = models.ForeignKey('Volume', on_delete=models.PROTECT)
