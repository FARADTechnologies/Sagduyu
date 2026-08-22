# Veri Kaynakları ve Kullanım Sınırları

Bu kayıt, veri kaynağı seçimini teknik uygunluk kadar erişim, lisans, boyut ve yeniden üretilebilirlik açısından da izler.

## NSosyal erişimi

İncelenen yarışma şartnamesi ve teknik rapor şablonu, yarışmacılara NSosyal API anahtarı, geliştirici paketi veya özel veri kümesi sağlanacağını belirtmiyor. Platform gizlilik politikası API erişiminin sınırlı veya lisanslı olabileceğini söylüyor; bu ifade yarışma takımlarına erişim verildiği anlamına gelmiyor.

Yarışma Google Grubu'nda API ve kullanıcı gönderilerine erişim sorusu paylaşılmıştır. Son kontrolde başlıkta resmî yanıt görünmemektedir.

Karar: Resmî kimlik bilgisi veya yazılı erişim sağlanmadıkça özel uç noktalar kullanılmayacak ve özel veri erişimi varsayılmayacaktır. Entegrasyon, platformdan bağımsız olay sözleşmesi arkasında tutulacaktır.

## Ephemeral Astroturfing

- Kaynak: <https://github.com/tugrulz/EphemeralAstroturfing>
- Yayın: <https://arxiv.org/abs/2304.07907>
- Uyum: Türkçe trend manipülasyonu, toplu paylaşım/silme ve koordineli hesap davranışı
- Ölçek: 212.916 tespit edilmiş hesap ve 29.271 sahte trend; depodaki trend istatistik tablosunda 530.403 satır
- Güçlü yön: Yerel dil ve doğrudan saldırı örüntüsü
- Sınırlama: Belirli bir ephemeral astroturfing davranışına odaklanır; geniş organik davranışı temsil etmez
- Lisans durumu: Kaynak depoda açık bir lisans dosyası bulunmuyor; README atıf yapılmasını ve araştırma kullanımı halinde iletişimi istiyor

Kullanım sınırı: Ham veri depoya yeniden dağıtılmayacak. Kaynak ve yayın açıkça atıflanacak; veri indirme/dönüştürme işlemleri ayrı ve yeniden üretilebilir tutulacak. Yayınlama veya türev veri dağıtımı öncesinde kullanım izni netleştirilecek.

## LEN — Large Engagement Networks

- Kaynak: <https://github.com/erdemUB/LEN>
- Veri sayfası: <https://erdemub.github.io/large-engagement-network/>
- Yayın: <https://doi.org/10.1609/icwsm.v19i1.35839>
- Uyum: Türkçe koordineli kampanya ve organik gündem ağlarının doğrudan karşılaştırması
- Kapsam: Yayında 179 kampanya ve 135 kampanya dışı ağ; kaynak sayfasındaki güncel kod tablosunda 170 kampanya ve 135 kampanya dışı ağ
- Boyut: Sunucu başlıklarına göre small arşivi yaklaşık 5,8 GB, tam arşiv yaklaşık 123 GB
- Lisans: Yayın, veri kümesini CC BY lisanslı olarak tanımlıyor
- Güçlü yön: Organik haber, spor, etkinlik ve duyurulmuş kampanya örneklerini içerir
- Sınırlama: Büyük dosya ve ağ boyutları; ücretsiz çalışma ortamlarında süre/bellek riski

Kullanım sınırı: Kritik prototip yolundan bağımsız bulut deneyi. Veri sürümü ve kaynak sayısındaki fark deney kaydında açıkça belirtilecek.

## Yeniden üretilebilir indirme kaydı

Public kaynak adresleri `configs/data-sources.toml` içinde sürümlenir. `scripts/fetch_dataset.py`, seçilen kaynağı `data/raw/` altına indirir ve dosyanın URL, lisans notu, indirme zamanı, byte büyüklüğü ve SHA-256 özetini ayrı metadata dosyasına yazar. Ham dosyalar ile metadata kayıtları public depodan hariç tutulur; doğrulanmış özetler kaynak sürümüyle birlikte raporlanır.

İndirici arşivleri otomatik açmaz ve veriyi dönüştürmez. Böylece kaynağın beklenmedik dosya yollarıyla çalışma alanına yazması engellenir; dönüşüm, doğrulanan ham dosyadan ayrı bir adaptör adımıdır.

## MGTAB

- Kaynak: <https://github.com/GraphDetec/MGTAB>
- Yayın: <https://arxiv.org/abs/2301.01123>
- Uyum: Çok ilişkili hesap düzeyi bot/insan sınıflandırması
- Kapsam: 10.199 uzman etiketli hesap ve yedi ilişki türü
- Lisans: CC BY-NC-ND 4.0
- Sınırlama: Koordineli kampanya sınıflandırması yerine hesap düzeyi bot tespitine odaklanır

Karar: İlk sürüm için gerekli değildir. Daha sonraki hesap-risk yardımcı sinyali araştırmasında, lisans sınırları korunarak değerlendirilebilir.

## Sentetik senaryolar

Sentetik veri yalnızca olay sözleşmesi, alarm akışı, sınır durumları ve kullanıcı arayüzü doğrulaması için kullanılacaktır. Gerçek dünya model başarımı iddiasında kullanılmayacaktır.

Asgari senaryolar:

- Organik haber patlaması
- Duyurulmuş topluluk kampanyası
- Aynı bağlantıyı kısa sürede yayan koordineli ağ
- Metni küçük değişikliklerle tekrarlayan koordineli ağ
- Toplu paylaşım ve kısa süre sonra toplu silme
- Az sayıda hesabın yüksek hacimde spam davranışı
