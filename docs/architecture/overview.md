# Mimari Genel Bakış

SAĞDUYU, sosyal medya olaylarını platformdan bağımsız bir sözleşmeye dönüştürür; zaman, içerik ve ağ sinyallerinden koordinasyon adayları üretir; her adayı açıklanabilir kanıtlarla insan incelemesine sunar.

## Sistem akışı

```text
Platform adaptörü
      ↓
Ortak olay sözleşmesi
      ↓
Zaman pencereli özellik üretimi
      ↓
Koordinasyon grafiği ve aday kümeler
      ↓
Açıklanabilir risk birleştirme
      ↓
Moderatör kuyruğu ve kanıt kartı
      ↓
Karar ve denetim kaydı
```

## Bileşenler

### Olay adaptörleri

Gönderi, yeniden paylaşım, yanıt, bahsetme ve silme olaylarını ortak şemaya dönüştürür. Dosya tekrar oynatma ve sentetik senaryo adaptörleri geliştirme ortamında kullanılır. Gelecekte sağlanabilecek resmî platform erişimi aynı arayüz arkasında eklenebilir.

### Koordinasyon motoru

Kayan zaman pencerelerinde ortak hedef, yakın zamanlı davranış, metin benzerliği, tekrar eden hesap eşleşmeleri, ağ yoğunluğu ve olağan dışı hacim gibi sinyalleri hesaplar. Sinyaller, tek bir içerik veya görüş yerine hesaplar arası davranış örüntüsünü temsil eder.

### Risk ve açıklama katmanı

Her aday küme için risk puanı ile sinyal katkılarını üretir. Açıklama çıktısı; ilişkili hesapları, ortak nesneleri, zaman çizgisini ve en güçlü bağlantıları içerir.

### Moderasyon API'si

Alarm listesi, kanıt ayrıntısı, moderatör kararı ve denetim geçmişi için kararlı bir sözleşme sunar. Yaptırım uygulamaz; karar desteği sağlar.

### Web arayüzü

Analistin yüksek öncelikli adayları taramasını, kanıt grafiğini incelemesini ve gerekçeli karar vermesini sağlar.

## Model yaklaşımı

İlk taban; açıklanabilir graf özellikleri ve denetlenebilir bir risk birleştirme yöntemidir. GNN modelleri ayrı deneylerde karşılaştırılır. Bir model ancak doğruluk, organik davranıştaki yanlış pozitif oranı, gecikme ve açıklanabilirlik açısından ölçülebilir üstünlük sağlarsa çalışma zamanına alınır.

## Güven ve veri sınırları

- Sistem içerik doğruluğu hakkında hüküm vermez.
- Otomatik hesap kapatma veya içerik silme yapmaz.
- Özel mesajları işlemez.
- Ham sosyal medya verisi ve kişisel veri depoda tutulmaz.
- Sentetik olaylar makinece okunabilir biçimde işaretlenir.
- Her alarm ve moderatör kararı sürüm bilgisiyle denetlenebilir olmalıdır.
