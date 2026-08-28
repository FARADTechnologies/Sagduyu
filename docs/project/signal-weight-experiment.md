# Sinyal Ağırlığı Duyarlılık Deney Sözleşmesi

Bu belge, koordinasyon motorundaki sinyal ağırlıklarının sonraki deneylerde nasıl
değiştirileceğini tanımlar. Henüz bir başarı metriği veya ürün modeli sonucu
yayımlamaz.

## Amaç

SAĞDUYU alarmının eşzamanlılık, içerik benzerliği, ortak hedef, tekrarlanan
birlikte hareket, ağ yoğunluğu ve toplu silme sinyallerine ne ölçüde bağlı
olduğunu görünür ve tekrar üretilebilir biçimde incelemek.

## Yapılandırma sözleşmesi

- Varsayılan ağırlıklar toplamı `1` olan altı sinyalden oluşur.
- Deney yapılandırması aynı altı anahtarı eksiksiz taşır; eksik veya ek anahtar
  kabul edilmez.
- Her ağırlık sonlu, negatif olmayan ve `1` değerini aşmayan bir sayıdır.
- Ağırlıkların toplamı `1` olmalıdır. Bir sinyal `0` yapılırsa kalan ağırlıklar
  açıkça yeniden dağıtılır; motor gizli normalizasyon yapmaz.
- Deney ağırlıkları yalnız güvenilir geliştirme/deney çağrısında verilir. API
  istemcisi sinyal ağırlığı değiştiremez.

## İlk mekanik kontroller

Bu kontroller performans ölçümü değildir:

1. Varsayılan yapılandırma, önceki alarm skorlarını ve kanıt kartlarını korur.
2. Bir sinyalin ağırlığı sıfırlandığında katkısı kanıt kartında sıfır görünür.
3. Her yapılandırmada sinyal katkılarının toplamı alarm skoruna karşılık gelir.
4. Geçersiz yapılandırma alarm üretmeden önce açık hata verir.

## Gerçek veri çalışmasına geçiş koşulu

Makro-F1, yanlış pozitif oranı veya eşik seçimi ancak olay düzeyinde zaman,
hesap, hedef ve metin alanlarını içeren; kampanya/grup sızıntısını önleyen
etiketli veriyle değerlendirilir. Sentetik senaryolar yalnızca yukarıdaki
mekanik sözleşmenin ve ürün akışının kontrolünde kullanılır.

## Sonraki deney

Her sinyal için ayrı azaltma ve sıfırlama koşulu çalıştırılacak; aynı veri
ayrımı, motor sürümü, ağırlık profili, karışıklık matrisi, makro-F1, yanlış
pozitif oranı ve gecikme birlikte kaydedilecektir. Ürün ağırlıkları, yalnızca
kilitli kabul kapılarını geçen koşullar arasında seçilecektir.
