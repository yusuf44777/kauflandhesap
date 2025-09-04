#!/usr/bin/env python3
"""
Hızlı Supabase bağlantı ve data test scripti
"""

from supabase import create_client
import pandas as pd

def test_supabase_connection():
    print("🔍 Supabase bağlantısı test ediliyor...")
    
    # Bağlantı bilgileri
    url = 'https://xtygcxtrjdqhrqmrnlpc.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh0eWdjeHRyamRxaHJxbXJubHBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NjcwODIsImV4cCI6MjA3MjU0MzA4Mn0.z4Dlkn2YlAByk4ICQHNxBqZjKdLkwu4FuMAoPA07qo8'
    
    try:
        client = create_client(url, key)
        print("✅ Supabase client oluşturuldu")
        
        # Tablo varlık kontrolü
        result = client.table('products').select('count', count='exact').execute()
        count = result.count
        print(f"✅ Products tablosu erişilebilir, kayıt sayısı: {count}")
        
        if count > 0:
            # Örnek veri çek
            sample = client.table('products').select('title,ean,fiyat,desi').limit(3).execute()
            print("📊 İlk 3 kayıt:")
            for item in sample.data:
                print(f"  • {item.get('title', 'N/A')[:50]}... - {item.get('fiyat', 'N/A')} - {item.get('desi', 'N/A')} desi")
        else:
            print("⚠️  Tablo boş - migration çalıştırmanız gerekebilir")
            
        return True
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        
        if "products" in str(e).lower() and "schema" in str(e).lower():
            print("💡 Çözüm: recreate_table.sql'i Supabase Dashboard'da çalıştırın")
        return False

def test_csv_data():
    print("\n🔍 Düzeltilmiş CSV test ediliyor...")
    
    try:
        df = pd.read_csv('kauflandurunler.csv')
        print(f"✅ CSV okundu: {len(df)} satır, {len(df.columns)} kolon")
        
        required_columns = [
            'title', 'ean', 'iwasku', 'fiyat', 'ham_maliyet_euro', 'desi',
            'tr_ne_navlun', 'ne_de_navlun', 'kara_tr_de_navlun',
            'express_kargo', 'ddp', 'hava_tr_de_navlun', 'reklam'
        ]
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            print(f"❌ Eksik kolonlar: {missing}")
            return False
        else:
            print("✅ Tüm gerekli kolonlar mevcut")
            
        # Veri kalitesi kontrolü
        empty_count = 0
        for col in required_columns:
            empty_in_col = df[col].isnull().sum() + (df[col] == '').sum()
            if empty_in_col > 0:
                empty_count += 1
                
        print(f"📊 Veri kalitesi: {len(required_columns) - empty_count}/{len(required_columns)} kolon tamamen dolu")
        return True
        
    except Exception as e:
        print(f"❌ CSV okuma hatası: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Kaufland Database Integration Test\n")
    
    csv_ok = test_csv_data()
    db_ok = test_supabase_connection()
    
    print("\n" + "="*50)
    print("📋 TEST SONUÇLARI:")
    print(f"📄 CSV Durumu: {'✅ HAZIR' if csv_ok else '❌ SORUNLU'}")
    print(f"🗄️  Database Durumu: {'✅ HAZIR' if db_ok else '❌ SORUNLU'}")
    
    if csv_ok and db_ok:
        print("🎉 Sistem tamamen hazır! Streamlit uygulamasını başlatabilirsiniz.")
    elif csv_ok and not db_ok:
        print("⚠️  CSV hazır ama database tablosu sorunlu. Migration çalıştırın.")
    else:
        print("⚠️  Sorun var, lütfen hataları giderin.")
