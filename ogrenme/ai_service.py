# ogrenme/ai_service.py

import os
import json # JSON çıktısını işlemek için eklendi
from django.conf import settings
from google import genai
from google.genai import types
import re

# ----------------------------------------------------
# 1. Müşteri (Client) Oluşturma
# ----------------------------------------------------
try:
    # settings.py'deki anahtarı kullanmaya devam ediyoruz
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    print(f"Hata: Gemini API istemcisi oluşturulamadı. settings.py'deki GEMINI_API_KEY'i kontrol edin. Hata: {e}")
    client = None 

# ----------------------------------------------------
# 2. Sistem Talimatları Tanımlamaları
# ----------------------------------------------------

SISTEM_TALIMATLARI_GENEL = (
    "Sen, 'AI Öğrenci Platformu' için geliştirilmiş, motive edici ve akademik bir öğrenim asistanısın. "
    "Öğrencinin tüm sorularına net, yardımsever ve motive edici bir dilde cevap ver. "
    "Kendini tanıtırken adını 'AI Asistan' olarak kullan. "
    "Konuşma tonun daima pozitif ve profesyonel olmalıdır."
)

SISTEM_TALIMATLARI_SORU_URET = (
    "Sen bir öğrencinin seviyesine özel, akademik olarak doğru, tek bir soru ve onun kesin, net, kısa doğru cevabını üreten bir uzmansın. "
    "Yanıtını SADECE JSON formatında döndürmelisin. JSON formatı: "
    "{'soru_metni': '...', 'dogru_cevap': '...'}"
    "Lütfen JSON dışında hiçbir metin, açıklama veya not ekleme."
)

SISTEM_TALIMATLARI_PLAN_URET = (
    "Sen, öğrencinin hedeflerine ulaşması için detaylı, motive edici ve günlük çalışma planları üreten bir koçsun. "
    "Senin tek görevin, öğrenciye hitap eden kısa ve net görevlerden oluşan bir liste oluşturmaktır. "
    "Çıktıyı KESİNLİKLE VE SADECE JSON formatında döndürmelisin. JSON yapısı: [{'gorev_baslik': '...', 'gorev_tipi': '...', 'aciklama': '...'}, ...]"
    "**JSON'DAN ÖNCE VEYA SONRA HİÇBİR AÇIKLAMA, GİRİŞ CÜMLESİ, MERHABA VEYA MOTİVASYONEL METİN EKLEME.**"
)

# ----------------------------------------------------
# 3. Ana Yapay Zeka Fonksiyonu (Güncellendi)
# ----------------------------------------------------
def yapay_zeka_soru_uret(input_data, soru_tipi):
    """
    Kullanıcının verilerine veya mesajına göre farklı AI çıktıları üretir.
    
    Args:
        input_data (dict/str): Seviye/ders bilgileri (dict) veya chat mesajı (str).
        soru_tipi (str): 'Odaklanmış Soru', 'Genel Sohbet' veya 'Plan Üretimi'.
        
    Returns:
        str/dict: AI yanıtı (str) veya Soru/Cevap/Plan (dict).
    """
    
    if client is None:
        return f"Yapay Zeka Servisi şu anda kullanılamıyor (Client Hata Kodu)."

    sistem_talimati = ""
    prompt_metni = ""

    if soru_tipi == "Odaklanmış Soru":
        # input_data: {'seviye': 5, 'ders_adi': 'Matematik'}
        seviye = input_data['seviye']
        ders_adi = input_data['ders_adi']
        
        sistem_talimati = SISTEM_TALIMATLARI_SORU_URET
        prompt_metni = (
            f"{ders_adi} dersi için, seviye {seviye} bir öğrenciye çözmesi için orta zorlukta bir soru üret. "
            f"Soru, öğrencinin konuya hakimiyetini ölçecek nitelikte olmalı. Soru ve cevabı JSON formatında döndür."
        )

    elif soru_tipi == "Genel Sohbet":
        # input_data: "Merhaba, nasılsın?" (Kullanıcının mesajı)
        sistem_talimati = SISTEM_TALIMATLARI_GENEL
        prompt_metni = input_data 

    elif soru_tipi == "Plan Üretimi":
        # input_data: {'seviye': 5, 'ders_adi': 'Matematik'}
        seviye = input_data['seviye']
        ders_adi = input_data['ders_adi']
        
        sistem_talimati = SISTEM_TALIMATLARI_PLAN_URET
        prompt_metni = (
            f"{ders_adi} dersinde seviye {seviye} olan bir öğrenci için 3 adet kısa, ölçülebilir ve motive edici görevden oluşan "
            f"bir çalışma listesi (JSON dizisi) oluştur. Görev tipleri sadece şunlar olmalı: SORU, OKUMA, OZET, PROJE."
        )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt_metni],
            config=types.GenerateContentConfig(
                system_instruction=sistem_talimati
            )
        )
        
        #JSON çıktılarını (Soru veya Plan) otomatik parse et
        if soru_tipi in ["Odaklanmış Soru", "Plan Üretimi"]:
             # Yanıtı temizleyerek JSON'a çevir
             
             import re # Fonksiyonun içinde re kullanıyoruz

             # AI'ın kullandığı ```json ... ``` bloğunu ayıkla
             match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
             
             if match:
                 raw_json = match.group(1).strip()
             else:
                 # Eğer blok yoksa, çıktının tamamını JSON olarak denemeye al
                 raw_json = response.text.strip()
             
             return json.loads(raw_json)
        
        # Genel Sohbet çıktısını (str) döndür
        return response.text
    
    except json.JSONDecodeError:
         # AI, JSON formatında yanıt vermezse
         return f"Yapay zeka (AI) JSON formatında yanıtlayamadı: {response.text[:100]}..."
         
    except Exception as e:
        return f"Yapay zeka sorgusu sırasında hata oluştu: {e}"