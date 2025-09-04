#!/usr/bin/env python3
"""
CSV to Supabase Migration Script
Bu script mevcut CSV dosyasını Supabase veritabanına aktarır.
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
    
    # 3. Tablo kontrolü
    try:
        result = client.table("products").select("count", count="exact").execute()
        existing_count = result.count
        print(f"✅ Mevcut kayıt sayısı: {existing_count}")
    except Exception as e:
        print(f"❌ Tablo erişim hatası: {str(e)}")
        print("   Lütfen önce SQL şemasını çalıştırdığınızdan emin olun!")
        return False
    
    # 4. Veri temizleme ve hazırlama
    print("📝 Veri hazırlanıyor...")
    
    # Eksik kolonları tamamla
    required_columns = [
        'title', 'ean', 'iwasku', 'fiyat', 'ham_maliyet_euro', 'ham_maliyet_usd', 'desi',
        'tr_ne_navlun', 'ne_de_navlun', 'express_kargo', 'ddp', 'hava_tr_de_navlun', 'kara_tr_de_navlun', 'reklam'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
    
    # Geriye dönük eşleme: eski kolonlardan yeni kolonlara
    if 'hava_tr_de_navlun' not in df.columns:
        if 'tr_de_navlun' in df.columns:
            df['hava_tr_de_navlun'] = df['tr_de_navlun']
        else:
            # express + ddp varsa bunlardan üret
            try:
                def _clean(v):
                    s = str(v)
                    s = s.replace('€','').replace(',','.')
                    try:
                        return float(s)
                    except:
                        return 0.0
                df['hava_tr_de_navlun'] = [
                    f"€{(_clean(df.get('express_kargo', 0).iloc[i]) + _clean(df.get('ddp', 0).iloc[i])):.2f}"
                    for i in range(len(df))
                ]
            except Exception:
                df['hava_tr_de_navlun'] = ""
    # kara_tr_de_navlun = tr_ne_navlun + ne_de_navlun
    try:
        def _clean2(v):
            s = str(v)
            s = s.replace('€','').replace(',','.')
            try:
                return float(s)
            except:
                return 0.0
        df['kara_tr_de_navlun'] = [
            f"€{(_clean2(df.get('tr_ne_navlun', 0).iloc[i]) + _clean2(df.get('ne_de_navlun', 0).iloc[i])):.2f}"
            for i in range(len(df))
        ]
    except Exception:
        if 'kara_tr_de_navlun' not in df.columns:
            df['kara_tr_de_navlun'] = ""

    # Sadece gerekli kolonları al
    df_clean = df[required_columns].fillna("")
    
    # String formatına çevir (Supabase'deki text alanlarla uyumlu olması için)
    df_clean = df_clean.astype(str)
    
    print(f"✅ Veri hazırlandı: {len(df_clean)} satır, {len(df_clean.columns)} kolon")
    
    # 5. Eğer varsa mevcut verileri temizle (opsiyonel)
    if existing_count > 0:
        choice = input(f"⚠️  Veritabanında {existing_count} kayıt var. Silip yeniden eklemek ister misiniz? (y/n): ")
        if choice.lower() == 'y':
            try:
                client.table("products").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                print("🗑️  Mevcut veriler silindi")
            except Exception as e:
                print(f"⚠️  Veri silme hatası: {str(e)}")
    
    # 6. Bulk insert
    try:
        records = df_clean.to_dict('records')
        print(f"📤 {len(records)} kayıt ekleniyor...")
        
        # Büyük veri setlerini parça parça ekle
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            client.table("products").insert(batch).execute()
            print(f"   ✅ {i+1}-{min(i+len(batch), len(records))} arası eklendi")
        
        print("🎉 Tüm veriler başarıyla eklendi!")
        
    except Exception as e:
        print(f"❌ Veri ekleme hatası: {str(e)}")
        return False
    
    # 7. Kontrol
    try:
        result = client.table("products").select("count", count="exact").execute()
        final_count = result.count
        print(f"✅ Final kontrol: {final_count} toplam kayıt")
    except Exception as e:
        print(f"⚠️  Final kontrol hatası: {str(e)}")
    
    print("🎉 Migration tamamlandı!")
    return True

if __name__ == "__main__":
    success = migrate_csv_to_supabase()
    if not success:
        sys.exit(1)
