# Doğrulanmış Model Seçim Sonuçları

Bu kayıt yalnızca tamamlanmış gerçek veri koşularını içerir. Örnek, tahminî veya
literatürden aktarılmış metrikler proje sonucu olarak sunulmaz. Ham veri,
checkpoint ve kişisel içerik depoda tutulmaz.

## LEN-Small graf karşılaştırması

### Veri ve protokol

- Resmî arşiv SHA-256: `aaa1fdc13f5ee581b4006f024c0753871b652debbe31f97958082399729b1c75`
- Graf sayısı: 104; 53 kampanya, 51 kampanya dışı
- Ayrım birimi: bağımsız graf
- Ayrım: her seed için stratified %75 eğitim / %25 test
- Seed'ler: `11`, `23`, `37`
- GCN eğitimi: 40 epoch
- Ortam: Tesla T4, PyTorch `2.11.0+cu128`, PyG `2.8.0.post1`,
  scikit-learn `1.9.0`, NetworkX `3.6.1`

| Seed | Açıklanabilir taban makro-F1 | Taban FPR | GCN makro-F1 | GCN FPR |
|---:|---:|---:|---:|---:|
| 11 | 0,8452 | 0,0769 | 0,6905 | 0,2308 |
| 23 | 0,8462 | 0,1538 | 0,4808 | 0,6923 |
| 37 | 0,8003 | 0,3846 | 0,6492 | 0,2308 |
| **Ortalama** | **0,8306** | **0,2051** | **0,6068** | **0,3846** |

GCN, açıklanabilir toplu graf özellikleri tabanından `0,2237` daha düşük
makro-F1 verdi ve yanlış pozitif oranını `0,1795` artırdı. Önceden tanımlanan
`+0,02` makro-F1 ve en fazla `+0,01` FPR koşulunu geçmedi.

**Karar:** GCN ürün motoruna alınmadı. Açıklanabilir taban karşılaştırmayı açık
farkla kazandı; ancak ortalama FPR değeri doğrudan otomatik yaptırım için yüksek
olduğundan yalnız insan inceleme adayı ve sonraki kalibrasyon çalışmalarının
tabanı olarak değerlendirilir.

## SentiTurca BERTurk dayanıklılık karşılaştırması

### Veri ve protokol

- Veri: `turkish-nlp-suite/SentiTurca`, `hate` yapılandırması
- Veri sürümü: `1c60b26c0a2ec776b7fd7f9deba7f9f84cd296b8`
- Ayrımlar: 42.175 eğitim, 5.000 doğrulama, 5.000 test
- Model: `dbmdz/bert-base-turkish-cased`
- Model sürümü: `b6e1de16c983e0f2c70664591ea3f22810072608`
- Koşu: seed `42`, 3 epoch
- Kalibrasyon: sınıf sapmaları ve ikili uyarı eşiği yalnızca doğrulama
  ayrımında öğrenildi; test etiketleri ayar için kullanılmadı
- Ortam: Tesla T4, PyTorch `2.11.0+cu128`, Transformers `4.57.6`,
  Datasets `4.0.0`

| Yapılandırma | Özgün makro-F1 | Maskeli makro-F1 | Özgün ikili FPR |
|---|---:|---:|---:|
| Ham, kalibrasyonsuz | 0,5066 | 0,3139 | 0,1687 |
| Ham, kalibre | 0,5727 | 0,4147 | 0,0916 |
| Normalize, kalibrasyonsuz | 0,5052 | 0,5051 | 0,1300 |
| **Normalize, kalibre** | **0,5471** | **0,5465** | **0,0890** |

Normalize ve kalibre yapılandırma, maskeli testte ham ve kalibre modele göre
`+0,1318` makro-F1 kazandı. Özgün-maskeli düşüş yalnızca `0,00059` oldu ve
özgün yanlış pozitif oranı `%10` sınırının altına indi.

Özgün makro-F1 `0,5471` ile önceden tanımlanan `0,55` kapısının `0,0029`
altında kaldı. Bu nedenle toplam ürün kabulü `false` olarak korundu.

**Karar:** Türkçe normalizasyonun maskeleme dayanıklılığı ve doğrulama tabanlı
uyarı eşiği kabul edildi. Bu tek-seed BERTurk checkpoint'i henüz canlı ürün
modeli olarak alınmadı; sonraki aday yeni seed'lerde aynı kapıları geçmeden
ürün başarımı iddiası yapılmayacak.

## Ürün sınırı

Her iki deney de otomatik yaptırım yerine açıklanabilir kanıt ve insan
incelemesi yaklaşımını destekliyor. Model karmaşıklığı tek başına seçim nedeni
değildir; daha karmaşık yöntem ancak aynı ayrım ve metriklerde ölçülebilir bir
kazanç sağlarsa ürün adayı olur.
