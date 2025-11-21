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
    path('plan-uret/', views.plan_uret_view, name='plan_uret'), # Çalışma planı üretme ve kaydetme
    path('chat/yeni/', views.yeni_sohbet_baslat_view, name='yeni_sohbet_baslat'),
    
    # --------------------------------------------------
    # KİMLİK DOĞRULAMA (AUTHENTICATION)
    # --------------------------------------------------
    path('kayit-ol/', views.kayit_ol_view, name='kayit_ol'), # Kayıt olma sayfası
    
    # Django'nun yerleşik giriş ve çıkış URL'leri:
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # Çıkış yaptıktan sonra anasayfaya yönlendir
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'), 
]