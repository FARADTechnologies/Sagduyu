# Türkçe Toksisite ve Maskeleme Dayanıklılığı Deneyi

Bu deney, gönderi öncesi nezaket katmanındaki açık demo tabanını gerçek Türkçe bağlam sınıflandırmasıyla karşılaştırır. Demo tabanı güvenli geri dönüş ve açıklama sözleşmesi olarak kalır; gerçek veri sonucu üretilmeden model başarımı iddiası yapılmaz.

## Veri ve model

- Veri: `turkish-nlp-suite/SentiTurca`, `hate` yapılandırması
- Sabit veri sürümü: `1c60b26c0a2ec776b7fd7f9deba7f9f84cd296b8`
- Veri lisansı: CC BY-SA 4.0
- Ayrımlar: 42.175 eğitim, 5.000 doğrulama, 5.000 test örneği
- Sınıflar: `offensive`, `hate`, `neutral`, `civilized`
- Temel model: `dbmdz/bert-base-turkish-cased`
- Sabit model sürümü: `b6e1de16c983e0f2c70664591ea3f22810072608`
- Model lisansı: MIT

Ürün uyarısı için `offensive` ve `hate` risk; `neutral` ve `civilized` organik/risksiz sınıf olarak değerlendirilir. Dört sınıflı tahmin ve ikili uyarı metriği ayrı raporlanır.

## Deney tasarımı

İki ayrı BERTurk yapılandırması aynı resmî ayrımlarda eğitilir:

1. `raw`: özgün metinle eğitim ve değerlendirme
2. `normalized`: Türkçe kanonikleştirme sonrası eğitim ve değerlendirme

Test örnekleri eğitim veya doğrulama ayrımına taşınmaz. Her test metninin noktayla ayrılmış harf, sıfır genişlikli karakter ve leetspeak biçimleri yalnızca dayanıklılık değerlendirmesinde üretilir. Aynı metnin saldırı varyantları farklı veri ayrımlarına sızmaz.

Her yapılandırma için şu ölçümler kaydedilir:

- dört sınıflı macro-F1 ve doğruluk
- sınıf bazında kesinlik, duyarlılık ve F1
- ikili uyarı kesinliği, duyarlılığı ve yanlış pozitif oranı
- örnek başına çıkarım gecikmesi
- özgün ve maskeli test farkı
- veri/model sürümü, ortam ve checkpoint SHA-256 kayıtları

## Kabul kapısı

Normalize edilmiş model ancak aşağıdaki koşulların tamamında ürün adayıdır:

- özgün test macro-F1 en az `0,55`
- özgün organik yanlış pozitif oranı en fazla `0,10`
- maskeli test macro-F1 düşüşü en fazla `0,05`
- maskeli testte ham modele göre macro-F1 kazancı en az `0,10`

Kapının geçilememesi gizlenecek bir sonuç değildir. Bu durumda gerçek model ürün akışına bağlanmaz; demo tabanı açıkça etiketlenmiş biçimde kalır ve hata analizi raporlanır.

## Çalıştırma

Notebook, bulut ortamında proje deposunu alır ve deney betiğini çalıştırır. Komut satırı karşılığı:

```bash
python experiments/sentiturca_berturk.py \
  --output artifacts/sentiturca_results.json \
  --checkpoint-dir artifacts/sentiturca-checkpoints \
  --modes raw,normalized \
  --seeds 42 \
  --epochs 3
```

İlk geçiş iki yapılandırmayı tek tohumla karşılaştırır. Kabul kapısına yaklaşan yapılandırma, nihai rapor ölçümü için `11,23,37` tohumlarıyla tekrarlanır.
