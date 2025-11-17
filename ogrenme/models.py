# ogrenme/models.py

from django.db import models
from django.contrib.auth.models import User # Django'nun hazır kullanıcı modelini kullanıyoruz

# 1. Ders Modeli (Matematik, Almanca, Fizik vb.)
class Ders(models.Model):
    isim = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, null=True, blank=True) # URL için kolay isim

    def __str__(self):
        return self.isim

# 2. Kullanıcı İlerleme Modeli (Veri Toplama Noktası)
# Bu model, kullanıcının belirli bir dersteki tüm istatistiklerini tutar.
class OgrenciIlerleme(models.Model):
    # Kullanıcı ile ilişki (auth.User modeline bağlanır)
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Ders ile ilişki
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE)

    # İlerleme Metrikleri (Görseldeki Gereksinimler)
    toplam_cozulen_soru = models.IntegerField(default=0) # "300 sorudan sonra" için
    dogru_cevap_sayisi = models.IntegerField(default=0)
    yanlis_cevap_sayisi = models.IntegerField(default=0)
    
    # Süre Metriği
    toplam_calisma_suresi_dk = models.IntegerField(default=0) # "20 dk" için
    
    # Yapay Zeka Geri Bildirimi/Seviye
    # Yapay zekanın kullanıcının seviyesini tuttuğu bir skor olabilir
    ai_seviye_skoru = models.DecimalField(max_digits=5, decimal_places=2, default=0.0) 

    son_guncelleme = models.DateTimeField(auto_now=True)

    # Bir kullanıcının aynı dersten sadece tek bir ilerleme kaydı olabilir
    class Meta:
        unique_together = ('kullanici', 'ders')

    def __str__(self):
        return f"{self.kullanici.username} - {self.ders.isim} İlerlemesi"


# 3. Cevap Kaydı Modeli (Geri Bildirim Döngüsü İçin)
# Bu model, kullanıcının her bir soru/cevap etkileşimini kaydeder.
class CevapKaydi(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE)
    
    # Soruyu Yapay Zeka Ürettiği İçin, Sorunun Metnini Saklıyoruz
    soru_metni = models.TextField()
    kullanici_cevabi = models.TextField()
    
    # Yapay zekanın doğru/yanlış geri bildirimi için
    is_dogru = models.BooleanField(default=False) 
    cevap_tarihi = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        durum = "Doğru" if self.is_dogru else "Yanlış"
        return f"{self.kullanici.username} - {self.ders.isim} - {durum}"