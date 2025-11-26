# ogrenme/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # Django'nun yerleşik giriş/çıkış görünümleri için

urlpatterns = [
    # --------------------------------------------------
    # ANA VE DASHBOARD
    # --------------------------------------------------
    # Giriş yapılmışsa dashboard'u, yapılmamışsa home.html'i gösterir
    path('', views.home_view, name='home'),
    
    # --------------------------------------------------
    # AI ÖZELLİKLERİ
    # --------------------------------------------------
    path('test-ai/', views.test_ai_view, name='test_ai'), # Soru sorma sayfası
    path('cevapla/', views.cevap_kontrol_view, name='cevap_kontrol'), # Cevap kontrolü ve geri bildirim
    path('chat/', views.serbest_chat_view, name='serbest_chat'), # Dashboard sol paneldeki chat formunun işleyicisi
    path('chat/yeni/', views.yeni_sohbet_baslat_view, name='yeni_sohbet_baslat'),
    path('zihin-haritasi/', views.zihin_haritasi_view, name='zihin_haritasi'),
    path('kaynak-uret/', views.kaynak_uret_view, name='kaynak_uret'), # <-- YENİ EKLEME
    path('arkadas-ekle/', views.arkadas_ekle_view, name='arkadas_ekle'), 
    
    
    # --------------------------------------------------
    # KİMLİK DOĞRULAMA (AUTHENTICATION)
    # --------------------------------------------------
    path('kayit-ol/', views.kayit_ol_view, name='kayit_ol'), # Kayıt olma sayfası
    
    # Django'nun yerleşik giriş ve çıkış URL'leri:
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # Çıkış yaptıktan sonra anasayfaya yönlendir
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'), 
]