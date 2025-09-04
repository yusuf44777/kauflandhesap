#!/usr/bin/env python3
"""
Supabase Setup & CSV Migration Script
Bu script önce tabloyu oluşturur, sonra CSV'yi aktarır.
"""

import pandas as pd
import sys
import os
from supabase import create_client

# Supabase connection config
SUPABASE_URL = "https://xtygcxtrjdqhrqmrnlpc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh0eWdjeHRyamRxaHJxbXJubHBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NjcwODIsImV4cCI6MjA3MjU0MzA4Mn0.z4Dlkn2YlAByk4ICQHNxBqZjKdLkwu4FuMAoPA07qo8"

# CSV file path
CSV_FILE = "kauflandurunler.csv"

def create_table_if_not_exists(client):
    """Tablo yoksa oluşturur."""
    print("📋 Tablo kontrolü yapılıyor...")
    
    # Önce tablo var mı kontrol et
    try:
        result = client.table("products").select("count", count="exact").execute()
        print(f"✅ Tablo zaten mevcut! Kayıt sayısı: {result.count}")
        return True
    except Exception as e:
        print("📝 Tablo yok, oluşturuluyor...")
        
    # Raw SQL ile tablo oluştur (bu PostgREST API üzerinden olmayabilir)
    # Manuel olarak Supabase dashboard'da çalıştırmanız gerekiyor
    
    print("❌ Tablo otomatik oluşturulamıyor.")
    print("🔧 Lütfen Supabase Dashboard'da şu adımları izleyin:")
    print("   1. https://supabase.com/dashboard adresine gidin")
    print("   2. Projenizi seçin")
    print("   3. SQL Editor → New Query")
    print("   4. supabase.sql dosyasındaki kodu çalıştırın")
    print("   5. Sonra bu script'i tekrar çalıştırın")
    
    return False

def migrate_csv_to_supabase():
    """CSV dosyasını Supabase'e aktarır."""
    
    print("🚀 CSV to Supabase Migration Başlatıldı...")
    
    # 1. CSV dosyasını oku
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV dosyası bulunamadı: {CSV_FILE}")
        return False
    
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"✅ CSV dosyası okundu: {len(df)} satır")
        
        # İlk birkaç satırı göster
        print("📊 CSV Önizleme:")
        print(df.head(3).to_string())
        print()
        
    except Exception as e:
        print(f"❌ CSV okuma hatası: {str(e)}")
        return False
    
    # 2. Supabase bağlantısı
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase bağlantısı kuruldu")
    except Exception as e:
        print(f"❌ Supabase bağlantı hatası: {str(e)}")
        return False
    
    # 3. Tablo kontrolü ve oluşturma
    if not create_table_if_not_exists(client):
        return False
    
    # 4. Mevcut kayıt kontrolü
    try:
        result = client.table("products").select("count", count="exact").execute()
        existing_count = result.count
        print(f"✅ Mevcut kayıt sayısı: {existing_count}")
    except Exception as e:
        print(f"❌ Tablo erişim hatası: {str(e)}")
        return False
    
    # 5. Veri temizleme ve hazırlama
    print("📝 Veri hazırlanıyor...")
    
    # Database için gerekli kolonlar (CSV artık bunları içeriyor)
    required_columns = [
        'title', 'ean', 'iwasku', 'fiyat', 'ham_maliyet_euro', 'desi',
        'tr_ne_navlun', 'ne_de_navlun', 'kara_tr_de_navlun',
        'express_kargo', 'ddp', 'hava_tr_de_navlun', 'reklam'
    ]
    
    # CSV'de eksik kolonları kontrol et
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"   ❌ CSV'de eksik kolonlar: {missing_columns}")
        print("   💡 Lütfen önce fix_csv.py script'ini çalıştırın!")
        return False
    
    # Sadece gerekli kolonları al
    df_clean = df[required_columns].fillna("")
    
    # String formatına çevir (Supabase'deki text alanlarla uyumlu olması için)
    df_clean = df_clean.astype(str)
    
    print(f"✅ Veri hazırlandı: {len(df_clean)} satır, {len(df_clean.columns)} kolon")
    
    # 6. Eğer varsa mevcut verileri temizle (opsiyonel)
    if existing_count > 0:
        print(f"⚠️  Veritabanında {existing_count} kayıt var.")
        choice = input("   Silip yeniden eklemek ister misiniz? (y/n): ")
        if choice.lower() == 'y':
            try:
                # Tüm kayıtları sil
                client.table("products").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                print("🗑️  Mevcut veriler silindi")
            except Exception as e:
                print(f"⚠️  Veri silme hatası: {str(e)}")
        else:
            print("📝 Mevcut veriler korunuyor, yeni veriler eklenecek.")
    
    # 7. Bulk insert
    try:
        records = df_clean.to_dict('records')
        print(f"📤 {len(records)} kayıt ekleniyor...")
        
        # Büyük veri setlerini parça parça ekle
        batch_size = 20  # Küçük batch size ile hatayı önle
        success_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                client.table("products").insert(batch).execute()
                success_count += len(batch)
                print(f"   ✅ {success_count}/{len(records)} kayıt eklendi")
            except Exception as e:
                print(f"   ❌ Batch {i+1}-{i+len(batch)} hatası: {str(e)}")
                # İlk hatada dur ve detay ver
                print(f"   📋 Hatalı batch örneği: {batch[0] if batch else 'Boş'}")
                return False
        
        print("🎉 Tüm veriler başarıyla eklendi!")
        
    except Exception as e:
        print(f"❌ Veri ekleme hatası: {str(e)}")
        return False
    
    # 8. Final kontrol
    try:
        result = client.table("products").select("count", count="exact").execute()
        final_count = result.count
        print(f"✅ Final kontrol: {final_count} toplam kayıt")
        
        # Birkaç örnek kayıt göster
        sample = client.table("products").select("title,ean,fiyat").limit(3).execute()
        if sample.data:
            print("📊 Eklenen verilerden örnekler:")
            for item in sample.data:
                print(f"   • {item.get('title', 'N/A')[:50]}... - {item.get('fiyat', 'N/A')} - EAN: {item.get('ean', 'N/A')}")
        
    except Exception as e:
        print(f"⚠️  Final kontrol hatası: {str(e)}")
    
    print("🎉 Migration tamamlandı!")
    print("🔗 Artık Streamlit uygulamanız Supabase'den veri çekecek!")
    return True

if __name__ == "__main__":
    success = migrate_csv_to_supabase()
    if not success:
        print("\n❌ Migration başarısız. Lütfen hataları kontrol edin.")
        sys.exit(1)
    else:
        print("\n✅ Migration başarılı! Artık uygulamanızı çalıştırabilirsiniz.")
