from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from imgnon.contrast.models import Image as img
import StringIO
from PIL import Image, ImageEnhance
# Create your views here.
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
    post = request.POST
    files = request.FILES
    image = request.FILES['img']
    con = request.POST['amt']
    imagen = Image.open(StringIO.StringIO(image.read()))
    bri = ImageEnhance.Brightness(imagen)
    imagen = bri.enhance(float(con))
    enh = ImageEnhance.Contrast(imagen)
    out = StringIO.StringIO()
    imagen = enh.enhance(float(con))
    imagen.save(out, "PNG")
    cont = out.getvalue()
    out.close()
    return HttpResponse(cont, mimetype='image/png')
  else:
    return Http404
def handle_uploaded_file(f):
  destination = open('/home/gabriel/tmp/imgnon/contrast.png', 'wb+')
  for chunk in f.chunks():
    destination.write(chunk)
  destination.close()
