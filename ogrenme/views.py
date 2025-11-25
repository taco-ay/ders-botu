# ogrenme/views.py
import re
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views

# Kendi uygulama importları
from .ai_service import yapay_zeka_soru_uret
from .forms import KayitFormu
# Tüm modelleri buraya import ediyoruz
from .models import Ders, OgrenciIlerleme, CevapKaydi, AISerbestChat

# ----------------------------------------------------
# Ana Görünümler (Home & Dashboard)
# ----------------------------------------------------
def home_view(request):
    if request.user.is_authenticated:
        kullanici = request.user
        aktif_id = request.session.get('aktif_chat_id')
        
        # 1. Kaynak Merkezi Geçmişi (Sadece Kaynak İstekleri)
        kaynak_merkezi_gecmisi = AISerbestChat.objects.filter(
            kullanici=kullanici,
            konusma_id=aktif_id,
            kullanici_mesaji__contains="Kaynak İsteği" 
        ).order_by('timestamp')

        # 2. Serbest Chat Geçmişi (Kaynak İstekleri DAHİL DEĞİL)
        # Bu, Serbest Chat'i Kaynak Merkezi'nden ayırır.
        serbest_chat_gecmisi = AISerbestChat.objects.filter(
            kullanici=kullanici,
            konusma_id=aktif_id
        ).exclude(
            kullanici_mesaji__contains="Kaynak İsteği" # Kaynak İsteklerini hariç tut
        ).order_by('timestamp')

        context = {
            'serbest_chat_gecmisi': serbest_chat_gecmisi, # YENİ değişken
            'kaynak_merkezi_gecmisi': kaynak_merkezi_gecmisi,
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
    
    # İlerleme nesnesini (veya yeni alanları içeren OgrenciIlerleme nesnesini) al
    ilerleme, created = OgrenciIlerleme.objects.get_or_create(
        kullanici=request.user, 
        ders=matematik_dersi, 
        defaults={'seviye': 1}
    )

    # Oturumda cevaplanmamış bir soru varsa, yeni soru üretme!
    if 'current_question' in request.session and request.session['current_question']:
        current_q = request.session.get('current_question', {})
    else:
        # Yeni soru üret
        try:
            # DÜZELTME BURADA: Sınıf ve Ülke bilgilerini input_data'ya ekliyoruz.
            input_data = {
                'seviye': ilerleme.seviye, 
                'ders_adi': matematik_dersi.isim,
                # KİŞİSELLEŞTİRME VERİLERİ:
                'sinif': ilerleme.sinif_seviyesi, 
                'ulke': ilerleme.ulkede_egitim
            }
            
            # AI'dan JSON formatında soru ve cevap alıyoruz
            ai_data = yapay_zeka_soru_uret(input_data, "Odaklanmış Soru")
            
            # Soru ve cevabı oturumda tut
            request.session['current_question'] = ai_data
            current_q = ai_data
            
        except Exception as e:
            current_q = {'soru_metni': f"Yapay zeka sırasında hata oluştu: {e}", 'dogru_cevap': ''}
            request.session['current_question'] = current_q


    context = {
        'soru_metni': current_q.get('soru_metni', 'Soru Yüklenemedi. Lütfen tekrar deneyin.'), # Not: Sizin kodunuzda 'soru_metri' yazıyordu, 'soru_metni' olarak düzelttim.
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
        
        # Oturumdan soruyu çek
        q_data = request.session.pop('current_question', None)
        
        if not q_data or 'soru_metni' not in q_data: # ⚠️ DÜZELTME BURADA YAPILDI (soru_metri -> soru_metni)
            return redirect('test_ai')
            
        dogru_cevap = q_data.get('dogru_cevap', '').strip()
        soru_metni = q_data.get('soru_metni', '')
        
        # Basit Kontrol: Gelişmiş kontrol için AI'a tekrar sormak gerekir.
        # Biz şimdilik cevabın ilk 10 karakterini veya tamamını karşılaştıralım.
        is_correct = (kullanici_cevabi.lower().strip() == dogru_cevap.lower().strip())
        
        # İlerleme Kaydı ve Güncelleme Mantığı
        if is_correct:
            # İlerlemeyi artır
            OgrenciIlerleme.objects.filter(kullanici=request.user).update(
                cozulen_soru_sayisi=F('cozulen_soru_sayisi') + 1
            )
        
        # Cevap Kaydını oluştur
        CevapKaydi.objects.create(
            kullanici=request.user,
            ders=Ders.objects.get(isim="Matematik"), # Varsayılan ders
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
        
        # Geri bildirim şablonunu göster
        return render(request, 'ogrenme/cevap_geri_bildirim.html', context)

    return redirect('test_ai') 

# ----------------------------------------------------
# Diğer Görünümler (Kayit Ol, Chat)
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
        
        # ⚠️ DÜZELTME BURADA: Aktif chat ID'sini oturumdan çek
        # Eğer oturumda yoksa (ki bu olmamalı), bir hata önleyici olarak yeni bir tane oluştur
        aktif_id = request.session.get('aktif_chat_id')
        if not aktif_id:
             aktif_id = str(uuid.uuid4())
             request.session['aktif_chat_id'] = aktif_id
        # ----------------------------------------------------
        
        if mesaj:
            try:
                # Yapay Zeka servisini Genel Sohbet tipiyle çağır
                ai_yanit = yapay_zeka_soru_uret(mesaj, "Genel Sohbet")
                
                AISerbestChat.objects.create(
                    kullanici=kullanici,
                    kullanici_mesaji=mesaj,
                    ai_cevabi=ai_yanit,
                    konusma_id=aktif_id # <-- 🔑 Burası EKLEME/DÜZELTME noktası!
                )
            except Exception as e:
                print(f"Chat Hatası: {e}")
                
            return redirect('home')
        
    return redirect('home') # POST yoksa veya mesaj boşsa ana sayfaya dön
        
@login_required
def yeni_sohbet_baslat_view(request):
    """
    Kullanıcının mevcut serbest chat geçmişini silmez, ancak yeni bir sohbet başlatma izlenimi verir.
    İleride, bu fonksiyon farklı bir 'chat_id' atayarak konuşma geçmişlerini ayırabilir.
    Şimdilik sadece Dashboard'a yönlendiriyoruz.
    """
    # Not: Gerçek bir geçmiş ayrımı için 'AISerbestChat' modeline 'konusma_id' alanı eklenmesi gerekir.
    # Şimdilik, sadece kullanıcının anasayfaya yönlendirilmesi yeterlidir.
    return redirect('home')

@login_required
def zihin_haritasi_view(request):
    kullanici = request.user
    
    try:
        # Örnek olarak Matematik dersini alıyoruz.
        ders = Ders.objects.get(isim="Matematik")
        ilerleme, created = OgrenciIlerleme.objects.get_or_create(
            kullanici=kullanici, 
            ders=ders, 
            defaults={'seviye': 1}
        )
    except Ders.DoesNotExist:
        return HttpResponse("HATA: Ders bulunamadı.", status=500)
        
    # AI'a gönderilecek veriyi hazırla
    input_data = {
        'seviye': ilerleme.seviye, 
        'ders_adi': ders.isim,
        'sinif': ilerleme.sinif_seviyesi, 
        'ulke': ilerleme.ulkede_egitim
    }
    
    try:
        # Yeni AI tipini kullanarak taslağı üret
        harita_taslagi = yapay_zeka_soru_uret(input_data, "Zihin Haritası Taslağı")
        
        context = {
            'harita_taslagi': harita_taslagi,
            'ders_adi': ders.isim
        }
        
        # Yeni bir template ('ogrenme/zihin_haritasi.html' gibi) kullanabilirsiniz.
        return render(request, 'ogrenme/zihin_haritasi.html', context)
        
    except Exception as e:
        return HttpResponse(f"Zihin Haritası Üretim Hatası: {e}", status=500)


@login_required
def kaynak_uret_view(request):
    if request.method == 'POST':
        konu_adi = request.POST.get('konu_adi', 'Temel Matematik Konuları') 
        istek_tipi = request.POST.get('istek_tipi', 'Zihin Haritası Taslağı')
        kullanici = request.user
        
        # 🛑 KRİTİK DÜZELTME 🛑
        # Aktif chat ID'sini çek. Eğer yoksa, bu bir hatadır, çünkü kaynak üretimi 
        # sadece aktif bir sohbet varken yapılmalıdır.
        aktif_id = request.session.get('aktif_chat_id')
        
        # Eğer aktif chat ID yoksa, yeni bir tane oluşturup o ID'yi kullan. 
        # (Bu, chat_gecmisi'nin de bu yeni ID'yi çekmesini sağlayacak.)
        if not aktif_id:
             aktif_id = str(uuid.uuid4()) 
             request.session['aktif_chat_id'] = aktif_id 
        # ----------------------
        
        try:
            # ... (Ders ve ilerleme çekme kodları aynı kalır) ...
            matematik_dersi = Ders.objects.get(isim="Matematik")
            ilerleme, _ = OgrenciIlerleme.objects.get_or_create(
                kullanici=kullanici, 
                ders=matematik_dersi, 
                defaults={'seviye': 1, 'sinif_seviyesi': '10. Sınıf', 'ulkede_egitim': 'Türkiye'}
            )

            input_data = {
                'seviye': ilerleme.seviye, 
                'ders_adi': matematik_dersi.isim, 
                'sinif': ilerleme.sinif_seviyesi, 
                'ulke': ilerleme.ulkede_egitim,
                'konu_adi': konu_adi
            }
            
            ai_yanit = yapay_zeka_soru_uret(input_data, istek_tipi)
            
            # Kaydı, mevcut aktif ID ile yap
            AISerbestChat.objects.create(
                kullanici=kullanici,
                konusma_id=aktif_id, # Aktif olan ID'yi kullanıyoruz
                kullanici_mesaji=f"Kaynak İsteği: {konu_adi} - {istek_tipi} (Seviye {ilerleme.seviye})",
                ai_cevabi=ai_yanit
            )
        
        except Exception as e:
            # Hata yönetimi (loglama veya kullanıcıya gösterme)
            print(f"Kaynak Üretim Hatası: {e}")
            pass
        
        return redirect('home')
        
    return redirect('home')