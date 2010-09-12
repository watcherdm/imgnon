from django.db import models

# Create your models here.

class Image(models.Model):
  imgdata = models.FileField(upload_to="img")