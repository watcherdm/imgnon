from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
import StringIO
import hashlib
import datetime
from PIL import Image, ImageEnhance, ImageOps, ImageStat
from imgnon.contrast.sbm import stickybits
from django.utils import simplejson as json
TEST_KEY = "c1e1928908a544dbc15b5e0231887a58"
import os.path
PROJECT_DIR = os.path.dirname(__file__)
TEMP_DIR = os.path.join(PROJECT_DIR, "imgtmp")
IMAGE_RANDOM = 'holder'
def index(request):
  return render_to_response('adjust.html')

def evaluate(request):
  """ This will attempt a passive evaluation of the image
      reduce the size if it is larger than 2000 in any direction
      greyscale all images"""
  if request.method == 'POST':
    IMAGE_RANDOM = hashlib.sha224(datetime.datetime.now().isoformat()).hexdigest()[:8]
    sb = stickybits.Stickybits(apikey=TEST_KEY)
    sb.base_url = 'http://dev.stickybits.com/api/2/'
    current = "%s/%s.jpg" % (TEMP_DIR, IMAGE_RANDOM)
    post = request.POST
    image = request.FILES['img']
    imagen = Image.open(image)
    imagen = ImageOps.grayscale(imagen)
    sz = imagen.size
    while sz[0] > 2000 or sz[1] > 2000:
      imagen = imagen.resize([x/2 for x in list(sz)])
      sz = imagen.size
    imagen.save(current, "JPEG")
    cont = upload_image(sb, current)
    if len(cont["codes"]) > 0:
      result = json.dumps({'success': True, 'codes':cont['codes'],'method':'greyscale and scale only'})
      return HttpResponse(result)
    return adjust(request)
  else:
    return HttpResponse({'success': False, 'message': 'Post an image to evaluate'})

def adjust(request):
  if request.method == 'POST':
    IMAGE_RANDOM = hashlib.sha224(datetime.datetime.now().isoformat()).hexdigest()[:8]
    sb = stickybits.Stickybits(apikey=TEST_KEY)
    sb.base_url = 'http://dev.stickybits.com/api/2/'
    current = "%s/%s.jpg" % (TEMP_DIR, IMAGE_RANDOM)
    post = request.POST
    files = request.FILES
    image = request.FILES['img']
    imagen = Image.open(image)
    imagen = ImageOps.grayscale(imagen)
    sz = imagen.size
    while sz[0] > 2000 or sz[1] > 2000:
      imagen = imagen.resize([x/2 for x in list(sz)])
      sz = imagen.size
    imagen.save(current, "JPEG")
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
      current = '%s/%s%d.jpg' % (TEMP_DIR, IMAGE_RANDOM, con * 100)
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
