from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from imgnon.contrast.models import Image as img
import StringIO
from PIL import Image, ImageEnhance, ImageOps, ImageStat
from imgnon.contrast.sbm import stickybits
from django.utils import simplejson as json
TEST_KEY = "c1e1928908a544dbc15b5e0231887a58"
import os.path
PROJECT_DIR = os.path.dirname(__file__)
TEMP_DIR = os.path.join(PROJECT_DIR, "imgtmp")
def index(request):
  return render_to_response('adjust.html')

def detail(request, contrast_id):
  try:
    image = img.objects.get(pk=contrast_id)
  except Contrast.DoesNotExist:
    raise Http404
  return render_to_response('detail.html', {'image_index':image})

def evaluate(request):
  if request.method == 'POST':
    sb = stickybits.Stickybits(apikey=TEST_KEY)
    sb.base_url = 'http://dev.stickybits.com/api/2/'
    current = TEMP_DIR + "/f.png"
    post = request.POST
    files = request.FILES
    image = request.FILES['img']
    dest = open(current, 'wb+')
    for chunk in image.chunks():
      print "Writing the image to disk"
      dest.write(chunk)
    dest.close()
    current = TEMP_DIR + "/f.png"
    imagen = Image.open(current)
    imagen = ImageOps.grayscale(imagen)
    sz = imagen.size
    while sz[0] > 2000 or sz[1] > 2000:
      imagen.resize([x/2 for x in list(sz)])
      sz = imagen.size
    imst = ImageStat.Stat(imagen)
    xt = imst.extrema
    con = (xt[0]/25500) * CONTRAST_CONSTANT if x[0] > 20 else None
    bri =  (xt[1]/25500) * BRIGHTNESS_CONSTANT if x[1] < 180 else None
    if bri:
      brienh = ImageEnhance.Brightness(imagen)
      imagen = brienh.enhance(float(bri))
    if con:
      conenh = ImageEnhance.Contrast(imagen)
      imagen = conenh.enhance(float(con))
    current = '%s/f%d.jpg' % (TEMP_DIR, con * 100)
    imagen.save(current, "JPEG")
    cont = upload_image(sb, current)
    result = json.dumps({'success': True, 'codes':cont['codes'],'contrast': con, 'brightness':bri}) if len(cont['codes']) else json.dumps({'success': False, 'codes':None,'contrast': con, 'brightness':bri})
    return HttpResponse(result)
  else:
    return HttpResponse({'success': False, 'message': 'Post an image to evaluate'})

def adjust(request):
  if request.method == 'POST':
    sb = stickybits.Stickybits(apikey=TEST_KEY)
    sb.base_url = 'http://dev.stickybits.com/api/2/'
    current = TEMP_DIR + "/f.png"
    post = request.POST
    files = request.FILES
    image = request.FILES['img']
    dest = open(current, 'wb+')
    for chunk in image.chunks():
      dest.write(chunk)
    dest.close()
    con = 1.0
    tries = 0
    cont = upload_image(sb, current)
    count = len(cont['codes'])
    while count == 0 and tries <= 5:
      con += 0.3
      imagen = Image.open(current)
      imagen = ImageOps.grayscale(imagen)
      bri = ImageEnhance.Brightness(imagen)
      imagen = bri.enhance(float(con) * 1.2)
      enh = ImageEnhance.Contrast(imagen)
      imagen = enh.enhance(float(con))
      current = '%s/f%d.jpg' % (TEMP_DIR, con * 100)
      imagen.save(current, "JPEG")
      cont = upload_image(sb, current)
      tries += 1
      count = len(cont['codes'])
    result = json.dumps({'success': True, 'codes':cont['codes'],'tries':tries}) if len(cont['codes']) else json.dumps({'success': False, 'codes':None,'tries':tries})
    return HttpResponse(result)
  else:
    result = json.dumps({'success':False, 'message': 'Post an image to this url to see if there is a valid UPC code lookup for it.'})
    return HttpResponse(result)

def upload_image(sb, code_image, **kwargs):
  data = {}
  headers = None
  data['code_image'] = code_image

  try:
    content_type, body = stickybits.file_encode(data['code_image'])
  except:
    return False

  headers = {
  'Content-Type': content_type
  }
  data = body

  return sb.request('scan.create', kwargs, "POST",
  data=data, headers=headers)
