# LEN GNN Rakip Deneyi

`notebooks/LEN_GNN_Challenger.ipynb`, LEN-Small üzerinde açıklanabilir toplu graf özellikleri tabanı ile iki katmanlı GCN modelini karşılaştırır. Notebook Colab veya Kaggle çalışma alanını otomatik seçer, resmî LEN-Small arşivini kaldığı yerden indirebilir ve gerekli Python paketlerini kurar.

## Protokol

- Ayrım birimi bağımsız grafiktir; düğüm ve kenarlar grafikler arasında bölünmez.
- Üç sabit seed kullanılır: 11, 23 ve 37.
- Her tekrarda sınıf oranını koruyan %25 holdout oluşturulur.
- Her iki model aynı train/test grafiklerini kullanır.
- Makro-F1, kesinlik, duyarlılık, organik yanlış pozitif oranı ve grafik başına gecikme kaydedilir.
- Sonuç LEN-Small arşivinin SHA-256 özeti; Python, PyTorch, PyTorch Geometric, scikit-learn ve NetworkX sürümleri; cihaz ve GPU bilgisiyle JSON'a yazılır.

## Kabul kapısı

GCN ancak ortalama makro-F1 değerinde açıklanabilir tabanı en az `0,02` geçer ve organik yanlış pozitif oranını `0,01` değerinden fazla kötüleştirmezse aday kabul edilir. Kapıyı geçememesi başarısız veya gizlenecek sonuç değildir; açıklanabilir tabanın çalışma zamanı modeli olarak kalması için deneysel gerekçedir.

Notebook içinde kayıtlı çıktı yoktur. Gerçek veri çalıştırması tamamlanmadan örnek veya varsayımsal metrik yayımlanmaz.
