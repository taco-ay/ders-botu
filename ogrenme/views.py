# ogrenme/views.py
import re
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
from .models import Ders, OgrenciIlerleme, CevapKaydi, AISerbestChat, CalismaPlani 

# ----------------------------------------------------
# Ana Görünümler (Home & Dashboard)
# ----------------------------------------------------
def home_view(request):
    if request.user.is_authenticated:
        kullanici = request.user
        
        # 1. Serbest Chat Geçmişini Çekme (Dashboard Sol Panel)
        chat_gecmisi = AISerbestChat.objects.filter(kullanici=kullanici).order_by('-timestamp')[:10]

        # 2. Çalışma Planı Görevlerini Çekme (Dashboard Orta Panel)
        calisma_plani_gorevleri = CalismaPlani.objects.filter(
            kullanici=kullanici
        ).exclude(
            durum='TAMAM'
        ).order_by('durum', '-olusturma_tarihi')[:10]

        context = {
            'chat_gecmisi': chat_gecmisi,
            'calisma_plani': calisma_plani_gorevleri,
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
            input_data = {'seviye': ilerleme.seviye, 'ders_adi': matematik_dersi.isim}
            # AI'dan JSON formatında soru ve cevap alıyoruz
            ai_data = yapay_zeka_soru_uret(input_data, "Odaklanmış Soru")
            
            # Soru ve cevabı oturumda tut
            request.session['current_question'] = ai_data
            current_q = ai_data
            
        except Exception as e:
            current_q = {'soru_metni': f"Yapay zeka sırasında hata oluştu: {e}", 'dogru_cevap': ''}
            request.session['current_question'] = current_q


    context = {
        'soru_metni': current_q.get('soru_metri', 'Soru Yüklenemedi. Lütfen tekrar deneyin.'), 
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
        
        if not q_data or 'soru_metri' not in q_data:
            return redirect('test_ai') 
            
        dogru_cevap = q_data.get('dogru_cevap', '').strip()
        soru_metni = q_data.get('soru_metri', '')
        
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
        
        if mesaj:
            try:
                # Yapay Zeka servisini Genel Sohbet tipiyle çağır
                ai_yanit = yapay_zeka_soru_uret(mesaj, "Genel Sohbet")
                
                AISerbestChat.objects.create(
                    kullanici=kullanici,
                    kullanici_mesaji=mesaj,
                    ai_cevabi=ai_yanit
                )
            except Exception as e:
                print(f"Chat Hatası: {e}")
                
            return redirect('home')
        
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

# ----------------------------------------------------
# AI Çalışma Planı Üretme Görünümü
# ----------------------------------------------------
@login_required
def plan_uret_view(request):
    kullanici = request.user

    try:
        matematik_dersi = Ders.objects.get(isim="Matematik")
        ilerleme, created = OgrenciIlerleme.objects.get_or_create(
            kullanici=kullanici, 
            ders=matematik_dersi, 
            defaults={'seviye': 1}
        )
    except Ders.DoesNotExist:
        return HttpResponse("HATA: 'Matematik' dersi bulunamadı.", status=500)

    # 1. Mevcut tüm aktif (YENI, BASLADI) planları sıfırla/sil
    CalismaPlani.objects.filter(kullanici=kullanici).exclude(durum='TAMAM').delete()
    
    # Not: Eğer aktif plan sayısını kontrol eden bir mantık varsa, artık gerek yok.
    # Her zaman yeni bir plan oluşturulacak.

    # 2. Yapay Zekadan yeni plan iste
    try:
        input_data = {'seviye': ilerleme.seviye, 'ders_adi': matematik_dersi.isim}
        ai_yanit = yapay_zeka_soru_uret(input_data, "Plan Üretimi")

        plan_listesi = []
        
        if isinstance(ai_yanit, str):
            # JSON bloğunu ayıkla (ai_service.py'de de yapsak burada da garantiye alıyoruz)
            match = re.search(r'```json\s*(.*?)\s*```', ai_yanit, re.DOTALL)
            
            raw_json = match.group(1).strip() if match else ai_yanit.strip()
            
            import json
            plan_listesi = json.loads(raw_json)
        
        elif isinstance(ai_yanit, list):
            plan_listesi = ai_yanit
        

        if isinstance(plan_listesi, list):
            yeni_gorevler = []
            
            # 3. Gelen JSON listesindeki görevleri veritabanına kaydet
            for gorev_data in plan_listesi:
                if all(key in gorev_data for key in ['gorev_baslik', 'gorev_tipi', 'aciklama']):
                    
                    gorev_tipi = gorev_data['gorev_tipi'].upper()
                    
                    izin_verilen_tipler = [tip[0] for tip in CalismaPlani.GOREV_TIPI]
                    if gorev_tipi not in izin_verilen_tipler:
                        gorev_tipi = 'DIGER' 
                        
                    yeni_gorevler.append(
                        CalismaPlani(
                            kullanici=kullanici,
                            ders=matematik_dersi,
                            gorev_baslik=gorev_data['gorev_baslik'],
                            gorev_aciklama=gorev_data['aciklama'],
                            gorev_tipi=gorev_tipi,
                            durum='YENI'
                        )
                    )
            
            if yeni_gorevler:
                CalismaPlani.objects.bulk_create(yeni_gorevler)
                
            # Eğer AI yanıtı bir metin ise, plan oluşturulmadı (Muhtemelen bug'a girdik)
            else:
                # Kullanıcıya boş bir plan gösterilmesini sağlamak için hata yokmuş gibi devam et
                pass


    except Exception as e:
        print(f"Plan Üretim veya Kayıt Hatası: {e}")
        # Hata durumunda bile anasayfaya yönlendir
        pass 

    return redirect('home')