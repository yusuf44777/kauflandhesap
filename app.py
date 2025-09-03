import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io

# Sayfa yapılandırması
st.set_page_config(
    page_title="Kaufland Fiyat Hesaplama",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# JSON veritabanı dosya yolu
JSON_FILE = "kaufland_products.json"

# CSV dosya yolu
CSV_FILE = "kauflandurunler.csv"

# Varsayılan parametreler
DEFAULT_PARAMS = {
    "reklam_maliyeti": 5.25,
    "pazaryeri_kesintisi": 15.0,
    "vergi_yuzdesi": 20.0
}

@st.cache_data(show_spinner=False)
def load_json_data():
    """JSON dosyasından verileri yükler (cache'li)"""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"products": [], "last_updated": ""}
    return {"products": [], "last_updated": ""}

def save_json_data(data):
    """Verileri JSON dosyasına kaydeder"""
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Cache'i temizle (bir sonraki okumada güncel veri yüklensin)
    try:
        load_json_data.clear()
    except Exception:
        pass

@st.cache_data(show_spinner=False)
def load_csv_data():
    """CSV dosyasından verileri yükler (cache'li)"""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def clean_euro_value(value):
    """Euro değerini temizler ve float'a çevirir"""
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        # €, ", " karakterlerini kaldır ve virgülü noktaya çevir
        clean_val = value.replace('€', '').replace('"', '').replace(',', '.').strip()
        try:
            return float(clean_val)
        except:
            return 0.0
    return float(value) if value else 0.0

def calculate_total_cost(row, params):
    """İki farklı rota ile maliyet hesaplar: TR→NL→DE ve TR→DE"""
    # Ham maliyet
    ham_maliyet = clean_euro_value(row.get('ham_maliyet_euro', 0))
    # Satış fiyatı (pazar yeri ve vergi bu fiyata göre hesaplanacak)
    satis_fiyati = clean_euro_value(row.get('fiyat', 0))
    
    # Maliyet bileşenleri
    unit_in = clean_euro_value(row.get('unit_in', 0))
    box_in = clean_euro_value(row.get('box_in', 0))
    pick_pack = clean_euro_value(row.get('pick_pack', 0))
    storage = clean_euro_value(row.get('storage', 0))
    fedex = clean_euro_value(row.get('fedex', 0))
    ne_de_navlun = clean_euro_value(row.get('ne_de_navlun', 0))  # NL→DE navlun
    tr_ne_navlun_field = clean_euro_value(row.get('tr_ne_navlun', 0))  # TR→NL toplam navlun (varsa)
    express_kargo = clean_euro_value(row.get('express_kargo', 0))
    ddp = clean_euro_value(row.get('ddp', 0))
    tr_de_navlun_field = clean_euro_value(row.get('tr_de_navlun', 0))  # TR→DE toplam navlun (varsa)
    
    # Reklam maliyeti
    reklam_maliyeti = params['reklam_maliyeti']
    
    # ROTA 1: TR → NL → DE
    # TR→NL segmenti: detay bileşenler varsa topla; yoksa tek alanı kullan
    tr_ne_navlun_hesaplanan = unit_in + box_in + pick_pack + storage + fedex
    tr_ne_navlun_final = tr_ne_navlun_hesaplanan if tr_ne_navlun_hesaplanan > 0 else tr_ne_navlun_field
    tr_nl_de_temel_maliyet = ham_maliyet + tr_ne_navlun_final + ne_de_navlun
    tr_nl_de_reklam_dahil = tr_nl_de_temel_maliyet + reklam_maliyeti
    # Vergi ve pazar yeri kesintisi satış fiyatı üzerinden hesaplanır
    tr_nl_de_vergi = (satis_fiyati * params['vergi_yuzdesi']) / 100
    tr_nl_de_pazaryeri_kesinti = (satis_fiyati * params['pazaryeri_kesintisi']) / 100
    tr_nl_de_son_maliyet = tr_nl_de_reklam_dahil + tr_nl_de_vergi + tr_nl_de_pazaryeri_kesinti
    
    # ROTA 2: TR → DE (Direkt)
    # TR→DE segmenti: detay bileşenler varsa topla; yoksa tek alanı kullan
    tr_de_navlun_hesaplanan = express_kargo + ddp
    tr_de_navlun_final = tr_de_navlun_hesaplanan if tr_de_navlun_hesaplanan > 0 else tr_de_navlun_field
    tr_de_temel_maliyet = ham_maliyet + tr_de_navlun_final
    tr_de_reklam_dahil = tr_de_temel_maliyet + reklam_maliyeti
    # Vergi ve pazar yeri kesintisi satış fiyatı üzerinden hesaplanır
    tr_de_vergi = (satis_fiyati * params['vergi_yuzdesi']) / 100
    tr_de_pazaryeri_kesinti = (satis_fiyati * params['pazaryeri_kesintisi']) / 100
    tr_de_son_maliyet = tr_de_reklam_dahil + tr_de_vergi + tr_de_pazaryeri_kesinti
    
    # En uygun rotayı seç
    optimal_route = "TR→NL→DE" if tr_nl_de_son_maliyet <= tr_de_son_maliyet else "TR→DE"
    optimal_cost = min(tr_nl_de_son_maliyet, tr_de_son_maliyet)
    
    return {
        # TR→NL→DE Rotası
        'tr_nl_de_temel_maliyet': tr_nl_de_temel_maliyet,
        'tr_nl_de_navlun': tr_ne_navlun_final + ne_de_navlun,
        'tr_nl_de_reklam_dahil': tr_nl_de_reklam_dahil,
        'tr_nl_de_vergi': tr_nl_de_vergi,
        'tr_nl_de_pazaryeri_kesinti': tr_nl_de_pazaryeri_kesinti,
        'tr_nl_de_son_maliyet': tr_nl_de_son_maliyet,
        
        # TR→DE Direkt Rota
        'tr_de_temel_maliyet': tr_de_temel_maliyet,
        'tr_de_navlun': tr_de_navlun_final,
        'tr_de_reklam_dahil': tr_de_reklam_dahil,
        'tr_de_vergi': tr_de_vergi,
        'tr_de_pazaryeri_kesinti': tr_de_pazaryeri_kesinti,
        'tr_de_son_maliyet': tr_de_son_maliyet,
        
        # Optimal seçim
        'optimal_route': optimal_route,
        'optimal_cost': optimal_cost,
        'cost_difference': abs(tr_nl_de_son_maliyet - tr_de_son_maliyet),
        
        # Eski format uyumluluğu için
        'reklam_maliyeti': reklam_maliyeti,
        'son_maliyet': optimal_cost
    }

def main():
    st.title("🛒 Kaufland Fiyat Hesaplama Modülü")
    st.markdown("---")
    
    # Sidebar - Parametreler
    with st.sidebar:
        st.header("📊 Hesaplama Parametreleri")
        
        reklam_maliyeti = st.number_input(
            "Reklam Maliyeti (€)", 
            value=DEFAULT_PARAMS["reklam_maliyeti"],
            min_value=0.0,
            step=0.01,
            help="Ürün başına sabit reklam tutarı"
        )
        
        pazaryeri_kesintisi = st.number_input(
            "Pazaryeri Kesintisi (%)", 
            value=DEFAULT_PARAMS["pazaryeri_kesintisi"],
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            help="Platform komisyon oranı"
        )
        
        vergi_yuzdesi = st.number_input(
            "Vergi Yüzdesi (%)", 
            value=DEFAULT_PARAMS["vergi_yuzdesi"],
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            help="Vergi oranı"
        )
        
        params = {
            "reklam_maliyeti": reklam_maliyeti,
            "pazaryeri_kesintisi": pazaryeri_kesintisi,
            "vergi_yuzdesi": vergi_yuzdesi
        }
        
        st.markdown("---")
        st.markdown("**💡 Bilgi:**")
        st.markdown("Bu parametreler tüm hesaplamalarda kullanılır.")
        
        st.markdown("---")
        st.markdown("**🔗 Faydalı Linkler:**")
        st.markdown("📝 [Title Description Generator](https://kauflandiwa.streamlit.app/)")
        st.markdown("*Kaufland için başlık ve açıklama oluşturun*")
    
    # Ana tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Ürün Listesi", 
        "➕ Yeni Ürün Ekle", 
        "📊 Fiyat Hesaplama", 
        "📥 Export/Import",
        "📈 Analiz"
    ])
    
    with tab1:
        st.header("Mevcut Ürünler")
        
        # CSV'den verileri yükle
        df = load_csv_data()
        
        if not df.empty:
            # Fiyat hesaplamalarını ekle
            with st.spinner('Hesaplamalar yapılıyor...'):
                df['Satış Fiyatı'] = df['fiyat'].apply(clean_euro_value)
                hesaplama_sonuclari = []
                for index, row in df.iterrows():
                    hesaplama = calculate_total_cost(row, params)
                    hesaplama_sonuclari.append(hesaplama)
            
            # Hesaplama sonuçlarını DataFrame'e ekle
            df['TR→NL→DE Maliyet'] = [h['tr_nl_de_son_maliyet'] for h in hesaplama_sonuclari]
            df['TR→DE Maliyet'] = [h['tr_de_son_maliyet'] for h in hesaplama_sonuclari]
            df['Optimal Rota'] = [h['optimal_route'] for h in hesaplama_sonuclari]
            df['Son Maliyet'] = [h['optimal_cost'] for h in hesaplama_sonuclari]
            df['Kar Marjı'] = df['Satış Fiyatı'] - df['Son Maliyet']
            df['Kar Marjı %'] = ((df['Satış Fiyatı'] - df['Son Maliyet']) / df['Satış Fiyatı'] * 100).round(2)
            
            # Gösterim için sütunları seç
            display_columns = [
                'title', 'ean', 'Satış Fiyatı', 'TR→NL→DE Maliyet', 
                'TR→DE Maliyet', 'Optimal Rota', 'Son Maliyet', 'Kar Marjı', 'Kar Marjı %'
            ]
            
            # Filtreleme
            with st.expander("🔍 Filtreler", expanded=False):
                fcol1, fcol2 = st.columns(2)
                with fcol1:
                    search_term = st.text_input("Ürün adında ara:", placeholder="Örn: Dünya Haritası")
                with fcol2:
                    kar_marji_filtre = st.selectbox(
                        "Kâr durum filtresi:",
                        ["Tümü", "Pozitif", "Negatif", "0'a yakın (±5%)"]
                    )
                rcol1, rcol2, rcol3 = st.columns(3)
                with rcol1:
                    min_price = float(df['Satış Fiyatı'].min()) if len(df) else 0.0
                    max_price = float(df['Satış Fiyatı'].max()) if len(df) else 0.0
                    price_range = st.slider(
                        "Satış fiyatı aralığı (€)",
                        min_value=0.0,
                        max_value=max(0.0, round(max_price + 1, 2)),
                        value=(round(min_price, 2), round(max_price, 2)) if max_price >= min_price else (0.0, 0.0)
                    )
                with rcol2:
                    pct_min = float(df['Kar Marjı %'].min()) if len(df) else 0.0
                    pct_max = float(df['Kar Marjı %'].max()) if len(df) else 0.0
                    pct_range = st.slider(
                        "Kâr % aralığı",
                        min_value=float(min(-50.0, pct_min)) if len(df) else -50.0,
                        max_value=float(max(50.0, pct_max)) if len(df) else 50.0,
                        value=(float(min(0.0, pct_min)), float(max(0.0, pct_max))) if len(df) else (-10.0, 30.0)
                    )
                with rcol3:
                    rota_secimi = st.multiselect(
                        "Rota",
                        options=["TR→NL→DE", "TR→DE"],
                        default=["TR→NL→DE", "TR→DE"]
                    )

            # Filtrelemeyi uygula
            filtered_df = df.copy()
            if search_term:
                filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False, na=False)]
            if kar_marji_filtre == "Pozitif":
                filtered_df = filtered_df[filtered_df['Kar Marjı'] > 0]
            elif kar_marji_filtre == "Negatif":
                filtered_df = filtered_df[filtered_df['Kar Marjı'] < 0]
            elif kar_marji_filtre == "0'a yakın (±5%)":
                filtered_df = filtered_df[abs(filtered_df['Kar Marjı %']) <= 5]
            # Aralık filtreleri
            if len(filtered_df) > 0:
                filtered_df = filtered_df[
                    (filtered_df['Satış Fiyatı'] >= price_range[0]) &
                    (filtered_df['Satış Fiyatı'] <= price_range[1]) &
                    (filtered_df['Kar Marjı %'] >= pct_range[0]) &
                    (filtered_df['Kar Marjı %'] <= pct_range[1]) &
                    (filtered_df['Optimal Rota'].isin(rota_secimi))
                ]
            
            # Sonuçları göster
            st.subheader(f"📊 Toplam {len(filtered_df)} ürün")
            
            if not filtered_df.empty:
                # Özet istatistikler
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Ortalama Satış Fiyatı", f"€{filtered_df['Satış Fiyatı'].mean():.2f}")
                    
                with col2:
                    st.metric("Ortalama Kar Marjı", f"€{filtered_df['Kar Marjı'].mean():.2f}")
                    
                with col3:
                    st.metric("Ortalama Kar %", f"{filtered_df['Kar Marjı %'].mean():.1f}%")
                    
                with col4:
                    pozitif_kar = len(filtered_df[filtered_df['Kar Marjı'] > 0])
                    st.metric("Karlı Ürün Sayısı", pozitif_kar)
                
                # Tabloyu göster (renklendirme)
                display_df = filtered_df[display_columns].round(2)
                # Yumuşak renklerle kâr yüzdesi kategorilerine göre stiller
                def _pct_cell_style(pct):
                    try:
                        if pct < 0:
                            return 'background-color:#ffe6e6;color:#a10000;'
                        elif pct < 10:
                            return 'background-color:#fff3e0;color:#8a6d3b;'
                        elif pct < 20:
                            return 'background-color:#fffde7;color:#8a6d3b;'
                        elif pct < 30:
                            return 'background-color:#e8f5e9;color:#1b5e20;'
                        elif pct <= 40:
                            return 'background-color:#dcedc8;color:#33691e;'
                        else:
                            return 'background-color:#c8e6c9;color:#1b5e20;'
                    except Exception:
                        return ''

                def _highlight_row(row):
                    cols = list(display_df.columns)
                    styles = [''] * len(cols)
                    try:
                        idx_profit = cols.index('Kar Marjı')
                        idx_profit_pct = cols.index('Kar Marjı %')
                        if row['Kar Marjı'] < 0:
                            styles[idx_profit] = 'background-color:#ffe6e6;color:#a10000;'
                        styles[idx_profit_pct] = _pct_cell_style(row['Kar Marjı %'])
                    except Exception:
                        pass
                    return styles
                styler = (
                    display_df.style
                    .format({
                        'Satış Fiyatı': '€{:.2f}',
                        'TR→NL→DE Maliyet': '€{:.2f}',
                        'TR→DE Maliyet': '€{:.2f}',
                        'Son Maliyet': '€{:.2f}',
                        'Kar Marjı': '€{:.2f}',
                        'Kar Marjı %': '{:.1f}%'
                    })
                    .apply(_highlight_row, axis=1)
                )
                st.dataframe(styler, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("✏️ Gelişmiş Düzenleme")
                if st.toggle("Tabloda düzenlemeyi etkinleştir", value=False, help="Fiyat ve maliyet alanlarını satır içi düzenleyin"):
                    editable_cols = [
                        'fiyat', 'ham_maliyet_euro', 'reklam',
                        'unit_in', 'box_in', 'pick_pack', 'storage', 'fedex',
                        'ne_de_navlun', 'express_kargo', 'ddp'
                    ]
                    present_edit_cols = [c for c in editable_cols if c in filtered_df.columns]
                    edit_base_cols = ['title', 'ean'] + present_edit_cols
                    edit_df = filtered_df[edit_base_cols].copy()
                    for c in present_edit_cols:
                        edit_df[c] = edit_df[c].apply(clean_euro_value)
                    edit_df['ean'] = edit_df['ean'].astype(str)
                    edited_df = st.data_editor(
                        edit_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'title': st.column_config.TextColumn('Ürün'),
                            'ean': st.column_config.TextColumn('EAN'),
                        }
                    )
                    c1, c2 = st.columns([1,1])
                    with c1:
                        if st.button("Değişiklikleri Kaydet", type="primary"):
                            with st.spinner('Kaydediliyor...'):
                                existing_df = load_csv_data()
                                if not existing_df.empty:
                                    existing_df['ean'] = existing_df['ean'].astype(str)
                                    updates = edited_df.dropna(subset=['ean']).set_index('ean')
                                    for ean_key, row_vals in updates.iterrows():
                                        idx = existing_df[existing_df['ean'].astype(str) == str(ean_key)].index
                                        if len(idx) > 0:
                                            for col in present_edit_cols:
                                                existing_df.loc[idx, col] = row_vals[col]
                                    existing_df.to_csv(CSV_FILE, index=False)
                                    try:
                                        load_csv_data.clear()
                                    except Exception:
                                        pass
                                    st.success("Değişiklikler kaydedildi.")
                                    st.rerun()
                                else:
                                    st.warning("Kaydedilecek veri bulunamadı.")
                    with c2:
                        del_options = edited_df['ean'].dropna().astype(str).unique().tolist()
                        del_select = st.multiselect("Silinecek ürünler (EAN)", options=del_options)
                        if st.button("Seçili Ürünleri Sil", type="secondary") and del_select:
                            with st.spinner('Siliniyor...'):
                                base_df = load_csv_data()
                                if not base_df.empty and 'ean' in base_df.columns:
                                    base_df['ean'] = base_df['ean'].astype(str)
                                    base_df = base_df[~base_df['ean'].isin([str(x) for x in del_select])]
                                    base_df.to_csv(CSV_FILE, index=False)
                                    try:
                                        load_csv_data.clear()
                                    except Exception:
                                        pass
                                    st.success("Seçili ürünler silindi.")
                                    st.rerun()
            else:
                st.warning("Filtrelere uygun ürün bulunamadı.")
        else:
            st.info("Henüz ürün bulunmuyor. 'Yeni Ürün Ekle' sekmesinden ürün ekleyebilirsiniz.")
    
    with tab2:
        st.header("Yeni Ürün Ekle")
        
        with st.form("add_product"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Ürün Adı*")
                ean = st.text_input("EAN Kodu")
                iwasku = st.text_input("IWASKU Kodu")
            
            with col2:
                fiyat = st.number_input("Satış Fiyatı (€)*", min_value=0.0, step=0.01)
                ham_maliyet = st.number_input("Ham Maliyet (€)*", min_value=0.0, step=0.01)
                desi = st.number_input("Desi", min_value=0.0, step=0.1)
            
            # Navlun maliyetleri
            st.subheader("🚚 Navlun Maliyetleri")
            col3, col4 = st.columns(2)
            with col3:
                tr_ne_navlun = st.number_input("TR-NE Navlun (€)", min_value=0.0, step=0.01)
                ne_de_navlun = st.number_input("NE-DE Navlun (€)", min_value=0.0, step=0.01)
            
            with col4:
                tr_de_navlun = st.number_input("TR-DE Navlun (€)", min_value=0.0, step=0.01)
            
            # Otomatik olarak 0 değeri atanacak alanlar
            unit_in = 0.0
            box_in = 0.0
            pick_pack = 0.0
            storage = 0.0
            fedex = 0.0
            express_kargo = 0.0
            ddp = 0.0
            
            submitted = st.form_submit_button("Ürün Ekle", type="primary")
            
            if submitted:
                if title and fiyat > 0 and ham_maliyet >= 0:
                    # Yeni ürün verisi
                    new_product = {
                        'title': title,
                        'ean': ean,
                        'iwasku': iwasku,
                        'fiyat': f"€{fiyat:.2f}",
                        'ham_maliyet_euro': ham_maliyet,
                        'desi': desi,
                        'unit_in': f"€{unit_in:.2f}",
                        'box_in': f"€{box_in:.2f}",
                        'pick_pack': f"€{pick_pack:.2f}",
                        'storage': f"€{storage:.2f}",
                        'fedex': f"€{fedex:.2f}",
                        'tr_ne_navlun': f"€{tr_ne_navlun:.2f}",
                        'ne_de_navlun': f"€{ne_de_navlun:.2f}",
                        'express_kargo': f"€{express_kargo:.2f}",
                        'ddp': f"€{ddp:.2f}",
                        'tr_de_navlun': f"€{tr_de_navlun:.2f}",
                        'reklam': f"€{params['reklam_maliyeti']:.2f}"
                    }
                    
                    # CSV'ye ekle
                    df = load_csv_data()
                    new_df = pd.DataFrame([new_product])
                    
                    if df.empty:
                        updated_df = new_df
                    else:
                        updated_df = pd.concat([df, new_df], ignore_index=True)
                    
                    updated_df.to_csv(CSV_FILE, index=False)
                    try:
                        load_csv_data.clear()
                    except Exception:
                        pass
                    
                    # JSON'a da ekle
                    json_data = load_json_data()
                    json_data["products"].append(new_product)
                    save_json_data(json_data)
                    
                    st.success(f"✅ '{title}' ürünü başarıyla eklendi!")
                    st.rerun()
                else:
                    st.error("❌ Lütfen zorunlu alanları doldurun (Ürün Adı, Satış Fiyatı)")
    
    with tab3:
        st.header("Detaylı Fiyat Hesaplama")
        
        df = load_csv_data()
        
        if not df.empty:
            # Ürün arama ve seçimi
            st.subheader("🔎 Ürün Arama")
            search_query = st.text_input(
                "Ürün adı veya EAN ile ara:",
                placeholder="Örn: Harita, 8684...",
                help="Başlığa veya EAN koduna göre filtreleyin"
            )
            filtered_df_sel = df.copy()
            if search_query:
                mask_title = filtered_df_sel['title'].str.contains(search_query, case=False, na=False)
                mask_ean = (
                    filtered_df_sel['ean'].astype(str).str.contains(search_query, case=False, na=False)
                    if 'ean' in filtered_df_sel.columns else pd.Series([False]*len(filtered_df_sel), index=filtered_df_sel.index)
                )
                filtered_df_sel = filtered_df_sel[mask_title | mask_ean]

            product_names = filtered_df_sel['title'].tolist()
            if len(product_names) == 0:
                st.info("Aramaya uygun ürün bulunamadı. Aramayı temizleyin veya farklı bir ifade deneyin.")
            else:
                selected_product = st.selectbox("Hesaplama yapılacak ürünü seçin:", product_names)
                
                if selected_product:
                    # Seçilen ürünün verileri
                    selected_row = df[df['title'] == selected_product].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📦 Ürün Bilgileri")
                    st.write(f"**Ürün Adı:** {selected_row['title']}")
                    st.write(f"**EAN:** {selected_row['ean']}")
                    st.write(f"**Satış Fiyatı:** €{clean_euro_value(selected_row['fiyat']):.2f}")
                    st.write(f"**Ham Maliyet:** €{clean_euro_value(selected_row['ham_maliyet_euro']):.2f}")
                    st.write(f"**Desi:** {selected_row['desi']}")
                
                with col2:
                    st.subheader("⚙️ Hesaplama Parametreleri")
                    st.write(f"**Reklam Maliyeti:** €{params['reklam_maliyeti']:.2f}")
                    st.write(f"**Pazaryeri Kesintisi:** {params['pazaryeri_kesintisi']}%")
                    st.write(f"**Vergi Yüzdesi:** {params['vergi_yuzdesi']}%")
                
                # Detaylı hesaplama
                st.subheader("💰 Detaylı Maliyet Analizi")
                
                with st.spinner('Hesaplanıyor...'):
                    hesaplama = calculate_total_cost(selected_row, params)
                satis_fiyati = clean_euro_value(selected_row['fiyat'])
                
                # İki rotayı karşılaştırmalı göster
                st.subheader("🛣️ Rota Karşılaştırması")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### TR → NL → DE")
                    st.metric("Temel Maliyet", f"€{hesaplama['tr_nl_de_temel_maliyet']:.2f}")
                    st.metric("Reklam Dahil", f"€{hesaplama['tr_nl_de_reklam_dahil']:.2f}")
                    st.metric(f"Vergi ({params['vergi_yuzdesi']}%)", f"€{hesaplama['tr_nl_de_vergi']:.2f}")
                    st.metric(f"Pazaryeri ({params['pazaryeri_kesintisi']}%)", f"€{hesaplama['tr_nl_de_pazaryeri_kesinti']:.2f}")
                    st.metric("**SON MALİYET**", f"€{hesaplama['tr_nl_de_son_maliyet']:.2f}")
                
                with col2:
                    st.markdown("#### TR → DE (Direkt)")
                    st.metric("Temel Maliyet", f"€{hesaplama['tr_de_temel_maliyet']:.2f}")
                    st.metric("Reklam Dahil", f"€{hesaplama['tr_de_reklam_dahil']:.2f}")
                    st.metric(f"Vergi ({params['vergi_yuzdesi']}%)", f"€{hesaplama['tr_de_vergi']:.2f}")
                    st.metric(f"Pazaryeri ({params['pazaryeri_kesintisi']}%)", f"€{hesaplama['tr_de_pazaryeri_kesinti']:.2f}")
                    st.metric("**SON MALİYET**", f"€{hesaplama['tr_de_son_maliyet']:.2f}")
                
                with col3:
                    st.markdown("#### 🏆 Optimal Seçim")
                    st.metric("En İyi Rota", hesaplama['optimal_route'])
                    st.metric("Optimal Maliyet", f"€{hesaplama['optimal_cost']:.2f}")
                    st.metric("Tasarruf", f"€{hesaplama['cost_difference']:.2f}")
                    
                    if hesaplama['optimal_route'] == "TR→NL→DE":
                        st.success("✅ Hollanda üzerinden daha ekonomik")
                    else:
                        st.info("✅ Direkt rota daha ekonomik")
                
                # Maliyet bileşenleri tablosu
                st.subheader("📋 Maliyet Bileşenleri Detayı")
                
                # TR-NL-DE Route Breakdown
                tr_nl_breakdown = {
                    'Bileşen': ['Ham Maliyet', 'Unit In', 'Box In', 'Pick Pack', 'Storage', 'Fedex', 'NE-DE Navlun', 'Reklam', f'Vergi ({params["vergi_yuzdesi"]}%)', f'Pazaryeri ({params["pazaryeri_kesintisi"]}%)'],
                    'TR→NL→DE (€)': [
                        clean_euro_value(selected_row['ham_maliyet_euro']),
                        clean_euro_value(selected_row['unit_in']),
                        clean_euro_value(selected_row['box_in']),
                        clean_euro_value(selected_row['pick_pack']),
                        clean_euro_value(selected_row['storage']),
                        clean_euro_value(selected_row['fedex']),
                        clean_euro_value(selected_row['ne_de_navlun']),
                        hesaplama['reklam_maliyeti'],
                        hesaplama['tr_nl_de_vergi'],
                        hesaplama['tr_nl_de_pazaryeri_kesinti']
                    ],
                    'TR→DE (€)': [
                        clean_euro_value(selected_row['ham_maliyet_euro']),
                        0, 0, 0, 0, 0,  # TR-DE rotasında bu maliyetler yok
                        hesaplama['tr_de_navlun'],
                        hesaplama['reklam_maliyeti'],
                        hesaplama['tr_de_vergi'],
                        hesaplama['tr_de_pazaryeri_kesinti']
                    ]
                }
                
                breakdown_df = pd.DataFrame(tr_nl_breakdown)
                st.dataframe(breakdown_df, hide_index=True)
                
                # Özet
                st.subheader("📊 Hesaplama Özeti")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Satış Fiyatı", f"€{satis_fiyati:.2f}")
                    
                with col2:
                    st.metric("Toplam Maliyet", f"€{hesaplama['son_maliyet']:.2f}")
                    
                with col3:
                    kar_marji = satis_fiyati - hesaplama['son_maliyet']
                    st.metric("Kar Marjı", f"€{kar_marji:.2f}")
                    
                with col4:
                    kar_yuzdesi = (kar_marji / satis_fiyati * 100) if satis_fiyati > 0 else 0
                    st.metric("Kar Marjı %", f"{kar_yuzdesi:.1f}%")
                
                # Kategori rozeti (yumuşak renkler)
                kategori = ""
                bg, fg = "#ffffff", "#333333"
                if kar_marji < 0:
                    kategori, bg, fg = "Zararlı", "#ffe6e6", "#a10000"
                elif kar_yuzdesi < 10:
                    kategori, bg, fg = "Çok Düşük", "#fff3e0", "#8a6d3b"
                elif kar_yuzdesi < 20:
                    kategori, bg, fg = "Düşük", "#fffde7", "#8a6d3b"
                elif kar_yuzdesi < 30:
                    kategori, bg, fg = "Orta", "#e8f5e9", "#1b5e20"
                elif kar_yuzdesi <= 40:
                    kategori, bg, fg = "Yüksek", "#dcedc8", "#33691e"
                else:
                    kategori, bg, fg = "Çok Yüksek", "#c8e6c9", "#1b5e20"
                st.markdown(
                    f"<div style='margin-top:-8px;'><span style='background:{bg};color:{fg};padding:3px 10px;border-radius:12px;font-size:0.9em;'>Kategori: {kategori}</span></div>",
                    unsafe_allow_html=True
                )
                
                # Uyarılar
                if kar_marji < 0:
                    st.error("⚠️ Bu ürün zarar ediyor!")
                elif kar_yuzdesi < 20:
                    st.warning("⚠️ Kar marjı düşük (<%20)")
                else:
                    st.success("✅ Kar marjı sağlıklı seviyede")

                # Hızlı aksiyonlar: hedef kâra göre fiyat öner ve uygula
                st.markdown("---")
                st.subheader("⚡ Hızlı Aksiyonlar")
                ac1, ac2 = st.columns([2, 1])
                with ac1:
                    hedef_kar_pct = st.slider(
                        "Hedef Kâr Marjı %",
                        min_value=0,
                        max_value=80,
                        value=25,
                        step=1,
                        help="Satış fiyatı bazında hedef kâr yüzdesi"
                    )
                    son_maliyet = hesaplama['son_maliyet']
                    oran = 1 - (hedef_kar_pct / 100.0)
                    onerilen_fiyat = son_maliyet / oran if oran > 0 else None
                    if onerilen_fiyat is not None:
                        st.metric("Önerilen Satış Fiyatı", f"€{onerilen_fiyat:.2f}")
                with ac2:
                    if (onerilen_fiyat is not None) and st.button("Fiyatı CSV’ye uygula", type="primary"):
                        with st.spinner('Güncelleniyor...'):
                            df_base = load_csv_data()
                            if not df_base.empty:
                                updated = False
                                # Öncelik EAN ile güncelle
                                if 'ean' in df_base.columns and pd.notna(selected_row.get('ean', None)) and str(selected_row['ean']).strip() != "":
                                    df_base['ean'] = df_base['ean'].astype(str)
                                    mask = df_base['ean'] == str(selected_row['ean'])
                                    if mask.any():
                                        df_base.loc[mask, 'fiyat'] = f"€{onerilen_fiyat:.2f}"
                                        updated = True
                                # EAN yoksa title ile dener
                                if not updated and 'title' in df_base.columns:
                                    mask = df_base['title'] == selected_row['title']
                                    if mask.any():
                                        df_base.loc[mask, 'fiyat'] = f"€{onerilen_fiyat:.2f}"
                                        updated = True
                                if updated:
                                    df_base.to_csv(CSV_FILE, index=False)
                                    try:
                                        load_csv_data.clear()
                                    except Exception:
                                        pass
                                    st.success("Yeni fiyat kaydedildi.")
                                    st.rerun()
                                else:
                                    st.warning("Güncellenecek satır bulunamadı.")

                # ROI bazlı fiyat belirleme
                st.markdown("---")
                st.subheader("📈 ROI Bazlı Fiyatlama")
                rcol1, rcol2, rcol3 = st.columns([2,1,1])
                with rcol1:
                    roi_ratio = st.slider(
                        "Hedef ROI",
                        min_value=0.0,
                        max_value=3.0,
                        value=0.5,
                        step=0.05,
                        help="ROI = Kâr / (Navlun + Ham Maliyet). Örn: 0.5 = %50 ROI"
                    )
                with rcol2:
                    roi_route_choice = st.selectbox(
                        "Rota (ROI için)",
                        options=["Optimal", "TR→NL→DE", "TR→DE"],
                        help="ROI hesaplamasında esas alınacak rota"
                    )
                with rcol3:
                    st.empty()

                # ROI hesaplarına temel değerler
                ham_maliyet_val = clean_euro_value(selected_row.get('ham_maliyet_euro', 0))
                trnl_navlun = hesaplama.get('tr_nl_de_navlun', 0.0)
                trde_navlun = hesaplama.get('tr_de_navlun', 0.0)

                if roi_route_choice == "TR→NL→DE":
                    roi_navlun = trnl_navlun
                    roi_son_maliyet = hesaplama['tr_nl_de_son_maliyet']
                elif roi_route_choice == "TR→DE":
                    roi_navlun = trde_navlun
                    roi_son_maliyet = hesaplama['tr_de_son_maliyet']
                else:
                    if hesaplama['optimal_route'] == "TR→NL→DE":
                        roi_navlun = trnl_navlun
                        roi_son_maliyet = hesaplama['tr_nl_de_son_maliyet']
                    else:
                        roi_navlun = trde_navlun
                        roi_son_maliyet = hesaplama['tr_de_son_maliyet']

                roi_denom = ham_maliyet_val + roi_navlun
                if roi_denom > 0:
                    onerilen_fiyat_roi = roi_son_maliyet + (roi_ratio) * roi_denom
                    mevcut_roi = ((satis_fiyati - roi_son_maliyet) / roi_denom)
                else:
                    onerilen_fiyat_roi = None
                    mevcut_roi = None

                m1, m2 = st.columns(2)
                with m1:
                    if onerilen_fiyat_roi is not None:
                        st.metric("Önerilen Satış Fiyatı (ROI)", f"€{onerilen_fiyat_roi:.2f}")
                    else:
                        st.info("ROI hesaplanamıyor: (Navlun + Ham) = 0")
                with m2:
                    if mevcut_roi is not None:
                        st.metric("Mevcut ROI", f"{mevcut_roi:.2f}")

                if (onerilen_fiyat_roi is not None) and st.button("Fiyatı CSV’ye uygula (ROI)"):
                    with st.spinner('Güncelleniyor...'):
                        df_base = load_csv_data()
                        if not df_base.empty:
                            updated = False
                            if 'ean' in df_base.columns and pd.notna(selected_row.get('ean', None)) and str(selected_row['ean']).strip() != "":
                                df_base['ean'] = df_base['ean'].astype(str)
                                mask = df_base['ean'] == str(selected_row['ean'])
                                if mask.any():
                                    df_base.loc[mask, 'fiyat'] = f"€{onerilen_fiyat_roi:.2f}"
                                    updated = True
                            if not updated and 'title' in df_base.columns:
                                mask = df_base['title'] == selected_row['title']
                                if mask.any():
                                    df_base.loc[mask, 'fiyat'] = f"€{onerilen_fiyat_roi:.2f}"
                                    updated = True
                            if updated:
                                df_base.to_csv(CSV_FILE, index=False)
                                try:
                                    load_csv_data.clear()
                                except Exception:
                                    pass
                                st.success("Yeni fiyat (ROI) kaydedildi.")
                                st.rerun()
                            else:
                                st.warning("Güncellenecek satır bulunamadı.")
        else:
            st.info("Hesaplama yapabilmek için önce ürün eklemelisiniz.")
    
    with tab4:
        st.header("📥 Export/Import İşlemleri")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📤 Export")
            
            df = load_csv_data()
            
            if not df.empty:
                # Hesaplamaları ekle
                with st.spinner('Export verileri hazırlanıyor...'):
                    hesaplama_sonuclari = []
                    for index, row in df.iterrows():
                        hesaplama = calculate_total_cost(row, params)
                        hesaplama_sonuclari.append(hesaplama)
                
                export_df = df.copy()
                export_df['Satış Fiyatı'] = df['fiyat'].apply(clean_euro_value)
                export_df['TR→NL→DE Maliyet'] = [h['tr_nl_de_son_maliyet'] for h in hesaplama_sonuclari]
                export_df['TR→DE Maliyet'] = [h['tr_de_son_maliyet'] for h in hesaplama_sonuclari]
                export_df['Optimal Rota'] = [h['optimal_route'] for h in hesaplama_sonuclari]
                export_df['Son Maliyet'] = [h['optimal_cost'] for h in hesaplama_sonuclari]
                export_df['Kar Marjı'] = export_df['Satış Fiyatı'] - export_df['Son Maliyet']
                export_df['Kar Marjı %'] = ((export_df['Satış Fiyatı'] - export_df['Son Maliyet']) / export_df['Satış Fiyatı'] * 100).round(2)
                
                # CSV Export
                csv_buffer = io.StringIO()
                export_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📁 CSV Olarak İndir",
                    data=csv_data,
                    file_name=f"kaufland_products_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
                # Excel Export
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    export_df.to_excel(writer, sheet_name='Ürünler', index=False)
                    
                    # Parametreler sheet'i
                    params_df = pd.DataFrame(list(params.items()), columns=['Parametre', 'Değer'])
                    params_df.to_excel(writer, sheet_name='Parametreler', index=False)
                
                excel_data = excel_buffer.getvalue()
                
                st.download_button(
                    label="📊 Excel Olarak İndir",
                    data=excel_data,
                    file_name=f"kaufland_products_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # JSON Export
                json_data = load_json_data()
                json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
                
                st.download_button(
                    label="🗂️ JSON Olarak İndir",
                    data=json_str,
                    file_name=f"kaufland_products_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
                
                # Boş CSV Şablonu
                template_required = [
                    'title', 'ean', 'iwasku', 'fiyat', 'ham_maliyet_euro', 'desi',
                    'unit_in', 'box_in', 'pick_pack', 'storage', 'fedex',
                    'tr_ne_navlun', 'ne_de_navlun', 'express_kargo', 'ddp', 'tr_de_navlun'
                ]
                template_optional = ['reklam']
                template_cols = template_required + template_optional
                template_df = pd.DataFrame(columns=template_cols)
                tmpl_csv = io.StringIO()
                template_df.to_csv(tmpl_csv, index=False)
                st.download_button(
                    label="📄 Boş CSV Şablonu (İndir)",
                    data=tmpl_csv.getvalue(),
                    file_name="kaufland_template.csv",
                    mime="text/csv",
                    help="Import için kolon isimlerini içeren boş şablon"
                )
            else:
                st.info("Export edilecek ürün bulunmuyor.")
        
        with col2:
            st.subheader("📥 Import")
            
            uploaded_file = st.file_uploader(
                "CSV dosyası yükleyin:",
                type=['csv'],
                help="Mevcut şablonla uyumlu CSV dosyası yükleyebilirsiniz."
            )
            
            if uploaded_file is not None:
                try:
                    new_df = pd.read_csv(uploaded_file)
                    
                    # Gerekli sütunları kontrol et
                    required_columns = [
                        'title', 'ean', 'iwasku', 'fiyat', 'ham_maliyet_euro', 'desi',
                        'unit_in', 'box_in', 'pick_pack', 'storage', 'fedex',
                        'tr_ne_navlun', 'ne_de_navlun', 'express_kargo', 'ddp', 'tr_de_navlun'
                    ]
                    
                    optional_columns = ['reklam']  # İsteğe bağlı sütunlar
                    
                    missing_columns = []
                    for col in required_columns:
                        if col not in new_df.columns:
                            missing_columns.append(col)
                    
                    # Eksik sütun kontrolü
                    if missing_columns:
                        st.error("❌ CSV dosyasında eksik sütunlar bulundu!")
                        st.write("**Eksik sütunlar:**")
                        for col in missing_columns:
                            st.write(f"- `{col}`")
                        
                        st.write("**Gerekli tüm sütunlar:**")
                        st.code(", ".join(required_columns), language="text")
                        
                        st.warning("⚠️ Lütfen CSV dosyanızı kontrol edin ve eksik sütunları ekleyin.")
                        return
                    
                    # Veri türü kontrolü
                    numeric_columns = ['fiyat', 'ham_maliyet_euro', 'desi']
                    validation_errors = []
                    
                    for col in numeric_columns:
                        if col in new_df.columns:
                            # Sayısal olmayan değerleri kontrol et
                            non_numeric_rows = []
                            for idx, value in new_df[col].items():
                                try:
                                    if pd.notna(value) and value != "":
                                        clean_euro_value(value)
                                except:
                                    non_numeric_rows.append(idx + 2)  # +2 çünkü header + 0-based index
                            
                            if non_numeric_rows:
                                validation_errors.append(f"'{col}' sütununda geçersiz değerler (satır: {', '.join(map(str, non_numeric_rows[:5]))})")
                    
                    # Zorunlu alanların boş olup olmadığını kontrol et
                    required_not_empty = ['title', 'fiyat', 'ham_maliyet_euro']
                    for col in required_not_empty:
                        empty_rows = new_df[new_df[col].isna() | (new_df[col] == "")].index + 2
                        if len(empty_rows) > 0:
                            validation_errors.append(f"'{col}' sütunu boş bırakılamaz (satır: {', '.join(map(str, empty_rows[:5]))})")
                    
                    if validation_errors:
                        st.error("❌ CSV dosyasında veri hatası bulundu!")
                        for error in validation_errors:
                            st.write(f"- {error}")
                        st.warning("⚠️ Lütfen hataları düzelttikten sonra tekrar yükleyin.")
                        return
                    
                    st.write("**Yüklenen dosya önizlemesi:**")
                    st.dataframe(new_df.head(), hide_index=True)
                    
                    st.success(f"✅ Dosya doğrulandı! {len(new_df)} satır veri bulundu.")
                    
                    if st.button("Verileri İçe Aktar", type="primary"):
                        # Mevcut verilerle birleştir
                        existing_df = load_csv_data()
                        
                        if existing_df.empty:
                            combined_df = new_df
                        else:
                            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                            # Duplikaları temizle (EAN bazında)
                            if 'ean' in combined_df.columns:
                                combined_df = combined_df.drop_duplicates(subset=['ean'], keep='last')
                        
                        combined_df.to_csv(CSV_FILE, index=False)
                        try:
                            load_csv_data.clear()
                        except Exception:
                            pass
                        
                        st.success(f"✅ {len(new_df)} ürün başarıyla içe aktarıldı!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Dosya yükleme hatası: {str(e)}")
                    st.write("**Olası nedenler:**")
                    st.write("- Dosya formatı CSV değil")
                    st.write("- Dosya bozuk veya okunamıyor")
                    st.write("- Karakter kodlaması sorunu (UTF-8 kullanın)")
    
    with tab5:
        st.header("📈 Analiz ve Raporlar")
        
        df = load_csv_data()
        
        if not df.empty:
            # Hesaplamaları ekle
            with st.spinner('Analiz hesaplanıyor...'):
                hesaplama_sonuclari = []
                for index, row in df.iterrows():
                    hesaplama = calculate_total_cost(row, params)
                    hesaplama_sonuclari.append(hesaplama)
            
            df['Satış Fiyatı'] = df['fiyat'].apply(clean_euro_value)
            df['Son Maliyet'] = [h['son_maliyet'] for h in hesaplama_sonuclari]
            df['Kar Marjı'] = df['Satış Fiyatı'] - df['Son Maliyet']
            df['Kar Marjı %'] = ((df['Satış Fiyatı'] - df['Son Maliyet']) / df['Satış Fiyatı'] * 100).round(2)
            
            # Genel istatistikler
            st.subheader("📊 Genel İstatistikler")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Toplam Ürün", len(df))
            with col2:
                karlı_urun = len(df[df['Kar Marjı'] > 0])
                st.metric("Karlı Ürün", karlı_urun)
            with col3:
                zararlı_urun = len(df[df['Kar Marjı'] < 0])
                st.metric("Zararlı Ürün", zararlı_urun)
            with col4:
                ortalama_kar = df['Kar Marjı %'].mean()
                st.metric("Ortalama Kar %", f"{ortalama_kar:.1f}%")
            
            # En karlı ve en zararlı ürünler
            st.subheader("🏆 En İyi ve En Kötü Performans")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**En Karlı 5 Ürün:**")
                top_profitable = df.nlargest(5, 'Kar Marjı')[['title', 'Kar Marjı', 'Kar Marjı %']]
                st.dataframe(top_profitable, hide_index=True)
            
            with col2:
                st.write("**En Zararlı 5 Ürün:**")
                top_loss = df.nsmallest(5, 'Kar Marjı')[['title', 'Kar Marjı', 'Kar Marjı %']]
                st.dataframe(top_loss, hide_index=True)
            
            # Kar marjı dağılımı
            st.subheader("📊 Kar Marjı Dağılımı")
            
            kar_araliklari = {
                'Çok Yüksek (>40%)': len(df[df['Kar Marjı %'] > 40]),
                'Yüksek (30-40%)': len(df[(df['Kar Marjı %'] >= 30) & (df['Kar Marjı %'] <= 40)]),
                'Orta (20-30%)': len(df[(df['Kar Marjı %'] >= 20) & (df['Kar Marjı %'] < 30)]),
                'Düşük (10-20%)': len(df[(df['Kar Marjı %'] >= 10) & (df['Kar Marjı %'] < 20)]),
                'Çok Düşük (0-10%)': len(df[(df['Kar Marjı %'] >= 0) & (df['Kar Marjı %'] < 10)]),
                'Zararlı (<0%)': len(df[df['Kar Marjı %'] < 0])
            }
            
            kar_df = pd.DataFrame(list(kar_araliklari.items()), columns=['Aralık', 'Ürün Sayısı'])
            
            col1, col2 = st.columns(2)
            
            def _dist_row_style(row):
                aralik = str(row.get('Aralık', ''))
                # Varsayılan nötr stil
                bg, fg = '#ffffff', '#333333'
                if 'Zararlı' in aralik:
                    bg, fg = '#ffe6e6', '#a10000'
                elif '0-10%' in aralik:
                    bg, fg = '#fff3e0', '#8a6d3b'
                elif '10-20%' in aralik:
                    bg, fg = '#fffde7', '#8a6d3b'
                elif '20-30%' in aralik:
                    bg, fg = '#e8f5e9', '#1b5e20'
                elif '30-40%' in aralik:
                    bg, fg = '#dcedc8', '#33691e'
                elif '>40%' in aralik:
                    bg, fg = '#c8e6c9', '#1b5e20'
                return [f'background-color:{bg};color:{fg};'] * len(row)

            with col1:
                styler_dist = kar_df.style.apply(_dist_row_style, axis=1)
                st.dataframe(styler_dist, hide_index=True)
            
            with col2:
                # Basit bar chart
                st.bar_chart(kar_df.set_index('Aralık'))

            # Pareto analizi (kâr katkısına göre ilk %20 ürün)
            st.subheader("🧮 Pareto Analizi (%20 Ürün)")
            if len(df) > 0:
                sorted_df = df.sort_values('Kar Marjı', ascending=False)
                n_top = max(1, int(len(sorted_df) * 0.2))
                pareto_df = sorted_df.head(n_top)
                total_profit = float(df['Kar Marjı'].sum())
                pareto_profit = float(pareto_df['Kar Marjı'].sum())
                pareto_share = (pareto_profit / total_profit * 100.0) if total_profit > 0 else 0.0
                pc1, pc2, pc3 = st.columns(3)
                with pc1:
                    st.metric("Pareto Ürün Sayısı", n_top)
                with pc2:
                    st.metric("Pareto Kârı", f"€{pareto_profit:.2f}")
                with pc3:
                    st.metric("Pareto Kâr Payı", f"{pareto_share:.1f}%")
                st.write("En yüksek katkı yapan ürünler:")
                st.dataframe(pareto_df[['title', 'Kar Marjı', 'Kar Marjı %']].head(10), hide_index=True)

            # Rota bazlı kazanım (tasarruf)
            st.subheader("🛣️ Rota Bazlı Kazanım")
            save_nl = sum(h['cost_difference'] for h in hesaplama_sonuclari if h['optimal_route'] == 'TR→NL→DE')
            save_de = sum(h['cost_difference'] for h in hesaplama_sonuclari if h['optimal_route'] == 'TR→DE')
            cnt_nl = sum(1 for h in hesaplama_sonuclari if h['optimal_route'] == 'TR→NL→DE')
            cnt_de = sum(1 for h in hesaplama_sonuclari if h['optimal_route'] == 'TR→DE')
            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                st.metric("Hollanda Üzerinden Tasarruf", f"€{save_nl:.2f}")
            with rc2:
                st.metric("Direkt Rota Avantajı", f"€{save_de:.2f}")
            with rc3:
                st.metric("NL Rota Ürün Sayısı", cnt_nl)
            with rc4:
                st.metric("Direkt Rota Ürün Sayısı", cnt_de)

            # Senaryo analizi (what-if)
            st.subheader("🧪 Senaryo Analizi (What‑if)")
            with st.expander("Parametreleri göreli değiştir (uygulamaya yazmadan)", expanded=False):
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    komisyon_delta = st.number_input("Komisyon (puan)", value=2.0, min_value=-10.0, max_value=10.0, step=0.5)
                with sc2:
                    reklam_delta = st.number_input("Reklam (€)", value=1.0, min_value=-20.0, max_value=20.0, step=0.5)
                with sc3:
                    vergi_delta = st.number_input("Vergi (puan)", value=0.0, min_value=-10.0, max_value=10.0, step=0.5)

                scenario_params = {
                    'reklam_maliyeti': max(0.0, params['reklam_maliyeti'] + reklam_delta),
                    'pazaryeri_kesintisi': min(100.0, max(0.0, params['pazaryeri_kesintisi'] + komisyon_delta)),
                    'vergi_yuzdesi': min(100.0, max(0.0, params['vergi_yuzdesi'] + vergi_delta)),
                }

                with st.spinner('Senaryo hesaplanıyor...'):
                    hesaplama_sonuclari_scn = []
                    for _, row in df.iterrows():
                        hesaplama_sonuclari_scn.append(calculate_total_cost(row, scenario_params))
                df_scn = df.copy()
                df_scn['Son Maliyet'] = [h['son_maliyet'] for h in hesaplama_sonuclari_scn]
                df_scn['Kar Marjı'] = df_scn['Satış Fiyatı'] - df_scn['Son Maliyet']
                df_scn['Kar Marjı %'] = ((df_scn['Satış Fiyatı'] - df_scn['Son Maliyet']) / df_scn['Satış Fiyatı'] * 100).round(2)

                base_total_profit = float(df['Kar Marjı'].sum())
                scn_total_profit = float(df_scn['Kar Marjı'].sum())
                base_profitable = int((df['Kar Marjı'] > 0).sum())
                scn_profitable = int((df_scn['Kar Marjı'] > 0).sum())
                base_avg_pct = float(df['Kar Marjı %'].mean()) if len(df) else 0.0
                scn_avg_pct = float(df_scn['Kar Marjı %'].mean()) if len(df_scn) else 0.0

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("Toplam Kâr (Senaryo)", f"€{scn_total_profit:.2f}", delta=f"€{(scn_total_profit - base_total_profit):.2f}")
                with mc2:
                    st.metric("Kârlı Ürün (Senaryo)", scn_profitable, delta=scn_profitable - base_profitable)
                with mc3:
                    st.metric("Ortalama Kâr % (Senaryo)", f"{scn_avg_pct:.1f}%", delta=f"{(scn_avg_pct - base_avg_pct):.1f} pp")
            
            # Öneriler
            st.subheader("💡 Öneriler")
            
            zararlı_urun_sayisi = len(df[df['Kar Marjı'] < 0])
            düşük_kar_sayisi = len(df[(df['Kar Marjı %'] >= 0) & (df['Kar Marjı %'] < 20)])
            
            if zararlı_urun_sayisi > 0:
                st.warning(f"⚠️ {zararlı_urun_sayisi} ürün zarar ediyor. Bu ürünlerin fiyatlarını gözden geçirin.")
            
            if düşük_kar_sayisi > 0:
                st.info(f"ℹ️ {düşük_kar_sayisi} ürünün kar marjı %20'nin altında. Fiyat optimizasyonu düşünebilirsiniz.")
            
            if ortalama_kar > 20:
                st.success("✅ Genel kar marjı sağlıklı seviyede!")
        else:
            st.info("Analiz yapabilmek için önce ürün eklemelisiniz.")
    
    # Alt kısım bilgi
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        🛒 Kaufland Fiyat Hesaplama Modülü | Mahir Tarafından Geliştirildi
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
