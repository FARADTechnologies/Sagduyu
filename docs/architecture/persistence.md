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
