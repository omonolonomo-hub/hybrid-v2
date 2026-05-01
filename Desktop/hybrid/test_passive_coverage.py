"""
Pasif Yetenek Kapsama Testi
============================
Bu script tüm kartları tarar ve hangi kartların pasif yeteneklerinin
handler'a sahip olduğunu, hangilerinin olmadığını tespit eder.
"""

import os
import sys
import json
from collections import defaultdict

# Proje kökünü path'e ekle
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from engine_core.passives.registry import PASSIVE_HANDLERS

# Cards.json dosyasını yükle
CARDS_JSON_PATH = os.path.join("assets", "data", "cards.json")

def load_cards():
    """Tüm kartları yükle"""
    if not os.path.exists(CARDS_JSON_PATH):
        print(f"❌ Kart dosyası bulunamadı: {CARDS_JSON_PATH}")
        sys.exit(1)
    
    with open(CARDS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_passive_coverage():
    """Pasif yetenek kapsama analizi yap"""
    cards = load_cards()
    
    # Pasif tiplere göre grupla
    by_passive_type = defaultdict(list)
    cards_with_handlers = []
    cards_without_handlers = []
    
    for card in cards:
        name = card.get("name", "")
        passive_type = card.get("passive_type", "none")
        passive_effect = card.get("passive_effect", "")
        
        # "none" veya boş pasif yetenekleri atla
        if passive_type == "none" or not passive_effect:
            continue
        
        by_passive_type[passive_type].append({
            "name": name,
            "effect": passive_effect,
            "has_handler": name in PASSIVE_HANDLERS
        })
        
        if name in PASSIVE_HANDLERS:
            cards_with_handlers.append(name)
        else:
            cards_without_handlers.append({
                "name": name,
                "type": passive_type,
                "effect": passive_effect
            })
    
    return {
        "by_type": by_passive_type,
        "with_handlers": cards_with_handlers,
        "without_handlers": cards_without_handlers,
        "total_cards": len(cards),
        "total_with_passive": sum(len(v) for v in by_passive_type.values()),
        "total_handlers": len(PASSIVE_HANDLERS)
    }

def print_report(analysis):
    """Analiz raporunu yazdır"""
    print("=" * 80)
    print("PASİF YETENEKLERİN KAPSAMA ANALİZİ")
    print("=" * 80)
    print()
    
    # Genel istatistikler
    print("📊 GENEL İSTATİSTİKLER")
    print("-" * 80)
    print(f"Toplam Kart Sayısı: {analysis['total_cards']}")
    print(f"Pasif Yetenekli Kart Sayısı: {analysis['total_with_passive']}")
    print(f"Kayıtlı Handler Sayısı: {analysis['total_handlers']}")
    print(f"Handler'ı Olan Kart Sayısı: {len(analysis['with_handlers'])}")
    print(f"Handler'ı Olmayan Kart Sayısı: {len(analysis['without_handlers'])}")
    print()
    
    # Kapsama oranı
    if analysis['total_with_passive'] > 0:
        coverage = (len(analysis['with_handlers']) / analysis['total_with_passive']) * 100
        print(f"✅ Kapsama Oranı: {coverage:.1f}%")
    else:
        print("⚠️  Pasif yetenekli kart bulunamadı!")
    print()
    
    # Pasif tiplere göre dağılım
    print("📋 PASİF TİPLERE GÖRE DAĞILIM")
    print("-" * 80)
    for passive_type, cards in sorted(analysis['by_type'].items()):
        with_handler = sum(1 for c in cards if c['has_handler'])
        without_handler = len(cards) - with_handler
        print(f"\n{passive_type.upper()}: {len(cards)} kart")
        print(f"  ✅ Handler var: {with_handler}")
        print(f"  ❌ Handler yok: {without_handler}")
        
        # Handler'ı olmayan kartları listele
        if without_handler > 0:
            print(f"  Handler'ı olmayan kartlar:")
            for card in cards:
                if not card['has_handler']:
                    print(f"    • {card['name']}")
                    print(f"      └─ {card['effect'][:80]}...")
    print()
    
    # Handler'ı olan kartlar
    print("✅ HANDLER'I OLAN KARTLAR")
    print("-" * 80)
    for name in sorted(analysis['with_handlers']):
        handler = PASSIVE_HANDLERS[name]
        print(f"  • {name} → {handler.__name__}")
    print()
    
    # Handler'ı olmayan kartların detaylı listesi
    if analysis['without_handlers']:
        print("❌ HANDLER'I OLMAYAN KARTLAR (DETAYLI)")
        print("-" * 80)
        for card in sorted(analysis['without_handlers'], key=lambda x: (x['type'], x['name'])):
            print(f"\n📌 {card['name']}")
            print(f"   Tip: {card['type']}")
            print(f"   Açıklama: {card['effect']}")
    print()
    
    # Kayıtlı ama kart havuzunda olmayan handler'lar
    print("⚠️  KAYITLI AMA KART HAVUZUNDA OLMAYAN HANDLER'LAR")
    print("-" * 80)
    cards = load_cards()
    card_names = {c.get("name", "") for c in cards}
    orphan_handlers = [name for name in PASSIVE_HANDLERS.keys() if name not in card_names]
    
    if orphan_handlers:
        for name in sorted(orphan_handlers):
            print(f"  • {name}")
    else:
        print("  Yok - Tüm handler'lar geçerli kartlara bağlı ✅")
    print()
    
    print("=" * 80)

def save_report(analysis):
    """Raporu JSON dosyasına kaydet"""
    output_path = "passive_coverage_report.json"
    
    # JSON serileştirilebilir formata dönüştür
    report = {
        "summary": {
            "total_cards": analysis['total_cards'],
            "total_with_passive": analysis['total_with_passive'],
            "total_handlers": analysis['total_handlers'],
            "cards_with_handlers": len(analysis['with_handlers']),
            "cards_without_handlers": len(analysis['without_handlers']),
            "coverage_percentage": (len(analysis['with_handlers']) / analysis['total_with_passive'] * 100) 
                                   if analysis['total_with_passive'] > 0 else 0
        },
        "by_passive_type": {
            ptype: {
                "total": len(cards),
                "with_handler": sum(1 for c in cards if c['has_handler']),
                "without_handler": sum(1 for c in cards if not c['has_handler']),
                "cards": [{"name": c['name'], "has_handler": c['has_handler'], "effect": c['effect']} 
                         for c in cards]
            }
            for ptype, cards in analysis['by_type'].items()
        },
        "cards_with_handlers": sorted(analysis['with_handlers']),
        "cards_without_handlers": sorted(analysis['without_handlers'], key=lambda x: x['name'])
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Detaylı rapor kaydedildi: {output_path}")

if __name__ == "__main__":
    print("🔍 Pasif yetenek kapsama analizi başlatılıyor...\n")
    
    analysis = analyze_passive_coverage()
    print_report(analysis)
    save_report(analysis)
    
    # Çıkış kodu: Handler'ı olmayan kart varsa 1, yoksa 0
    sys.exit(1 if analysis['without_handlers'] else 0)
