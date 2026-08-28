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

Model karşılaştırmalarında kullanılan ayrım, ölçüm ve sonuç yayınlama kuralları [değerlendirme protokolünde](docs/project/evaluation-protocol.md) tanımlıdır.

Türkçe karakter maskelemesine karşı kullanılan kanonikleştirme adımları ve sınırları [metin normalizasyonu belgesinde](docs/project/text-normalization.md) açıklanır.

Gönderi öncesi uyarının kullanıcı seçimini koruyan ilk çalışma biçimi [nezaket katmanı demo tabanında](docs/project/courtesy-baseline.md) açıklanır.

LEN-Small açıklanabilir taban ve GCN karşılaştırmasının veri ayrımı ile kabul kapısı [GNN deney protokolünde](docs/project/gnn-experiment.md) tanımlıdır.

SentiTurca üzerinde BERTurk, Türkçe normalizasyon ve maskeleme dayanıklılığı karşılaştırması [Türkçe toksisite deney protokolünde](docs/project/turkish-toxicity-experiment.md) tanımlıdır.

Gerçek LEN-Small ve SentiTurca koşularından gelen seed, ortam, SHA, metrik ve
ürün kararları [doğrulanmış model seçim sonuçlarında](docs/project/verified-results.md)
kayıtlıdır.

Hangi bileşenin ürün prototipine alındığı, yöntem olarak kabul edildiği veya
ölçüm sonucunda reddedildiği [bileşen kabul matrisinde](docs/project/acceptance-matrix.md)
açıklanır.

Koordinasyon motorundaki açıklanabilir sinyallerin sonraki deneylerde nasıl
değiştirileceği ve hangi koşulda gerçek başarı sonucu sayılacağı [sinyal ağırlığı
duyarlılık deney sözleşmesinde](docs/project/signal-weight-experiment.md) tanımlıdır.

Üç ana senaryoyu, gerekçeli kararı, nezaket uyarısını ve toplu gecikme özetini
tek komutta doğrulayan akış [demo ve ölçüm kanıtında](docs/project/demo-evidence.md)
yer alır.

## Hızlı başlangıç

Python 3.12 veya üzeri gerekir.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m uvicorn sagduyu.api:app --reload
```

PowerShell kullanıyorsanız etkinleştirme komutu `.venv\Scripts\Activate.ps1` şeklindedir.

API belgesi servis başladıktan sonra `http://127.0.0.1:8000/docs` adresindedir.

API, web, PostgreSQL ve Neo4j servislerini birlikte başlatmak için örnek ortam dosyasını kopyalayıp yerel parolaları değiştirin, ardından:

```bash
docker compose up --build
```

Web arayüzü `http://127.0.0.1:5173`, API belgesi `http://127.0.0.1:8000/docs`, Neo4j Browser ise `http://127.0.0.1:7474` adresinde açılır. Docker kullanılmadığında API, kalıcı veri yazmayan bellek deposuyla çalışmaya devam eder.

Moderatör arayüzünü ayrı bir terminalde başlatmak için:

```bash
cd apps/web
pnpm install
pnpm dev
```

Arayüz `http://127.0.0.1:5173` adresinde açılır ve varsayılan olarak yerel API'ye bağlanır.

Örnek koordineli ve organik senaryolar komut satırından çalıştırılabilir:

```bash
python -m sagduyu coordinated-campaign
python -m sagduyu organic-discussion
python -m sagduyu announced-campaign
```

Tam jüri demo akışını ve beklenen olay/alarm sayılarını otomatik doğrulamak için:

```bash
python scripts/run_demo_evidence.py --output artifacts/demo-evidence.json
```

Kalite kontrolleri:

```bash
ruff format --check src tests scripts experiments
ruff check src tests scripts experiments
mypy src scripts
pytest --cov=sagduyu --cov-report=term-missing
```

## Veri ve ölçüm hattı

Kayıtlı bir public veri kaynağı ham veriyi depoya eklemeden indirilebilir. İndirilen dosyanın URL, boyut, zaman ve SHA-256 bilgisi otomatik kaydedilir:

```bash
python scripts/fetch_dataset.py ephemeral_annotations
python scripts/fetch_dataset.py len_metadata
```

Büyük `len_small` kaynağı kritik geliştirme yolundan bağımsızdır ve uygun disk/bulut ortamında isteğe bağlı indirilir.

Ephemeral etiket dosyasının kimliksiz toplu profili şu şekilde üretilir:

```bash
python scripts/profile_ephemeral_annotations.py data/raw/ephemeral_attack_annotations.csv --output data/interim/ephemeral_profile.json
```

Bu profil sınıf dağılımı, tekrar sayısı, kaynak özeti ve eksik alan sınırını kaydeder; tweet kimliklerini veya ham satırları dışarı taşımaz.

Platform adaptörlerinin ürettiği kampanya JSONL kayıtlarında zaman ve grup ayrımlı ölçüm çalıştırmak için:

```bash
sagduyu-evaluate data/interim/campaigns.jsonl --output artifacts/evaluation.json
```

Çıktı; veri sürümlerini, motor sürümünü, karışıklık matrisini, makro-F1, kesinlik, duyarlılık, yanlış pozitif oranı ve p50/p95 gecikmesini birlikte taşır.

## Depo yapısı

```text
src/sagduyu/   Analiz motoru, olay modelleri ve moderasyon API'si
tests/         Birim ve entegrasyon testleri
docs/          Mimari ve veri yönetişimi belgeleri
apps/          Web uygulamaları
notebooks/     Yeniden üretilebilir araştırma deneyleri
```

Kod, dizin ve API adları uluslararası araçlarla uyum için İngilizce; jüriye ve proje paydaşlarına yönelik dokümantasyon Türkçedir.

## Katkı

Tüm değişiklikler Issue → dal → Pull Request → inceleme akışıyla yapılır. Ayrıntılar için [katkı rehberine](CONTRIBUTING.md) bakın.
