#!/usr/bin/env python3
"""
Card Image Path Updater
========================
cards.json dosyasına otomatik olarak image_front ve image_back path'leri ekler.

Kullanım:
    python update_card_images.py

Çıktı:
    assets/data/cards.json güncellenir (backup: cards.json.bak)
"""

import json
import os
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CARDS_JSON = PROJECT_ROOT / "assets" / "data" / "cards.json"
FRONTS_DIR = PROJECT_ROOT / "assets" / "cards" / "fronts"
BACKS_DIR = PROJECT_ROOT / "assets" / "cards" / "backs"

def sanitize_filename(name: str) -> str:
    """Kart adını dosya adına çevir (boşluk -> underscore, özel karakter temizle)"""
    # Türkçe karakterleri değiştir
    replacements = {
        'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    for tr, en in replacements.items():
        name = name.replace(tr, en)
    
    # Boşluk -> underscore
    name = name.replace(' ', '_')
    
    # Özel karakterleri temizle (sadece alfanumerik ve underscore)
    name = ''.join(c for c in name if c.isalnum() or c == '_')
    
    return name

def check_file_exists(path: Path) -> bool:
    """Dosya var mı kontrol et"""
    return path.exists() and path.is_file()

def update_cards_json():
    """cards.json'u güncelle"""
    
    # Backup oluştur
    if CARDS_JSON.exists():
        backup = CARDS_JSON.with_suffix('.json.bak')
        import shutil
        shutil.copy2(CARDS_JSON, backup)
        print(f"✅ Backup oluşturuldu: {backup.name}")
    
    # JSON oku
    with open(CARDS_JSON, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    print(f"\n📦 {len(cards)} kart bulundu\n")
    
    updated_count = 0
    missing_fronts = []
    missing_backs = []
    
    for card in cards:
        name = card.get('name', 'Unknown')
        filename = sanitize_filename(name)
        
        # Front image path
        front_filename = f"{filename}_front.png"
        front_path = FRONTS_DIR / front_filename
        front_res_path = f"res://assets/cards/fronts/{front_filename}"
        
        # Back image path
        back_filename = f"{filename}_back.png"
        back_path = BACKS_DIR / back_filename
        back_res_path = f"res://assets/cards/backs/{back_filename}"
        
        # Güncelle
        card['image_front'] = front_res_path
        card['image_back'] = back_res_path
        updated_count += 1
        
        # Dosya var mı kontrol et
        if not check_file_exists(front_path):
            missing_fronts.append(front_filename)
        if not check_file_exists(back_path):
            missing_backs.append(back_filename)
        
        print(f"  {name:30} → {filename}_front.png / {filename}_back.png")
    
    # Kaydet
    with open(CARDS_JSON, 'w', encoding='utf-8') as f:
        json.dump(cards, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {updated_count} kart güncellendi!")
    print(f"💾 Kaydedildi: {CARDS_JSON}")
    
    # Eksik dosyalar
    if missing_fronts or missing_backs:
        print("\n⚠️  Eksik Dosyalar:")
        if missing_fronts:
            print(f"\n  📁 Fronts ({len(missing_fronts)} eksik):")
            for f in missing_fronts[:10]:  # İlk 10'u göster
                print(f"    - {f}")
            if len(missing_fronts) > 10:
                print(f"    ... ve {len(missing_fronts) - 10} tane daha")
        
        if missing_backs:
            print(f"\n  📁 Backs ({len(missing_backs)} eksik):")
            for f in missing_backs[:10]:
                print(f"    - {f}")
            if len(missing_backs) > 10:
                print(f"    ... ve {len(missing_backs) - 10} tane daha")
        
        print("\n💡 İpucu: Eksik dosyaları ilgili klasörlere ekle:")
        print(f"   - {FRONTS_DIR}")
        print(f"   - {BACKS_DIR}")
    else:
        print("\n✅ Tüm dosyalar mevcut!")

if __name__ == "__main__":
    print("=" * 60)
    print("Card Image Path Updater")
    print("=" * 60)
    
    # Klasör kontrolü
    if not CARDS_JSON.exists():
        print(f"❌ Hata: {CARDS_JSON} bulunamadı!")
        exit(1)
    
    if not FRONTS_DIR.exists():
        print(f"⚠️  Uyarı: {FRONTS_DIR} bulunamadı, oluşturuluyor...")
        FRONTS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not BACKS_DIR.exists():
        print(f"⚠️  Uyarı: {BACKS_DIR} bulunamadı, oluşturuluyor...")
        BACKS_DIR.mkdir(parents=True, exist_ok=True)
    
    update_cards_json()
    
    print("\n" + "=" * 60)
    print("✅ Tamamlandı!")
    print("=" * 60)
