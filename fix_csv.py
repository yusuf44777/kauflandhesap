#!/usr/bin/env python3
"""
CSV dosyasını database şemasına uygun hale getirir
"""

import pandas as pd
import numpy as np

def fix_csv():
    print("🔧 CSV dosyası düzeltiliyor...")
    
    # CSV'yi oku
    df = pd.read_csv('kauflandurunler.csv')
    print(f"✅ Orijinal CSV okundu: {len(df)} satır, {len(df.columns)} kolon")
    
    # Euro değerleri temizleyen fonksiyon
    def clean_euro_value(val):
        if pd.isna(val) or val == '':
            return '€0,00'
        val_str = str(val)
        # Euro işaretini kaldır, virgülü nokta yap
        cleaned = val_str.replace('€', '').replace(',', '.')
        try:
            float_val = float(cleaned)
            return f"€{float_val:.2f}".replace('.', ',')  # Tekrar virgülle formatla
        except:
            return '€0,00'
    
    # USD kaldırıldı — yalnızca EUR kullanılacak, ham_maliyet_usd yok sayılır
    
    # 2. kara_tr_de_navlun kolonu (tr_ne_navlun + ne_de_navlun)
    if 'kara_tr_de_navlun' not in df.columns:
        print("   ➕ kara_tr_de_navlun kolonu hesaplanıyor...")
        def calculate_kara_navlun(row):
            try:
                tr_ne = str(row['tr_ne_navlun']).replace('€', '').replace(',', '.')
                ne_de = str(row['ne_de_navlun']).replace('€', '').replace(',', '.')
                
                tr_ne_float = float(tr_ne) if tr_ne else 0.0
                ne_de_float = float(ne_de) if ne_de else 0.0
                
                total = tr_ne_float + ne_de_float
                return f"€{total:.2f}".replace('.', ',')
            except:
                return '€0,00'
        
        df['kara_tr_de_navlun'] = df.apply(calculate_kara_navlun, axis=1)
    
    # 3. hava_tr_de_navlun kolonu (tr_de_navlun'dan al)
    if 'hava_tr_de_navlun' not in df.columns:
        print("   ➕ hava_tr_de_navlun kolonu ekleniyor...")
        if 'tr_de_navlun' in df.columns:
            df['hava_tr_de_navlun'] = df['tr_de_navlun'].apply(clean_euro_value)
        else:
            df['hava_tr_de_navlun'] = '€0,00'
    
    # 4. Eksik değerleri temizle
    print("   🧹 Eksik değerler temizleniyor...")
    
    # Boş değerleri uygun defaultlarla doldur
    fill_values = {
        'title': 'Ürün Adı Yok',
        'ean': '',
        'iwasku': '',
        'fiyat': '€0,00',
        'ham_maliyet_euro': '€0,00',
        'desi': '1',
        'tr_ne_navlun': '€0,00',
        'ne_de_navlun': '€0,00',
        'kara_tr_de_navlun': '€0,00',
        'express_kargo': '€0,00',
        'ddp': '€0,00',
        'hava_tr_de_navlun': '€0,00',
        'reklam': '€5,25'
    }
    
    for col, default_val in fill_values.items():
        if col in df.columns:
            df[col] = df[col].fillna(default_val)
            # Boş string'leri de doldur
            df.loc[df[col] == '', col] = default_val
    
    # 5. Database için gerekli kolonları seç
    required_columns = [
        'title', 'ean', 'iwasku', 'fiyat', 'ham_maliyet_euro', 'desi',
        'tr_ne_navlun', 'ne_de_navlun', 'kara_tr_de_navlun',
        'express_kargo', 'ddp', 'hava_tr_de_navlun',
        'reklam'
    ]
    
    df_cleaned = df[required_columns].copy()
    
    # 6. Düzeltilmiş CSV'yi kaydet
    output_file = 'kauflandurunler_fixed.csv'
    df_cleaned.to_csv(output_file, index=False)
    
    print(f"✅ Düzeltilmiş CSV kaydedildi: {output_file}")
    print(f"   📊 {len(df_cleaned)} satır, {len(df_cleaned.columns)} kolon")
    
    # 7. Özet bilgi
    print("\n📋 Düzeltilmiş CSV özeti:")
    print("Kolonlar:", ", ".join(df_cleaned.columns))
    
    print("\nİlk 3 satır:")
    print(df_cleaned.head(3).to_string())
    
    # Eksik değer kontrolü
    print("\n🔍 Eksik değer kontrolü:")
    for col in df_cleaned.columns:
        missing = df_cleaned[col].isnull().sum() + (df_cleaned[col] == '').sum()
        if missing > 0:
            print(f"   ⚠️  {col}: {missing} eksik değer")
    
    print("\n🎉 CSV düzeltme tamamlandı!")
    return output_file

if __name__ == "__main__":
    fix_csv()
