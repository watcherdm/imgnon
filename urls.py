from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    (r'^contrast/$', 'imgnon.contrast.views.index'),
    (r'^contrast/(?P<contrast_id>\d+).*$', 'imgnon.contrast.views.detail'),
    (r'^contrast/adjust', 'imgnon.contrast.views.adjust'),
    (r'^contrast/evaluate', 'imgnon.contrast.views.evaluate'),
    (r'^contrast/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/gabriel/imgnon/imgnon'}),
    # Example:
    # (r'^imgnon/', include('imgnon.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
