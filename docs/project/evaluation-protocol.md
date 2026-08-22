# Değerlendirme Protokolü

Bu protokol, model ve kural tabanlı sürümlerin aynı veri ayrımı ve ölçüm tanımlarıyla karşılaştırılmasını sağlar.

## Değerlendirme birimi

Bir örnek tek tweet veya tek hesap değildir; bağımsız bir kampanya ya da organik gündem grafiğidir. JSONL adaptörü her örnekte kampanya kimliği, ayrım grubu, kaynak, veri sürümü, beklenen sınıf ve olay listesini zorunlu tutar.

## Veri ayrımı

- Aynı kampanya veya ilişkili gündem grubu eğitim ve testte birlikte bulunamaz.
- Gruplar en erken olay zamanına göre sıralanır.
- Holdout kümesi en yeni gruplardan oluşur.
- Rastgele düğüm veya tweet ayrımı sonuç olarak raporlanmaz.
- Sentetik kayıtlar gerçek veri sonuçlarıyla birleştirilmez.

## Ölçümler

- Makro-F1: koordineli ve organik sınıfların F1 değerlerinin aritmetik ortalaması
- Kesinlik: üretilen koordinasyon alarmlarının ne kadarının koordineli kampanya olduğu
- Duyarlılık: koordineli kampanyaların ne kadarının alarm ürettiği
- Yanlış pozitif oranı: organik örneklerin ne kadarının alarm ürettiği
- P50 ve P95 gecikme: bir kampanya grafiğinin analiz süresi

Her sonuç; motor sürümü, kaynak veri sürümü, örnek sayısı, ayrım adı, karışıklık matrisi ve sentetik veri bayrağıyla aynı JSON kaydında tutulur.

## Sonuç yayınlama kapısı

Bir sonuç ancak aşağıdaki koşullarda gerçek veri başarımı olarak yayımlanabilir:

1. Kaynak dosyanın URL veya sürümü ve SHA-256 özeti kayıtlıdır.
2. Veri lisansı kullanıma ve sonuç paylaşımına uygundur.
3. Kampanya/grup sızıntısı olmadığı doğrulanmıştır.
4. Komut ve motor sürümü kaydedilmiştir.
5. Sonuç sentetik veriden üretilmemiştir.

Sentetik senaryolar yalnızca sözleşme, uç durum ve ürün akışı testidir.

## Doğrulanan Ephemeral etiketi

Kayıtlı kaynak üzerinden indirilen `attack_annotations.csv` dosyası için:

- SHA-256: `d8bd1c885dc8634f5301458910ea7a5f5afa460d7e6e48532c6c42e17224a489`
- Satır: 10.984
- Benzersiz tweet kimliği: 5.493
- Tweet satırı: 5.493
- Silme satırı: 5.491

Dosyada olay zamanı, metin ve hesap kimliği bulunmadığı doğrulanmıştır. Bu nedenle tek başına koordinasyon motorunun başarım ölçümünde kullanılmaz; başka alanlar uydurulmaz. Kimliksiz toplu profil şu komutla yeniden üretilebilir:

```bash
python scripts/fetch_dataset.py ephemeral_annotations
python scripts/profile_ephemeral_annotations.py data/raw/ephemeral_attack_annotations.csv --output data/interim/ephemeral_profile.json
```
