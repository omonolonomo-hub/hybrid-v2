# 5000 Maçlık Detaylı Simülasyon Raporu

## Genel Bakış

5000 maçlık kapsamlı simülasyon başarıyla tamamlandı. Her maç için detaylı kayıtlar tutuldu ve kapsamlı analizler yapıldı.

## Simülasyon Detayları

- **Toplam Maç**: 5000
- **Oyuncu Sayısı**: 4 (her maçta)
- **Stratejiler**: builder, evolver, economist, balancer
- **Ortalama Oyun Uzunluğu**: 23.4 tur
- **En Kısa Oyun**: 11 tur
- **En Uzun Oyun**: 37 tur

## Strateji Performansları

### 1. Builder - ⭐ ÇOK GÜÇLÜ (Meta Dominant)
- **Kazanma Oranı**: 55.7%
- **Ortalama Hasar**: 223.9
- **Ortalama Kill**: 4.9
- **Hayatta Kalma HP**: 40.1
- **Değerlendirme**: Builder stratejisi açık ara en güçlü. Board boyutu avantajı çok dominant.

### 2. Economist - ~ ORTA
- **Kazanma Oranı**: 17.8%
- **Ortalama Hasar**: 123.3
- **Ortalama Kill**: 5.2
- **Hayatta Kalma HP**: 6.6
- **Değerlendirme**: Ekonomi avantajı geç oyunda etkili ama erken baskıya karşı zayıf.

### 3. Evolver - ✗ ZAYIF
- **Kazanma Oranı**: 14.9%
- **Ortalama Hasar**: 124.4
- **Ortalama Kill**: 5.5
- **Hayatta Kalma HP**: 5.6
- **Değerlendirme**: Evrim mekanizması yeterince güçlü değil. Buff gerekli.

### 4. Balancer - ✗ ZAYIF
- **Kazanma Oranı**: 11.6%
- **Ortalama Hasar**: 115.4
- **Ortalama Kill**: 5.2
- **Hayatta Kalma HP**: 4.2
- **Değerlendirme**: Sinerji odaklı yaklaşım yetersiz. Threshold bonusları artırılmalı.

## Kart Performansları

### En Güçlü Kartlar (>50% Kazanma Oranı)

| Kart | Kazanma % | Satın Alma | Ort. Güç |
|------|-----------|------------|----------|
| Minotaur | 62.3% | 2683 | 19.8 |
| Asteroid Belt | 60.0% | 2408 | 25.0 |
| Tardigrade | 59.9% | 1805 | 23.1 |
| Migration | 55.2% | 1439 | 22.8 |
| Truva Atı | 54.9% | 1338 | 22.9 |
| Venus Flytrap | 54.6% | 1340 | 23.8 |
| Narwhal | 53.0% | 1331 | 25.2 |
| Sirius | 52.5% | 1169 | 26.6 |
| Cerberus | 51.9% | 2819 | 27.2 |

### En Popüler Kartlar

| Kart | Satın Alma | Kazanma % |
|------|------------|-----------|
| Platypus | 6998 | 29.8% |
| Frida Kahlo | 6677 | 18.4% |
| Moon Landing | 6552 | 20.3% |
| Ottoman Empire | 6381 | 28.6% |
| Space-Time | 6207 | 36.9% |
| Pop Art | 6042 | 21.4% |
| Mongol Empire | 6025 | 35.3% |
| Graffiti | 6017 | 19.8% |
| Ragnarök | 5963 | 32.3% |
| Shadow Puppetry | 5887 | 29.4% |

## Oyun Dinamikleri

### Tur Dağılımı

- **11-15 tur**: 35 maç (0.7%) - Çok hızlı oyunlar
- **16-20 tur**: 1272 maç (25.4%) - Hızlı oyunlar
- **21-25 tur**: 2099 maç (42.0%) - Normal oyunlar (en yaygın)
- **26-30 tur**: 1436 maç (28.7%) - Uzun oyunlar
- **31-35 tur**: 157 maç (3.1%) - Çok uzun oyunlar
- **36+ tur**: 1 maç (0.0%) - Aşırı uzun oyun

Oyunların %42'si 21-25 tur arasında tamamlanıyor, bu sağlıklı bir dağılım gösteriyor.

## Balans Önerileri

### Acil Müdahale Gereken Konular

#### 1. Builder Stratejisi Çok Dominant
**Problem**: %55.7 kazanma oranı (hedef ~%25)

**Öneriler**:
- Board boyutu limitini 37'den 30'a düşür
- Kart maliyetlerini %10-15 artır
- Tempo stratejisine erken oyun buff'u ver

#### 2. Evolver ve Balancer Çok Zayıf
**Problem**: %15'in altında kazanma oranı

**Evolver için öneriler**:
- Evrim için gereken kopya sayısını 3'ten 2'ye düşür
- Evolved kartlara +%20 güç bonusu ekle
- Copy strengthening'i evolver için de aktif et

**Balancer için öneriler**:
- Threshold bonuslarını artır (3 kart: +20 → +30)
- Sinerji cap'ini %30'dan %40'a çıkar
- Diversity bonusunu +1'den +2'ye çıkar

#### 3. Aşırı Güçlü Kartlar
**Nerf gerektirenler**:
- Minotaur: %62.3 kazanma oranı → Statları -2 düşür
- Asteroid Belt: %60.0 → Pasif etkisini zayıflat
- Tardigrade: %59.9 → Durability'yi 9'dan 7'ye düşür

## Oluşturulan Dosyalar

### Simülasyon Sonuçları
- `output/detailed_simulation/game_results.json` - 5000 maçın detaylı sonuçları
- `output/detailed_simulation/strategy_performance.json` - Strateji metrikleri
- `output/detailed_simulation/strategy_performance.csv` - CSV formatında
- `output/detailed_simulation/card_performance.json` - Kart metrikleri
- `output/detailed_simulation/card_performance_top50.csv` - En popüler 50 kart
- `output/detailed_simulation/summary_report.txt` - Özet rapor
- `output/detailed_simulation/comprehensive_analysis.txt` - Kapsamlı analiz

### Event Logları
- `output/logs/simulation_events.jsonl` - Tüm game eventleri (JSONL formatı)
- `output/logs/combat_events.jsonl` - Combat eventleri (JSONL formatı)

## Kullanım

### Simülasyonu Çalıştırma
```bash
# 5000 maç (varsayılan)
python tools/run_detailed_simulation.py

# Özel maç sayısı
python tools/run_detailed_simulation.py --games 1000
```

### Analiz Çalıştırma
```bash
python tools/analyze_simulation_results.py
```

## Sonuç

5000 maçlık simülasyon, oyunun mevcut durumunu net bir şekilde ortaya koydu:

✅ **Güçlü Yönler**:
- Oyun uzunluğu dengeli (ortalama 23.4 tur)
- Kart çeşitliliği yüksek (101 kart, hepsi kullanılıyor)
- Micro-buff sistemi çalışıyor (19 kart bufflandı)

⚠️ **İyileştirme Gereken Alanlar**:
- Builder stratejisi çok dominant (%55.7)
- Evolver ve Balancer çok zayıf (%15 altı)
- Bazı kartlar aşırı güçlü (Minotaur %62.3)

🎯 **Öncelikli Aksiyonlar**:
1. Builder'ı nerf et (board limit + maliyet artışı)
2. Evolver ve Balancer'a buff ver
3. Aşırı güçlü kartları dengele

## Tarih

- **Simülasyon Tarihi**: 2026-03-29
- **Simülasyon Süresi**: ~3 dakika
- **Engine Versiyonu**: v0.7 (micro-buff dahil)
