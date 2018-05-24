from django.contrib import admin

# Register your models here.

from .models import Question

admin.site.register(Question)


from .models import Disk, Volume, FileInfo
admin.site.register(Disk)
admin.site.register(Volume)
admin.site.register(FileInfo)

