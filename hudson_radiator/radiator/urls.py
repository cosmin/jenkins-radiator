from django.conf.urls.defaults import *
from django.conf import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
urlpatterns = patterns('')

if settings.DEBUG:
  urlpatterns += patterns('',
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.SITE_MEDIA})
 )

urlpatterns += patterns('',
    # Example:
    # (r'^hudson_radiator/', include('hudson_radiator.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^info/(.*)/(.*)/$', 'hudson_radiator.radiator.views.get_build_info'),
    (r'^data/(.*)/$', 'hudson_radiator.radiator.views.get_builds'),
    (r'^(.*)/$', 'hudson_radiator.radiator.views.get_radiator')
)

