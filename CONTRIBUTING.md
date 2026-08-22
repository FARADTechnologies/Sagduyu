# Katkı Rehberi

## Çalışma akışı

1. Yapılacak işi ve kabul ölçütlerini bir Issue içinde tanımlayın.
2. Güncel `main` dalından kısa ömürlü bir çalışma dalı açın.
3. Küçük, anlamlı ve doğrulanabilir commit'ler oluşturun.
4. Issue bağlantısı, test kanıtı ve riskleri içeren bir Pull Request açın.
5. Kontroller tamamlanmadan ve inceleme yapılmadan `main` dalına birleştirmeyin.

## Adlandırma

- Özellik: `feat/<kısa-ingilizce-ad>`
- Hata düzeltmesi: `fix/<kısa-ingilizce-ad>`
- Dokümantasyon: `docs/<kısa-ingilizce-ad>`
- Bakım: `chore/<kısa-ingilizce-ad>`

Commit mesajlarında Conventional Commits biçimi kullanılır. Tür ve kapsam İngilizce, açıklama kısa ve Türkçe olabilir:

```text
feat(engine): zaman pencereli koordinasyon skorunu ekle
docs(project): veri stratejisini güncelle
test(api): alarm ayrıntısı sözleşmesini doğrula
```

## Pull Request ölçütleri

- Değişiklik tek bir amacı tamamlamalıdır.
- İlgili Issue `Closes #<numara>` ifadesiyle bağlanmalıdır.
- Çalıştırılan kontroller ve sonuçları açıkça yazılmalıdır.
- Ölçülmemiş performans veya başarı iddiaları eklenmemelidir.
- Mimari ve ürün kararları karar günlüğüne işlenmelidir.
- Kullanıcı verisi, erişim anahtarı, gizli yapılandırma ve ham veri depoya eklenmemelidir.

## Dil politikası

- README, proje dokümanları, Issue ve Pull Request metinleri Türkçedir.
- Kod, dosya/dizin adları, API alanları, şema adları ve teknik tanımlayıcılar İngilizcedir.
- Kullanıcıya gösterilen arayüz metinleri Türkçedir ve ayrı kaynak dosyalarında tutulur.

## Veri ve etik

- Yalnızca kullanım hakkı doğrulanmış veri kaynakları kullanılır.
- Ham sosyal medya verileri ve kişisel veriler sürüm kontrolüne alınmaz.
- Sentetik örnekler açıkça `synthetic` alanıyla işaretlenir.
- Sistem otomatik yaptırım aracı değil, insan denetimli karar destek sistemi olarak geliştirilir.
