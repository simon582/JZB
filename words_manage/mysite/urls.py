#-*- coding:utf-8 -*-
from django.conf.urls import patterns, include, url
from mysite import views
from views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login/$',views.login),
    url(r'^auth/$',views.auth_view),
    url(r'^invalid/$',views.invalid_login),
    url(r'^logout/',views.logout),
    url(r'^words_manage/$',views.words_manage),
    url(r'^download_temp/$',views.download_temp),
    url(r'^download_vertical/$',views.download_vertical),
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
