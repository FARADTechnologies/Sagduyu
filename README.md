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

Örnek koordineli ve organik senaryolar komut satırından çalıştırılabilir:

```bash
python -m sagduyu coordinated-campaign
python -m sagduyu organic-discussion
python -m sagduyu announced-campaign
```

Kalite kontrolleri:

```bash
ruff format --check src tests
ruff check src tests
mypy src
pytest --cov=sagduyu --cov-report=term-missing
```

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
