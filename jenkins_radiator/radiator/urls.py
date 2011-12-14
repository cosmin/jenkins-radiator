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
    # (r'^jenkins_radiator/', include('jenkins_radiator.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^info/(.*)/(.*)/$', 'jenkins_radiator.radiator.views.get_build_info'),
    (r'^test/(.*)/$', 'jenkins_radiator.radiator.views.get_test_report'),
    (r'^project/(.*)/$', 'jenkins_radiator.radiator.views.get_project_report'),
    (r'^data/(.*)/$', 'jenkins_radiator.radiator.views.get_builds'),
    (r'^stats/(.*)/$', 'jenkins_radiator.radiator.views.get_stats'),
    (r'^state/(.*)/$', 'jenkins_radiator.radiator.views.get_state'),
    (r'^(.*)/$', 'jenkins_radiator.radiator.views.get_radiator'),
)

