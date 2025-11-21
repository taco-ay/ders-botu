# ogrenme/admin.py

from django.contrib import admin
from .models import Ders, OgrenciIlerleme, CevapKaydi # Modelleri import ediyoruz

# Modelleri yönetici paneline kaydetme
admin.site.register(Ders)
admin.site.register(OgrenciIlerleme)
admin.site.register(CevapKaydi)