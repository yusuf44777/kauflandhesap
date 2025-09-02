# Kaufland Fiyat Hesaplama Uygulaması

Kaufland pazar yerindeki ürünleriniz için doğru satış fiyatını belirlemenize, kârlılığı izlemenize ve iki lojistik rota arasında en ekonomik seçimi yapmanıza yardımcı olan iç araç.

## Uygulama Bağlantısı

- Erişim: https://kauflandiwahesap.streamlit.app
- Paylaşım: Kurum içi kullanım için uygundur (Streamlit).
- Para birimi: Tüm tutarlar Euro (€) üzerinden hesaplanır.

## Kimler İçin?

- Satın alma / ürün yöneticileri: Maliyet ve fiyat doğrulaması yapar.
- Pazarlama / performans ekipleri: Reklam maliyetinin kârlılığa etkisini izler.
- Operasyon / lojistik: Rota bazlı maliyet farklarını ve tasarrufları görür.

## Temel Kavramlar

- Ürün: Ad, EAN, satış fiyatı, ham maliyet ve lojistik verileri ile tanımlanır.
- Rota seçenekleri:
  - TR→NL→DE (aktarmalı)
  - TR→DE (direkt)
- Global parametreler: Reklam maliyeti (€), pazar yeri kesintisi (%) ve vergi (%) yan panelden ayarlanır ve tüm hesaplamalara uygulanır.
- Veri kaynağı: Ürünler CSV ile yönetilir; dışa aktarım (export) ve içe aktarım (import) desteklenir.

## Parametreler (Yan Panel)

- Reklam maliyeti (€): Ürün başına sabit reklam tutarı (opsiyonel ancak kârlılıkta etkili).
- Pazar yeri kesintisi (%): Platform komisyon oranı (ör. 15).
- Vergi (%): Ürünün vergisel yükü (ör. 20).

## Rotalar ve Maliyet Mantığı

- TR→NL→DE (aktarmalı): Ham maliyet + Türkiye çıkış işlemleri (unit_in, box_in, pick_pack, storage, fedex) + NL→DE navlun (ne_de_navlun) + reklam + vergi + pazar yeri kesintisi.
- TR→DE (direkt): Ham maliyet + express_kargo + ddp + reklam + vergi + pazar yeri kesintisi.
- Seçim: İki rota için “Son Maliyet” karşılaştırılır; düşük olan “Optimal Rota” olarak işaretlenir. Aradaki fark “Tasarruf” olarak gösterilir.

## Hesaplanan Metrikler

- Satış fiyatı: Ürünün platformdaki satış fiyatı (kullanıcı girişi).
- Temel maliyet: Rota bazlı ham maliyet + ilgili navlun/operasyonel kalemler toplamı.
- Reklam dahil: Temel maliyet + reklam maliyeti.
- Vergi: Reklam dahil tutar × vergi yüzdesi.
- Pazar yeri kesintisi: Reklam dahil tutar × kesinti yüzdesi.
- Son maliyet: Reklam dahil + vergi + pazar yeri kesintisi.
- Kâr marjı: Satış fiyatı − son maliyet.
- Kâr marjı %: (Satış fiyatı − son maliyet) / satış fiyatı × 100.
- Optimal rota: Son maliyeti düşük olan rota.
- Tasarruf: İki rotanın son maliyetleri arasındaki fark.

## Sekmeler ve İş Akışları

### Ürün Listesi

- Özet metrikler: Ortalama satış fiyatı, ortalama kâr, ortalama kâr %, kârlı ürün sayısı.
- Gelişmiş filtreler: Ürün adına göre arama, kâr durum filtresi; satış fiyatı aralığı, kâr % aralığı ve rota (TR→NL→DE / TR→DE) çoklu seçimi.
- Koşullu renklendirme: Negatif kâr hücreleri kırmızı, kâr % <10 sarı ile vurgulanır.
- Satır içi düzenleme: "Tabloda düzenlemeyi etkinleştir" ile fiyat ve maliyet alanlarını düzenleyin; "Değişiklikleri Kaydet" ile CSV güncellenir.
- Silme: EAN seçerek bir veya birden fazla ürünü listeden silebilirsiniz.
- Tablo: Satış fiyatı, her iki rota maliyeti, optimal rota, son maliyet, kâr ve kâr %.
- İpucu: Filtreleri ve renklendirmeyi kullanarak zararda veya düşük kârlı ürünleri hızlıca ayıklayın.

### Yeni Ürün Ekle

- Zorunlu alanlar: Ürün adı, satış fiyatı, ham maliyet.
- Opsiyonel alanlar: EAN, IWASKU, desi, navlun/operasyon kalemleri.
- Not: Gelişmiş operasyon kalemleri (unit_in, box_in, pick_pack, storage, fedex vb.) formda 0 girilebilir; detay için CSV import tercih edilebilir.
- Ekleme sonrası: Ürün listeye dahil olur; metrikler otomatik güncellenir.

### Fiyat Hesaplama

- Ürün seçimi: Tek bir ürün için derinlemesine analiz.
- Rota karşılaştırması: Her iki rota için temel maliyet, reklam dahil, vergi, kesinti ve “Son Maliyet”.
- Optimal seçim: En iyi rota, optimal maliyet ve tasarruf tutarı.
- Bileşen tablosu: Rota bazında maliyet kalemlerinin kırılımı.
- Özet ve uyarılar: Satış fiyatı, toplam maliyet, kâr, kâr %. Zararsa kırmızı uyarı; kâr % < 10 ise dikkat uyarısı.

### Export / Import

- Export (CSV / Excel / JSON): Liste + hesaplanmış metrikler dışa aktarılır. Excel’de ayrıca “Parametreler” sayfası bulunur (yan panel değerleri).
- Boş şablon: "Boş CSV Şablonu (İndir)" ile doğru kolon adlarını içeren boş bir CSV indirebilirsiniz.
- Import (CSV): Şablonla uyumlu CSV yükleyin; doğrulama yapılır, eksik sütunlar ve hatalı değerler için yönlendirme verilir. EAN üzerinden duplike kayıtlar temizlenir.
- Öneri: Önce küçük bir örnek export alın; dosyayı şablon olarak kullanın ve verinizi bu yapıya uydurun.

### Analiz

- Genel istatistikler: Toplam ürün, kârlı/zararlı ürün sayısı, ortalama kâr %.
- Sıralamalar: En kârlı 5 ve en zararlı 5 ürün.
- Dağılım: Kâr % aralıklarına göre sınıflandırma (Çok Yüksek >30, Yüksek 20–30, Orta 10–20, Düşük 0–10, Zararlı <0) ve grafik.
- Öneriler: Zararlı ürün sayısı, düşük kâr sayısı ve genel kârlılık durumuna göre rehber mesajlar.
- Pareto: Kâr katkısına göre ilk %20 ürün listelenir; Pareto kârı ve toplam kârdaki payı metrik olarak gösterilir.
- Rota kazanımı: “Hollanda üzerinden tasarruf” ve “Direkt rota avantajı” toplamları + her rota için ürün sayısı metrikleri.
- Senaryo analizi: Yan paneli bozmadan, “Komisyon Δ (puan)”, “Reklam Δ (€)”, “Vergi Δ (puan)” girdileriyle what‑if hesaplanır; toplam kâr, kârlı ürün sayısı ve ortalama kâr % için delta’lar gösterilir.

## Hızlı Başlangıç (3 Adım)

1) Parametreleri ayarlayın: Yan panelden reklam, kesinti ve vergi değerlerini kurum politikalarınıza göre belirleyin.
2) Veri ekleyin: Hızlı test için “Yeni Ürün Ekle”; gerçek çalışma için “Export” alıp şablona göre CSV hazırlayın ve “Import”.
3) Analiz edin: “Ürün Listesi” ve “Analiz” ile genel durumu; “Fiyat Hesaplama” ile tekil ürünleri inceleyin.

## İpuçları ve En İyi Uygulamalar

- Parametre güncelliği: Reklam ve kesinti oranlarını sözleşme/performans verilerine göre düzenli güncelleyin.
- Rota karşılaştırması: “Tasarruf” metriği anlamlıysa tedarik/lojistik kararı için tetikleyici olarak kullanın.
- Düşük kâr alarmı: Kâr % < 10 görünen ürünleri fiyat veya maliyet kalemleri açısından gözden geçirin.
- CSV şablonu: Export edilen CSV yapısını referans alın; sütun adları bire bir eşleşmelidir.
- EAN benzersizliği: Import sırasında duplikeler EAN ile tespit edilir; en son kayıt saklanır.

## CSV Alanları

| Alan                | Zorunlu | Açıklama                                           | Not / Örnek                    |
|---------------------|---------|----------------------------------------------------|--------------------------------|
| `title`             | Evet    | Ürün adı                                          |                                |
| `fiyat`             | Evet    | Satış fiyatı (€)                                  | 24.99                          |
| `ham_maliyet_euro`  | Evet    | Ürünün ham maliyeti (€)                           | 10.50                          |
| `ean`               | Önerilir| Benzersiz ürün kodu                               | Duplike kontrolü için kullanılır|
| `iwasku`            | Hayır   | İç SKU / stok kodu                                |                                |
| `desi`              | Hayır   | Kargo/desi bilgisi                                |                                |
| `unit_in`           | Hayır   | TR→NL→DE operasyon kalemi                         |                                |
| `box_in`            | Hayır   | TR→NL→DE operasyon kalemi                         |                                |
| `pick_pack`         | Hayır   | TR→NL→DE operasyon kalemi                         |                                |
| `storage`           | Hayır   | TR→NL→DE operasyon kalemi                         |                                |
| `fedex`             | Hayır   | TR→NL→DE operasyon kalemi                         |                                |
| `ne_de_navlun`      | Hayır   | NL→DE navlun                                      |                                |
| `express_kargo`     | Hayır   | TR→DE kargo                                       |                                |
| `ddp`               | Hayır   | TR→DE DDP maliyeti                                |                                |
| `reklam`            | Hayır   | Ürün bazlı reklam maliyeti (boşsa global değer)   |                                |

## Sık Sorulanlar (SSS)

- Parametreler neyi etkiler? Tüm ürünlerde reklam, vergi ve kesinti kalemlerini; maliyet ve kârlılık doğrudan değişir.
- Hangi rota daha iyi? Ürüne ve maliyet kalemlerine göre değişir; uygulama “Optimal Rota”yı otomatik seçer ve tasarrufu gösterir.
- Import hatası alıyorum. Sütun adlarını şablonla eşleyin; sayısal alanları sayı olarak girin (€, noktalama vb. kullanmayın).
- Negatif kâr görüyorum. Satış fiyatını artırın, reklamı optimize edin veya maliyet kalemlerini (özellikle navlun/operasyon) güncelleyin.

## Sorun Giderme

- Veriler görünmüyor: Önce ürün ekleyin veya geçerli bir CSV import edin.
- Metrikler tutarsız: Parametreleri kontrol edin; ürün bazlı maliyet alanlarında boş/0 değer kalmış olabilir.
- Excel indirme sorunu: Excel mümkün değilse CSV formatını kullanın.

## Destek

- Sahip: Ürün maliyetlendirme aracı (Kaufland) – İç ekip.
- Geri bildirim: Kâr dağılım aralıkları ve uyarı eşikleri kurum politikalarına göre güncellenebilir; önerilerinizi iletin.

Bu doküman, uygulamayı ilk kez kullanan ekiplerin hızla adapte olmasını ve rotalara göre kârlılık analizi yaparak karar almasını hedefler. Uygulamayı açın, parametreleri belirleyin, veriyi ekleyin ve metriklerle yönetin.
