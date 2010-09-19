from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^contrast/$', 'imgnon.contrast.views.index'),
    (r'^contrast/control','imgnon.contrast.views.control'),
    (r'^contrast/adjust', 'imgnon.contrast.views.adjust'),
    (r'^contrast/evaluate', 'imgnon.contrast.views.evaluate'),
    (r'^contrast/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/gabriel/imgnon/imgnon'})
)
