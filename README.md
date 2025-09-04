# Kaufland Fiyat Hesaplama Uygulaması 🛒

Kaufland pazar yerindeki ürünleriniz için doğru satış fiyatını belirlemenize, kârlılığı izlemenize ve iki lojistik rota arasında en ekonomik seçimi yapmanıza yardımcı olan Streamlit tabanlı web uygulaması.

## ✨ Özellikler

- **Çift Rota Karşılaştırması**: TR→NL→DE (aktarmalı) ve TR→DE (direkt) rotalarını karşılaştırır
- **Dinamik Fiyat Hesaplama**: Ham maliyet, navlun, vergi ve komisyon hesaplarını otomatik yapar
- **Kârlılık Analizi**: Ürün bazında kâr marjı ve tasarruf hesapları
- **Veri Yönetimi**: CSV import/export ile kolay veri yönetimi
- **Gerçek Zamanlı Hesaplama**: Parametreleri değiştirdiğinizde anında sonuç görün
- **Optimal Rota Önerisi**: En düşük maliyetli rotayı otomatik belirler

## 🚀 Canlı Demo

Uygulamaya şu linkten erişebilirsiniz: [Kaufland Fiyat Hesaplama](https://kauflandiwahesap.streamlit.app)

## 🛠️ Kurulum

### Gereksinimler

- Python 3.8+
- pip (Python paket yöneticisi)

### Kurulum Adımları

1. **Repository'yi klonlayın:**
   ```bash
   git clone https://github.com/yourusername/kaufland-fiyat-hesaplama.git
   cd kaufland-fiyat-hesaplama
   ```

2. **Virtual environment oluşturun (önerilen):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # veya
   venv\Scripts\activate  # Windows
   ```

3. **Gerekli paketleri yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Uygulamayı çalıştırın:**
   ```bash
   streamlit run app.py
   ```

## ☁️ Supabase Kalıcı Depolama (Önerilen)

Aşağıdaki adımlarla verilerinizi Supabase üzerinde kalıcı tutabilirsiniz. Bu sayede tarayıcı kapansa bile tüm eklemeler/düzenlemeler korunur.

1. Supabase projesi oluşturun: app.supabase.com → New project
2. `supabase.sql` dosyasındaki sorguyu çalıştırın:
   - Supabase Studio → SQL → New query → `supabase.sql` içeriğini yapıştırın → Run
3. API bilgilerini alın:
   - Project Settings → API → `Project URL` ve `anon` key
4. Streamlit Secrets tanımlayın:
   - Streamlit Cloud → App → Settings → Secrets (veya yerelde `.streamlit/secrets.toml`)
   - Aşağıdaki anahtarları ekleyin:
     - `supabase_url = "https://<PROJECT-REF>.supabase.co"`
     - `supabase_key = "<ANON-KEY>"`
5. Uygulamayı yeniden başlatın. Artık ürün verileri `products` tablosuna yazılır/okunur.

Notlar:
- Kod, Supabase secrets yoksa otomatik olarak yerel CSV’ye döner. Cloud ortamında kalıcılık için secrets zorunludur.
- `products` şeması metinsel değerlerle (örn. `€12.34`) uyumlu olacak şekilde text kolonlar kullanır. İsterseniz ileride sayısal kolonlara geçirilebilir.

5. Tarayıcınızda `http://localhost:8501` adresine gidin.

## 📊 Kullanım

### 1. Parametreleri Ayarlayın
Sol yan panelden aşağıdaki parametreleri ayarlayabilirsiniz:
- **Reklam Maliyeti (€)**: Ürün başına reklam maliyeti
- **Pazar Yeri Kesintisi (%)**: Platform komisyon oranı
- **Vergi Yüzdesi (%)**: Ürünün vergisel yükü

### 2. Veri Yükleme
- CSV dosyasını yükleyerek ürün verilerinizi içe aktarın
- Mevcut verileri JSON formatında dışa aktarabilirsiniz

### 3. Hesaplama ve Analiz
- Uygulama otomatik olarak her ürün için iki rota hesaplar
- En düşük maliyetli rota "Optimal Rota" olarak işaretlenir
- Kâr marjları ve tasarruf tutarları gösterilir

## 📁 Dosya Yapısı

```
kaufland-fiyat-hesaplama/
├── app.py                 # Ana uygulama dosyası
├── kauflandurunler.csv    # Örnek ürün verileri
├── README.md             # Bu dosya
├── requirements.txt      # Python bağımlılıkları
├── wiki.md              # Detaylı dokümantasyon
└── .gitignore           # Git ignore dosyası
```

## 💰 Rota Hesaplama Mantığı

### TR→NL→DE Rotası (Aktarmalı)
```
Ham Maliyet + Unit In + Box In + Pick Pack + Storage + FedEx + NL→DE Navlun + Reklam + Vergi + Pazar Yeri Kesintisi
```

### TR→DE Rotası (Direkt)
```
Ham Maliyet + Express Kargo + DDP + Reklam + Vergi + Pazar Yeri Kesintisi
```

## 📈 Hesaplanan Metrikler

- **Temel Maliyet**: Rota bazlı ham maliyet + lojistik maliyetler
- **Son Maliyet**: Tüm ek maliyetler dahil toplam maliyet
- **Kâr Marjı**: Satış fiyatı - Son maliyet
- **Kâr Marjı %**: (Kâr Marjı / Satış Fiyatı) × 100
- **Tasarruf**: İki rota arasındaki maliyet farkı

## 🎯 Hedef Kullanıcılar

- **Satın Alma/Ürün Yöneticileri**: Maliyet ve fiyat doğrulaması
- **Pazarlama/Performans Ekipleri**: Reklam maliyetinin kârlılığa etkisini izleme
- **Operasyon/Lojistik**: Rota bazlı maliyet farkları ve tasarruf analizi

## 🔧 Teknolojiler

- **Streamlit**: Web arayüzü framework'ü
- **Pandas**: Veri işleme ve analiz
- **Python**: Ana programlama dili

## 📝 CSV Dosya Formatı

CSV dosyanızın şu sütunları içermesi gerekir:
- `title`: Ürün adı
- `ean`: EAN kodu
- `fiyat`: Satış fiyatı (€)
- `ham_maliyet_euro`: Ham maliyet (€)
- `unit_in`, `box_in`, `pick_pack`, `storage`, `fedex`: TR çıkış maliyetleri
- `ne_de_navlun`: Hollanda-Almanya navlun maliyeti
- `express_kargo`, `ddp`: Direkt rota maliyetleri

## 🤝 Katkıda Bulunma

1. Repository'yi fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 📞 İletişim

Sorularınız için [GitHub Issues](https://github.com/yourusername/kaufland-fiyat-hesaplama/issues) kullanabilirsiniz.

---

**Not**: Bu uygulama iç kullanım için geliştirilmiştir. Para birimi Euro (€) üzerinden hesaplanır.
