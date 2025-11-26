# ogrenme/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User

# ----------------------------------------------------
# 1. Ders Modeli (Courses)
# ----------------------------------------------------
class Ders(models.Model):
    isim = models.CharField(max_length=100, unique=True)
    aciklama = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Dersler"

    def __str__(self):
        return self.isim

# ----------------------------------------------------
# 2. Öğrenci İlerleme Modeli (Student Progress)
# ----------------------------------------------------
class OgrenciIlerleme(models.Model):
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE) 
    
    # 💥 DÜZELTME: Eski satırların boş kalabilmesi için null/blank eklendi.
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, null=True, blank=True)
    
    seviye = models.IntegerField(default=1)
    cozulen_soru_sayisi = models.IntegerField(default=0)
    son_aktiflik = models.DateTimeField(auto_now=True)
    
    sinif_seviyesi = models.IntegerField(default=5, verbose_name="Sınıf Seviyesi")
    ulkede_egitim = models.CharField(max_length=50, default="Türkiye", verbose_name="Eğitim Aldığı Ülke")

    # 🥳 EKLENEN ALAN
    arkadas_kodu = models.CharField(max_length=6, unique=True, null=True, blank=True)

    class Meta:
        unique_together = ('kullanici', 'ders')
        verbose_name = "Öğrenci İlerleme Kaydı"
        verbose_name_plural = "Öğrenci İlerleme Kayıtları"

    def __str__(self):
        return f"{self.kullanici.username} - {self.ders.isim} (Seviye {self.seviye})"

# ----------------------------------------------------
# 3. Cevap Kayıt Modeli (Answer History)
# ----------------------------------------------------
class CevapKaydi(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE)
    soru_icerigi = models.TextField()
    kullanici_cevabi = models.TextField()
    dogru_mu = models.BooleanField(default=False)
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cevap Kaydı"
        verbose_name_plural = "Cevap Kayıtları"

    def __str__(self):
        return f"{self.kullanici.username} - {self.ders.isim} ({'Doğru' if self.dogru_mu else 'Yanlış'})"

# ----------------------------------------------------
# 4. AI Serbest Chat Modeli (Free Chat History)
# ----------------------------------------------------
class AISerbestChat(models.Model):
    # Hata buradaydı: İki sınıfı birleştirdik.
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    konusma_id = models.UUIDField(default=uuid.uuid4, verbose_name="Konuşma ID'si") # <-- EKLENDİ
    kullanici_mesaji = models.TextField()
    ai_cevabi = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Serbest Chat Kaydı"
        verbose_name_plural = "AI Serbest Chat Kayıtları"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.kullanici.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class ArkadaslikIstegi(models.Model):
    # İstek gönderen kullanıcı
    gonderen = models.ForeignKey(User, related_name='gonderilen_istekler', on_delete=models.CASCADE)
    # İstek alan kullanıcı
    alici = models.ForeignKey(User, related_name='alinan_istekler', on_delete=models.CASCADE)
    # İstek kabul edildi mi?
    kabul_edildi = models.BooleanField(default=False)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gonderen.username} -> {self.alici.username} ({'Kabul' if self.kabul_edildi else 'Bekliyor'})"

class ChatOdasi(models.Model):
    # Birçok kullanıcı tek bir odada olabilir (Örn: Grup chat'i, ama şimdilik 1'e 1 chat için kullanacağız)
    katilimcilar = models.ManyToManyField(User, related_name='chat_odalari')
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    # Odaları URL'de kullanmak için benzersiz bir isim (UUID yerine basit id de yeterli)
    def __str__(self):
        usernames = ", ".join([user.username for user in self.katilimcilar.all()])
        return f"Chat Odası ({self.pk}): {usernames}"

class OdaMesaji(models.Model):
    oda = models.ForeignKey(ChatOdasi, related_name='mesajlar', on_delete=models.CASCADE)
    gonderen = models.ForeignKey(User, on_delete=models.CASCADE)
    icerik = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('timestamp',) # Mesajları kronolojik olarak sıralar

    def __str__(self):
        return f"{self.gonderen.username}: {self.icerik[:20]}..."
    

