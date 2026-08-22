# SAĞDUYU

SAĞDUYU, sosyal medya platformlarında koordineli manipülasyon kampanyalarını davranış, zaman, içerik benzerliği ve etkileşim ağı sinyalleriyle tespit eden açıklanabilir bir karar destek katmanıdır.

Sistem tekil bir gönderinin doğru veya yanlış olduğuna hükmetmez. Birden fazla hesabın birlikte oluşturduğu örüntüyü inceler, alarmın hangi kanıtlara dayandığını gösterir ve son kararı insan moderatöre bırakır.

## Temel yetenekler

- Platformdan bağımsız olay şeması ve tekrar oynatma adaptörü
- Eşzamanlılık, benzer içerik, ortak hedef ve ağ yapısı analizi
- Sinyal katkılarını gösteren açıklanabilir kanıt kartları
- İnsan inceleme kuyruğu, karar kaydı ve denetlenebilir süreç
- Türkçe koordineli kampanya verileriyle yeniden üretilebilir deneyler

## Proje durumu

Proje aktif geliştirme aşamasındadır. İlk hedef, koordineli manipülasyon tespit motoru ile moderatör kanıt ekranını uçtan uca çalışan bir prototipte birleştirmektir.

Sistem bileşenleri ve teknik sınırlar [mimari genel bakışta](docs/architecture/overview.md), veri kaynakları ve kullanım koşulları ise [veri kaynağı kaydında](docs/project/data-sources.md) açıklanır.

## Depo yapısı

```text
apps/          Uygulama giriş noktaları
packages/      Paylaşılan uygulama paketleri
services/      Arka uç servisleri ve analiz motoru
tests/         Otomatik testler
docs/          Mimari, karar, deney ve rapor kanıtları
notebooks/     Yeniden üretilebilir araştırma deneyleri
```

Kod, dizin ve API adları uluslararası araçlarla uyum için İngilizce; jüriye ve proje paydaşlarına yönelik dokümantasyon Türkçedir.

## Katkı

Tüm değişiklikler Issue → dal → Pull Request → inceleme akışıyla yapılır. Ayrıntılar için [katkı rehberine](CONTRIBUTING.md) bakın.
