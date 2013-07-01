from django.db import models


# Create your models here.
class SomeDBModel(models.Model):
    date_dump = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, editable=False)
