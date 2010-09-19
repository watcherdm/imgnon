from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^/$', 'imgnon.contrast.views.index'),
    (r'^contrast/$', 'imgnon.contrast.views.index'),
    (r'^contrast/adjust', 'imgnon.contrast.views.adjust'),
    (r'^contrast/evaluate', 'imgnon.contrast.views.evaluate'),
    (r'^contrast/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/gabriel/imgnon/imgnon'})
)
