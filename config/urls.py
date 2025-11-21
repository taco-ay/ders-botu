# config/urls.py

from django.contrib import admin
from django.urls import path, include # 'include' import edildi

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ogrenme.urls')), # <-- Burası eklendi!
    # Django'nun yerleşik giriş/çıkış sistemini de ekleyelim
    path('accounts/', include('django.contrib.auth.urls')), 
]