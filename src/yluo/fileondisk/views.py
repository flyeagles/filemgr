from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from fileondisk.models import Question, Choice
#from django.template import loader
from django.http import Http404

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone


from django.http import Http404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status, mixins, generics
from rest_framework.views import APIView

import urllib

import ctypes
import os
import subprocess
import winshell

# Local objects
from .models import Disk, Volume, FileInfo, CrawlRoot
from .serializers import DiskSerializer, VolumeSerializer, FileInfoSerializer, CrawlRootSerializer
from .crawler import crawl_folder, crawl_as_raid1, collect_folder_tree, FileObject
from .systeminfo import  HardDiskInformation, RawSystemInformation




class DiskList(mixins.ListModelMixin, generics.GenericAPIView):
    '''
    List all disks
    '''
    queryset = Disk.objects.all()
    serializer_class = DiskSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class PresentDiskList(mixins.ListModelMixin, generics.GenericAPIView):
    '''
    List all disks
    '''
    hd_list = HardDiskInformation()
    queryset = Disk.objects.filter(serial_no__in=hd_list.get_hd_serial_no_list())
    serializer_class = DiskSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class DiskDetail(mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin,
                 generics.GenericAPIView):
    """
    Retrieve, update or delete a code snippet.
    """
    queryset = Disk.objects.all()
    serializer_class = DiskSerializer
    
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class DiskVolume(APIView):
    """
    List all volumes under a disk
    """
    
    def get(self, request, serial_no):
        disk = Disk.objects.get(pk=serial_no)
        volumes = disk.volume_set.all()
        volserializer = VolumeSerializer(volumes, many=True)
        return Response(volserializer.data)



class FolderCrawler(APIView):
    def post(self, request):
        crawl_folder(request.POST['crawl_folder'])
        return HttpResponseRedirect(reverse('fileondisk:index'), {'latest_question_list': Question.objects.all()})


class Raid1Crawler(APIView):

    def post(self, request):
        crawl_as_raid1(request.POST['raid_folder'])
        return HttpResponseRedirect(reverse('fileondisk:index'), {'latest_question_list': Question.objects.all()})




class VolumeRoot(APIView):
    '''
    List all root folders under a volume
    '''
    def get(self, request, vol_id):
        '''
            select * from fileondisk_fileinfo f1
            where volume_id = '1190491944' and folder not in
            (select fullvolpath from fileondisk_fileinfo  f2 where 
            f2.volume_id = '1190491944');
        '''
        ''' If the volume is crawled from root "\", we must use following SQL to get root.
         select * from fileondisk_fileinfo where folder = fullvolpath;
        '''

        '''
        # first try to get true root folder
        roots = Volume.objects.get(pk=vol_id).fileinfo_set.extra(where=["folder = fullvolpath"])
        if len(list(roots)) == 0: 
            # no true root folder. Need get individuals.

            files = Volume.objects.get(pk=vol_id).fileinfo_set.all()
            filelist2 = Volume.objects.get(pk=vol_id).fileinfo_set.all()
            #fullvolpaths = list(filelist2.values_list('fullvolpath', flat=True))
            #print(len(fullvolpaths))   # could be huge number, like 40000
            roots = files.exclude(folder__in=filelist2.values_list('fullvolpath', flat=True))
            print(len(list(roots)))
        '''
        roots = CrawlRoot.objects.filter(volume_id__exact=vol_id)
        fileinfoserializer = CrawlRootSerializer(roots, many=True)
        return Response(fileinfoserializer.data)
        #    FileInfo.objects.filter(your_condition).values_list('id', flat=True))
        
        #files.extra(where=["folder NOT IN (SELECT f2.fullname FROM FileInfo f2 WHERE f2.vol_id = some_parm)"])

    def delete(self, request, fullvolpath):
        fullvolpath = str(fullvolpath).replace('\\\\', '\\').replace('/', '\\') 
        CrawlRoot.objects.filter(fullvolpath__exact=fullvolpath).delete()
        FileInfo.objects.filter(folder__contains=fullvolpath).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class Folder(APIView):
    '''
    List all fileinfo items under a folder
    '''
    def get(self, requst, fullvolpath):
        # fullvolpath is url-escaped. Need turn it back to original form.
        fullvolpath = urllib.parse.unquote(fullvolpath)
        instr = str(fullvolpath).replace('\\\\', '\\').replace('/', '\\')  # have to remove extra '\'
        files = FileInfo.objects.filter(folder__exact=instr).extra(where=["folder <> fullvolpath"]) #str(fullvolpath))
        fileinfoserializer = FileInfoSerializer(files, many=True)
        return Response(fileinfoserializer.data)
        

class FileDuplicates(APIView):
    '''
    List all fileinfo with identical fname and size.
    '''
    def get(self, request, fullvolpath):
        fullvolpath = urllib.parse.unquote(fullvolpath)
        instr = str(fullvolpath).replace('\\\\', '\\').replace('/', '\\')  # have to remove extra '\'
        files = list(FileInfo.objects.filter(fullvolpath__exact=instr))
        '''
        select * from fileinfo where 
        '''
        dupfiles = FileInfo.objects.filter(size__exact=files[0].size, fname__exact=files[0].fname)
        fileinfoserializer = FileInfoSerializer(dupfiles, many=True)
        return Response(fileinfoserializer.data)



class FileSearchResult(APIView):
    '''
    List all fileinfo containing the search text
    '''
    def get(self, request, searchtext):
        '''
        select * from fileinfo where 
        '''
        print("Get search:" + searchtext)
        searchtext.replace(':', '').replace(",", "")
        # need handle wildcard.
        terms = searchtext.split('*')
        qs = FileInfo.objects
        for term in terms:
            if term != '':
                short_terms = term.split(' ')
                for short_term in short_terms:
                    if short_term != '':
                        qs = qs.filter(fname__contains=short_term.strip())
        searchmatches = qs
        fileinfoserializer = FileInfoSerializer(searchmatches, many=True)
        return Response(fileinfoserializer.data)


def getFilesOnRAID1():
    '''
    Get all fileInfo objects that exist on RAID1 disk.
    '''
    diskset = Disk.objects.filter(is_raid1=1)
    volumeset = Volume.objects.filter(disk__in=diskset)
    fileset = FileInfo.objects.filter(volume__in=volumeset)

    return fileset


def isRAID1Drive(target_folder):
    drive = target_folder[0:2]
    rawsysinfo = RawSystemInformation()
    vol_id = rawsysinfo.get_volume_id(drive)

    diskset = Disk.objects.filter(volume__id__exact=vol_id)
    for disk in list(diskset):
        if disk.is_raid1 == 1:
            return True
    
    return False

def getMatchedFileInfos(target_folder):
    if isRAID1Drive(target_folder):
        return ( FileInfo.objects.none(), [] )

    raid1_files_set = getFilesOnRAID1()
    # we need crawl the target folder and get all the files in the folder tree.
    all_file_objects_in_target_folder = []
    collect_folder_tree(target_folder, all_file_objects_in_target_folder)


    # now we need filter the RAID1 file set with those files in the all_file_objects_in_target_folder
    query_fields = ({ 'fname': fobj.fname, 'size': fobj.fsize} for fobj in all_file_objects_in_target_folder)

    queryset = raid1_files_set.none()
    for query_kwarg in query_fields:
        queryset |= raid1_files_set.filter(**query_kwarg)

    searchmatches = queryset.distinct()

    found_files = list(searchmatches)
    found_file_set = { FileObject(found_file.fname, found_file.size, "") for found_file in found_files }

    dup_files_in_target = []
    for fileobj in all_file_objects_in_target_folder:
        if fileobj in found_file_set:
            dup_files_in_target.append(fileobj)

    print("============ {cnt} Files to be deleted!!!! =================".format(cnt=len(dup_files_in_target)))
    for fileobj in dup_files_in_target:
        print(str(fileobj))
    print("=============================================")
    
    return (searchmatches, dup_files_in_target)

class FindRAID1Duplicates(APIView):
    '''
    Collect files in target folder, and list those duplilcated with existing items in RAID1 disks
    '''
    def get(self, request, target_folder):
        '''
        select * from fileinfo where 
        '''
        print("Get findRaid1Duplicates:" + target_folder)

        (searchmatches, dup_files_in_target) = getMatchedFileInfos(target_folder)

        fileinfoserializer = FileInfoSerializer(searchmatches, many=True)
        return Response(fileinfoserializer.data)


class DeleteRAID1Duplicates(APIView):
    '''
    Collect files in target folder, and list those duplilcated with existing items in RAID1 disks
    '''
    def get(self, request, target_folder):
        '''
        select * from fileinfo where 
        '''
        print("Get DeleteRAID1Duplicates:" + target_folder)

        (searchmatches, dup_files_in_target) = getMatchedFileInfos(target_folder)

        for fileobj in dup_files_in_target:
            filepath = os.path.abspath(fileobj.folder + '/' + fileobj.fname)
            winshell.delete_file(filepath)
            
        print("********  {cnt} Files are deleted!!!!!! =============".format(cnt=len(dup_files_in_target)))

        fileinfoserializer = FileInfoSerializer(searchmatches, many=True)
        return Response(fileinfoserializer.data)



import win32gui

def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))

class OpenExplorer(APIView):
    '''
    Open windows explorer based on the file location
    '''

    rawsysinfo = RawSystemInformation()

    def get(self, request, selection):
        print(selection)
        pos = selection.find('/')
        if pos == -1:
            pos = selection.find('\\')

        volume_id = selection[:pos]
        path = selection[pos:]

        path = str(path).replace('\\\\', '\\').replace('/', '\\')
        drive = self.rawsysinfo.get_drive(int(volume_id))
        if drive is None:
            # the volume is not present in current computer. Return immediately
            return Response(status=status.HTTP_204_NO_CONTENT)


        fullpath = os.path.join(drive, path)
        print(fullpath)

        subprocess.Popen(r'explorer /select,"{p}"'.format(p=fullpath))

        '''This code will crash when used on Windows 10
        ctypes.windll.ole32.CoInitialize(None)

        #fullpath = fullpath.encode('utf-16')
        pidl = ctypes.windll.shell32.ILCreateFromPathW(fullpath)
        ctypes.windll.shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
        ctypes.windll.shell32.ILFree(pidl)
        ctypes.windll.ole32.CoUninitialize()
        '''
        
        return Response(status=status.HTTP_204_NO_CONTENT)








class IndexView(generic.ListView):
    template_name = 'fileondisk/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]




def detail(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'fileondisk/detail.html', {'question': question})


def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'fileondisk/results.html', {'question': question})


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'fileondisk/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('fileondisk:results', args=(question.id,)))
