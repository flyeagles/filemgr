from rest_framework import serializers
from .models import Disk, Volume, FileInfo, CrawlRoot


class DiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disk
        fields = ('serial_no', 'disk_model', 'disk_index', 'size', 'partitions', 'SMART_pass',
                  'SMART_info', 'machine', 'media_type')


class VolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Volume
        fields = ('id', 'volume_name', 'size', 'size_free')

class FileInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileInfo
        fields = ('fullvolpath', 'fname', 'size', 'file_type',
                  'mod_time', 'folder', 'volume_id')


class CrawlRootSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlRoot
        fields = ('fullvolpath', 'fname', 'folder', 'volume_id')
