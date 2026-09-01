# Kalıcılık Mimarisi

SAĞDUYU, geliştirme ve üretim benzeri çalışma biçimlerini aynı API sözleşmesinin arkasında ayırır.

## PostgreSQL

PostgreSQL alarmın tam kanıt belgesini JSONB olarak, risk ve inceleme durumunu ise sorgulanabilir sütunlarda tutar. Moderatör kararları ayrı ve eklemeli bir tabloda saklanır. Aynı alarm yeni analizle tekrar üretildiğinde kanıt belgesi güncellenir; mevcut insan kararı ve karar geçmişi korunur.

`SAGDUYU_DATABASE_URL` ayarlanmadığında sistem geçici bellek deposuna döner. Bu mod yalnızca geliştirme ve deterministik demo içindir.

## Neo4j

Neo4j adaptörü alarmı, ilişkili hesapları ve en güçlü hesap çiftlerini kanıt grafiğine yazar. Her ilişki alarm ve motor sürümüyle etiketlenir. Bu depo sorgulama ve görselleştirme içindir; risk skorunun tek kaynağı değildir.

Neo4j yalnızca URI, kullanıcı adı ve parola birlikte sağlandığında etkinleşir. Eksik yapılandırma sessizce kabul edilmez.

## Güvenlik sınırları

- `.env` ve gerçek kimlik bilgileri depoya eklenmez.
- `.env.example` yalnızca değiştirilecek örnek değerler içerir.
- Compose varsayılanları yerel geliştirme içindir ve production ortamında kullanılmamalıdır.
- Production parolaları secret yöneticisinden sağlanmalıdır.
- Public demo yalnızca sentetik veya açıkça yetkilendirilmiş veriyi kullanmalıdır.

## Uzaktan pilot için geçiş koşulları

Compose dosyası yerel geliştirme ve demo içindir; yayımlanan portlar yalnızca
`127.0.0.1` üzerinden erişilir. Uzaktan erişilebilen bir pilot ortamına geçmeden
önce aşağıdaki koşullar tamamlanmalıdır:

- Moderatör ve servis erişimi için kimlik doğrulama ile rol bazlı yetkilendirme
  tanımlanır.
- Trafik TLS sonlandıran bir ters vekil üzerinden alınır; CORS yalnızca pilot
  alan adıyla sınırlandırılır.
- Üretim sırları, kalıcı veritabanı parolaları ve bağlantı bilgileri secret
  yöneticisinden sağlanır.
- Analiz uçları için istek boyutu, zaman aşımı ve hız sınırları pilot yüküne
  göre yapılandırılır.

Bu maddeler uzaktan pilot için bir geçiş kontrol listesidir; mevcut yerel
prototipte tamamlanmış üretim özellikleri olarak yorumlanmamalıdır.
