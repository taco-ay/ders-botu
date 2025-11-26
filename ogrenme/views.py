# ogrenme/views.py

import re
import uuid
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.db import models
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib import messages

# Kendi uygulama importları
from .ai_service import yapay_zeka_soru_uret
from .forms import KayitFormu
# Tüm modelleri buraya import ediyoruz
from .models import Ders, OgrenciIlerleme, CevapKaydi, AISerbestChat, ChatOdasi, OdaMesaji, ArkadaslikIstegi


# ----------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ----------------------------------------------------
def rastgele_kod_uret():
    """6 haneli rastgele bir sayısal kod üretir."""
    return str(random.randint(100000, 999999))


# ----------------------------------------------------
# Ana Görünümler (Home & Dashboard)
# ----------------------------------------------------
def home_view(request):
    if request.user.is_authenticated:
        kullanici = request.user
        
        # 1. AKTIF_ID TANIMLAMA (Chat oturumu ID'si)
        aktif_id = request.session.get('aktif_chat_id')
        if not aktif_id:
            aktif_id = str(uuid.uuid4())
            request.session['aktif_chat_id'] = aktif_id
        # ----------------------------------------------------

        # 2. Ders Modelini Çekme
        try:
             matematik_dersi = Ders.objects.get(isim="Matematik")
        except Ders.DoesNotExist:
             matematik_dersi = None 
        
        # 3. İlerleme Objesi ve Arkadaşlık Kodu Yönetimi
        
        # 🥳 DÜZELTME: Alan adı artık kesin olarak 'kullanici'
        try:
            ilerleme_objesi, _ = OgrenciIlerleme.objects.get_or_create(
                kullanici=kullanici, # <-- DOĞRU ALAN ADI KULLANILDI
                defaults={'seviye': 1, 'ders': matematik_dersi} 
            )
        except Exception as e:
            return HttpResponse(f"Kritik Model Hatası: OgrenciIlerleme tablosunda eksik veri veya ilişki hatası. Hata: {e}", status=500)
        
        
        # Arkadaşlık Kodu Kontrolü ve Oluşturma
        if not ilerleme_objesi.arkadas_kodu:
            yeni_kod = rastgele_kod_uret()
            while OgrenciIlerleme.objects.filter(arkadas_kodu=yeni_kod).exists():
                yeni_kod = rastgele_kod_uret() 
                
            ilerleme_objesi.arkadas_kodu = yeni_kod
            ilerleme_objesi.save()
            
        kullanici_arkadas_kodu = ilerleme_objesi.arkadas_kodu
        # ----------------------------------------------------

        # 4. CHAT GEÇMİŞİ SORGULARI
        kaynak_merkezi_gecmisi = AISerbestChat.objects.filter(
            kullanici=kullanici,
            konusma_id=aktif_id,
            kullanici_mesaji__contains="Kaynak İsteği" 
        ).order_by('timestamp')

        serbest_chat_gecmisi = AISerbestChat.objects.filter(
            kullanici=kullanici,
            konusma_id=aktif_id
        ).exclude(
            kullanici_mesaji__contains="Kaynak İsteği"
        ).order_by('timestamp')

        context = {
            'serbest_chat_gecmisi': serbest_chat_gecmisi,
            'kaynak_merkezi_gecmisi': kaynak_merkezi_gecmisi,
            'kullanici_arkadas_kodu': kullanici_arkadas_kodu,
            'matematik_dersi': matematik_dersi 
        }
        return render(request, 'ogrenme/dashboard.html', context)
    else:
        return render(request, 'ogrenme/home.html', {})
        
# ----------------------------------------------------
# AI Test Görünümü (Soru Üretme Sayfası)
# ----------------------------------------------------
@login_required
def test_ai_view(request):
    
    try:
        matematik_dersi = Ders.objects.get(isim="Matematik")
    except Ders.DoesNotExist:
        return HttpResponse("HATA: Lütfen Yönetici Panelinde 'Matematik' dersini oluşturun.")
    
    # 🥳 DÜZELTME: Alan adı artık kesin olarak 'kullanici'
    try:
        ilerleme, created = OgrenciIlerleme.objects.get_or_create(
            kullanici=request.user, # <-- DOĞRU ALAN ADI KULLANILDI
            ders=matematik_dersi, 
            defaults={'seviye': 1, 'sinif_seviyesi': 10, 'ulkede_egitim': 'Türkiye'} 
        )
    except Exception as e:
        return HttpResponse(f"Model Sorgulama Hatası (test_ai_view): {e}", status=500)

    if 'current_question' in request.session and request.session['current_question']:
        current_q = request.session.get('current_question', {})
    else:
        try:
            input_data = {
                'seviye': ilerleme.seviye, 
                'ders_adi': matematik_dersi.isim,
                'sinif': ilerleme.sinif_seviyesi, 
                'ulke': ilerleme.ulkede_egitim
            }
            
            ai_data = yapay_zeka_soru_uret(input_data, "Odaklanmış Soru")
            
            request.session['current_question'] = ai_data
            current_q = ai_data
            
        except Exception as e:
            current_q = {'soru_metni': f"Yapay zeka sırasında hata oluştu: {e}", 'dogru_cevap': ''}
            request.session['current_question'] = current_q


    context = {
        'soru_metni': current_q.get('soru_metni', 'Soru Yüklenemedi. Lütfen tekrar deneyin.'),
        'ilerleme': ilerleme,
        'ders_adi': matematik_dersi.isim
    }

    return render(request, 'ogrenme/ai_test.html', context)

# ----------------------------------------------------
# Cevap Kontrol Görünümü (Geri Bildirim Sayfası)
# ----------------------------------------------------
@login_required
def cevap_kontrol_view(request):
    if request.method == 'POST':
        kullanici_cevabi = request.POST.get('cevap', '').strip()
        
        q_data = request.session.pop('current_question', None)
        
        if not q_data or 'soru_metni' not in q_data:
            return redirect('test_ai')
            
        dogru_cevap = q_data.get('dogru_cevap', '').strip()
        soru_metni = q_data.get('soru_metni', '')
        
        is_correct = (kullanici_cevabi.lower().strip() == dogru_cevap.lower().strip())
        
        # İlerleme Kaydı ve Güncelleme Mantığı
        if is_correct:
            # 🥳 DÜZELTME: Alan adı artık kesin olarak 'kullanici'
            try:
                OgrenciIlerleme.objects.filter(kullanici=request.user).update(
                    cozulen_soru_sayisi=F('cozulen_soru_sayisi') + 1
                )
            except Exception as e:
                print(f"İlerleme Güncelleme Hatası: {e}")
        
        # Cevap Kaydını oluştur
        CevapKaydi.objects.create(
            kullanici=request.user,
            ders=Ders.objects.get(isim="Matematik"),
            soru_icerigi=soru_metni,
            kullanici_cevabi=kullanici_cevabi,
            dogru_mu=is_correct,
        )
        
        context = {
            'is_correct': is_correct,
            'soru_metni': soru_metni,
            'kullanici_cevabi': kullanici_cevabi,
            'dogru_cevap': dogru_cevap,
        }
        
        return render(request, 'ogrenme/cevap_geri_bildirim.html', context)

    return redirect('test_ai') 

# ----------------------------------------------------
# Diğer Görünümler (Kayit Ol, Chat, Zihin Haritası vb.)
# ----------------------------------------------------
def kayit_ol_view(request):
    if request.method == 'POST':
        form = KayitFormu(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = KayitFormu()
    return render(request, 'registration/kayit_ol.html', {'form': form})

@login_required
def serbest_chat_view(request):
    if request.method == 'POST':
        mesaj = request.POST.get('mesaj', '')
        kullanici = request.user
        
        aktif_id = request.session.get('aktif_chat_id')
        if not aktif_id:
             aktif_id = str(uuid.uuid4())
             request.session['aktif_chat_id'] = aktif_id
        
        if mesaj:
            try:
                ai_yanit = yapay_zeka_soru_uret(mesaj, "Genel Sohbet")
                
                AISerbestChat.objects.create(
                    kullanici=kullanici,
                    kullanici_mesaji=mesaj,
                    ai_cevabi=ai_yanit,
                    konusma_id=aktif_id 
                )
            except Exception as e:
                print(f"Chat Hatası: {e}")
                messages.error(request, f"Yapay zeka sorgusu sırasında hata oluştu: {e}")
                
            return redirect('home')
        
    return redirect('home')
        
@login_required
def yeni_sohbet_baslat_view(request):
    """Mevcut oturum ID'sini yeni bir ID ile değiştirerek yeni bir sohbet başlatır."""
    request.session['aktif_chat_id'] = str(uuid.uuid4())
    messages.info(request, "Yeni bir sohbet oturumu başlatıldı.")
    return redirect('home')

@login_required
def zihin_haritasi_view(request):
    kullanici = request.user
    
    try:
        ders = Ders.objects.get(isim="Matematik")
        # 🥳 DÜZELTME: Alan adı artık kesin olarak 'kullanici'
        ilerleme, created = OgrenciIlerleme.objects.get_or_create(
            kullanici=kullanici, # <-- DOĞRU ALAN ADI KULLANILDI
            ders=ders, 
            defaults={'seviye': 1}
        )
    except Ders.DoesNotExist:
        return HttpResponse("HATA: Ders bulunamadı.", status=500)
    except Exception as e:
         return HttpResponse(f"HATA: Öğrenci İlerleme modeline ulaşılamadı. Models.py'yi kontrol edin. Hata: {e}", status=500)
        
    input_data = {
        'seviye': ilerleme.seviye, 
        'ders_adi': ders.isim,
        'sinif': ilerleme.sinif_seviyesi, 
        'ulke': ilerleme.ulkede_egitim
    }
    
    try:
        harita_taslagi = yapay_zeka_soru_uret(input_data, "Zihin Haritası Taslağı")
        
        context = {
            'harita_taslagi': harita_taslagi,
            'ders_adi': ders.isim
        }
        
        return render(request, 'ogrenme/zihin_haritasi.html', context)
        
    except Exception as e:
        return HttpResponse(f"Zihin Haritası Üretim Hatası: {e}", status=500)


@login_required
def kaynak_uret_view(request):
    if request.method == 'POST':
        konu_adi = request.POST.get('konu_adi', 'Temel Matematik Konuları') 
        istek_tipi = request.POST.get('istek_tipi', 'Zihin Haritası Taslağı')
        kullanici = request.user
        
        aktif_id = request.session.get('aktif_chat_id')
        
        if not aktif_id:
             aktif_id = str(uuid.uuid4()) 
             request.session['aktif_chat_id'] = aktif_id 
        
        try:
            matematik_dersi = Ders.objects.get(isim="Matematik")
            # 🥳 DÜZELTME: Alan adı artık kesin olarak 'kullanici'
            ilerleme, _ = OgrenciIlerleme.objects.get_or_create(
                kullanici=kullanici, # <-- DOĞRU ALAN ADI KULLANILDI
                ders=matematik_dersi, 
                defaults={'seviye': 1, 'sinif_seviyesi': 10, 'ulkede_egitim': 'Türkiye'}
            )

            input_data = {
                'seviye': ilerleme.seviye, 
                'ders_adi': matematik_dersi.isim, 
                'sinif': ilerleme.sinif_seviyesi, 
                'ulke': ilerleme.ulkede_egitim,
                'konu_adi': konu_adi
            }
            
            ai_yanit = yapay_zeka_soru_uret(input_data, istek_tipi)
            
            AISerbestChat.objects.create(
                kullanici=kullanici,
                konusma_id=aktif_id,
                kullanici_mesaji=f"Kaynak İsteği: {konu_adi} - {istek_tipi} (Seviye {ilerleme.seviye})",
                ai_cevabi=ai_yanit
            )
            messages.success(request, f"'{konu_adi}' konusunda yeni bir kaynak başarıyla oluşturuldu!")
        
        except Ders.DoesNotExist:
            messages.error(request, "HATA: Matematik dersi bulunamadı. Yönetici panelini kontrol edin.")
        except Exception as e:
            messages.error(request, f"Kaynak Üretim Hatası: {e}")
            print(f"Kaynak Üretim Hatası: {e}")
            
        return redirect('home')
        
    return redirect('home')

@login_required
def arkadas_ekle_view(request):
    if request.method == 'POST':
        arkadas_kodu = request.POST.get('arkadas_kodu')
        gonderen = request.user

        try:
            # OgrenciIlerleme'yi kod ile çekiyoruz.
            alici_ilerleme = OgrenciIlerleme.objects.get(arkadas_kodu=arkadas_kodu)
            alici = alici_ilerleme.kullanici # <-- DOĞRU ALAN ADI KULLANILDI
        except OgrenciIlerleme.DoesNotExist:
             messages.error(request, 'HATA: Bu arkadaşlık kodu bulunamadı.')
             return redirect('home')


        if gonderen == alici:
            messages.warning(request, 'Kendinizi ekleyemezsiniz.')
            return redirect('home')

        # Zaten bir istek gönderildi mi/alındı mı kontrol et
        if ArkadaslikIstegi.objects.filter(
            (Q(gonderen=gonderen, alici=alici) | Q(gonderen=alici, alici=gonderen)),
            kabul_edildi=False
        ).exists():
            messages.info(request, 'Bu kullanıcıya zaten bir arkadaşlık isteği gönderilmiş veya beklemede.')
            return redirect('home')

        # Arkadaşlık zaten kabul edilmiş mi?
        if ArkadaslikIstegi.objects.filter(
            (Q(gonderen=gonderen, alici=alici) | Q(gonderen=alici, alici=gonderen)),
            kabul_edildi=True
        ).exists():
            messages.info(request, 'Bu kişi zaten arkadaşınız.')
            return redirect('home')
        
        # İstek oluştur
        ArkadaslikIstegi.objects.create(gonderen=gonderen, alici=alici)
        messages.success(request, f'Arkadaşlık isteği {alici.username} kullanıcısına gönderildi.')
        return redirect('home')
    
    return redirect('home')