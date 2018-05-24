from django.urls import path
from . import views
from django.contrib import admin
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'fileondisk'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),

    # ex: /fileondisk/5/
    path('<int:question_id>/', views.detail, name='detail'),
    
    # ex: /fileondisk/5/results/
    path('<int:question_id>/results/', views.results, name='results'),
    
    # ex: /fileondisk/5/vote/
    path('<int:question_id>/vote/', views.vote, name='vote'),

    url(r'^disks/$', views.DiskList.as_view()),
    url(r'^disks/(?P<pk>[^/]+)/$', views.DiskDetail.as_view()),
    url(r'^disks/(?P<serial_no>.+)/volumes/$', views.DiskVolume.as_view()),
    url(r'^volumes/(?P<vol_id>.+)/$', views.VolumeRoot.as_view()),
    
    url(r'^root/(?P<fullvolpath>.+)/$', views.VolumeRoot.as_view()),

    url(r'^folders/(?P<fullvolpath>.+)/$', views.Folder.as_view()),
    url(r'^file/(?P<fullvolpath>.+)/$', views.FileDuplicates.as_view()),
    url(r'^search/(?P<searchtext>.+)/$', views.FileSearchResult.as_view()),
    url(r'^presentdisks/$', views.PresentDiskList.as_view()),

    url(r'^explore/(?P<selection>.+)/$', views.OpenExplorer.as_view()),

    path('crawl/', views.FolderCrawler.as_view(), name='crawl'),
]


urlpatterns = format_suffix_patterns(urlpatterns)