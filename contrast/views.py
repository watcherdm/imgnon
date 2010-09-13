from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from imgnon.contrast.models import Image as img
import StringIO
from PIL import Image, ImageEnhance, ImageOps
from imgnon.contrast.sbm import stickybits
import simplejson as json
TEST_KEY = "c1e1928908a544dbc15b5e0231887a58"

def index(request):
  return render_to_response('adjust.html')

def detail(request, contrast_id):
  try:
    image = img.objects.get(pk=contrast_id)
  except Contrast.DoesNotExist:
    raise Http404
  return render_to_response('detail.html', {'image_index':image})

@csrf_exempt
def adjust(request):
  if request.method == 'POST':
    sb = stickybits.Stickybits(apikey=TEST_KEY)
    sb.base_url = 'http://dev.stickybits.com/api/2/'
    current = '/home/gabriel/imgnon/tmp/f.jpg'
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
      current = '/home/gabriel/imgnon/tmp/f%d.jpg' % (con * 100)
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
