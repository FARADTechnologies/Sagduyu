# Nezaket Katmanı Demo Tabanı

Gönderi öncesi nezaket katmanı, kullanıcının metni paylaşmadan önce olası incitici dili gözden geçirmesini sağlar. İlk çalışan sürüm, Türkçe normalizasyon katmanının katkısını uçtan uca göstermek için küçük ve açık bir eşleşme tabanı kullanır.

## Davranış

1. Metin cihaz/uygulama içindeki API'ye gönderilir.
2. Maskeleme biçimleri kanonikleştirilir.
3. Açık demo tabanındaki tam kelime eşleşmeleri bulunur.
4. Eşleşme, kategori, dönüşüm adımları ve risk katkısı kullanıcıya açıklanır.
5. Kullanıcı metni düzenleyebilir veya uyarıya rağmen devam edebilir.

Sistem bu akışta gönderiyi engellemez, silmez ve kullanıcıya yaptırım uygulamaz. İstekler kalıcı olarak kaydedilmez.

## Ölçüm sınırı

`transparent_demo_baseline_v1` bir üretim toksisite modeli değildir. Bağlam, ironi, alıntı ve hedef analizi yapmaz. Bu tabandan üretilen sonuçlar gerçek veri makro-F1 değeri olarak raporlanmaz. Amaç; normalizasyon, açıklama, kullanıcı uyarısı ve seçim hakkı sözleşmesini doğrulamaktır.

Model tabanlı sürüm, lisansı ve veri ayrımı doğrulanan Türkçe veri üzerinde eğitildikten sonra aynı API sözleşmesi arkasına eklenebilir. Demo tabanı karşılaştırma ve güvenli geri dönüş yolu olarak kalır.
