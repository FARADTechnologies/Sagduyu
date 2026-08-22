# Türkçe Metin Normalizasyonu

Metin güvenliği katmanı, sınıflandırıcıdan önce yaygın karakter maskeleme yöntemlerini deterministik bir kanonik biçime dönüştürür.

## Desteklenen dönüşümler

- Unicode NFKC normalizasyonu
- Türkçe büyük/küçük harf dönüşümü
- sıfır genişlikli ve yönlendirme karakterlerinin temizlenmesi
- sınırlı Kiril ve Yunan benzer karakter eşlemesi
- rakam ve sembolle yapılan yaygın leetspeak dönüşümleri
- nokta, boşluk, yıldız veya tireyle ayrılmış harflerin birleştirilmesi
- üç veya daha fazla tekrarlanan karakterin sadeleştirilmesi
- Türkçe aksanların sınıflandırıcı için ASCII kanoniğine dönüştürülmesi

Katman özgün metnin yerine kalıcı kayıt oluşturmaz. Orijinal içerik, kanonik biçim ve uygulanan dönüşüm adları açıklama üretiminde ayrı alanlar olarak ele alınabilir.

## Sınırlar

Normalizasyon tek başına toksisite kararı vermez ve yaptırım uygulamaz. Benzer Unicode karakter eşlemeleri yalnızca açıkça kayıtlı sınırlı bir tabloyla yapılır. Saf sayısal diziler leetspeak olarak dönüştürülmez. Dönüşümün anlam kaybı ve yanlış eşleşme riski sınıflandırıcı değerlendirmesinde ayrıca ölçülmelidir.

`generate_masked_variants` işlevi, sabit test örneklerinden boşluk, nokta, yıldız, sıfır genişlikli karakter, leetspeak ve karakter tekrarı varyantları üretir. Bu varyantlar gerçek kullanıcı verisi değil, dayanıklılık testi girdileridir.
