# Bileşen Kabul Matrisi

Bu matris, doğrulanmış deney ve ürün kontrollerinin hangi karara dönüştüğünü
gösterir. Bir bileşenin çalışması tek başına ürün kabulü anlamına gelmez.
Başarım, yanlış pozitif riski, açıklanabilirlik ve güvenli kullanım sınırı
birlikte değerlendirilir.

## Durum tanımları

- **Ürün prototipinde:** Çalışan uçtan uca akışta doğrulanmıştır.
- **Yöntem olarak kabul:** Teknik yaklaşım kanıtlanmıştır; ilgili model veya
  checkpoint ürün bileşeni olarak kabul edilmemiş olabilir.
- **Araştırma tabanı:** Karşılaştırma ve sonraki kalibrasyon için kullanılır;
  otomatik karar vermez.
- **Reddedildi:** Önceden tanımlanan kabul koşullarını geçmemiştir.

| Bileşen | Durum | Doğrulama | Ürün sınırı |
|---|---|---|---|
| Koordinasyon analiz motoru | Ürün prototipinde | Koordineli ve organik tekrar oynatma senaryoları; API ve arayüz akışı | Etiketli platform verisiyle pilot yapılmadan üretim başarımı iddia edilmez |
| Açıklanabilir kanıt kartı ve moderatör kararı | Ürün prototipinde | Kuyruk, sinyal katkıları, graf, zaman çizgisi ve gerekçeli karar kaydı | Son karar insandadır; alarm otomatik yaptırım değildir |
| PostgreSQL karar günlüğü ve Neo4j kanıt grafı | Ürün prototipinde | Docker tam-yığın kontrolü, servis yeniden başlatma sonrası kalıcılık | Üretim kurulumu ayrı kimlik, yetki ve gizli bilgi yönetimi gerektirir |
| Türkçe maskeleme normalizasyonu | Yöntem olarak kabul | Maskeli SentiTurca testinde kalibre ham modele göre +0,1318 makro-F1; özgün-maskeli düşüş 0,00059 | Normalizasyon tek başına toksisite hükmü vermez |
| Doğrulama tabanlı karar kalibrasyonu | Yöntem olarak kabul | Test etiketlerine bakmadan FPR 0,1300'dan 0,0890'a indi | Yeni veri dağılımında yeniden kalibrasyon ve izleme gerekir |
| Normalize BERTurk seed 42 checkpoint'i | Reddedildi | Özgün makro-F1 0,5471 ile 0,55 kabul sınırının 0,0029 altında | Canlı ürün modeli veya tamamlanmış başarı olarak sunulmaz |
| LEN açıklanabilir toplu özellik tabanı | Araştırma tabanı | Üç seed ortalaması makro-F1 0,8306; FPR 0,2051 | Yüksek FPR nedeniyle yalnız insan incelemesi ve eşik araştırması için kullanılır |
| LEN GCN adayı | Reddedildi | Makro-F1 0,6068; tabana göre -0,2237 ve FPR +0,1795 | Daha karmaşık olduğu için değil, ölçülebilir biçimde daha kötü olduğu için ürüne alınmadı |
| Gönderi öncesi nezaket akışı | Ürün prototipinde | Maskeli metin uyarısı, gerekçe ve düzenle/devam et seçimi | Otomatik engelleme yoktur; kullanıcı metni kalıcı tutulmaz |

## Karar ilkesi

SAĞDUYU, tekil içeriğin doğruluğuna hükmeden veya kullanıcıyı otomatik
cezalandıran bir sistem olarak tasarlanmaz. Koordinasyon sinyalleri inceleme
adayı üretir, kanıtlar görünür biçimde sunulur ve gerekçeli karar insan
moderatör tarafından verilir. Meşru kampanyaların da benzer davranış örüntüsü
oluşturabilmesi nedeniyle yanlış pozitif oranı, makro-F1 kadar temel bir kabul
ölçütüdür.

Ayrıntılı seed, ortam, veri sürümü ve metrikler
[doğrulanmış model seçim sonuçlarında](verified-results.md) yer alır.

