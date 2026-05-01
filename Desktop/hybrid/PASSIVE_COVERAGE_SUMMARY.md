# Pasif Yetenek Kapsama Raporu

## 📊 Genel Durum

- **Toplam Kart:** 101
- **Pasif Yetenekli Kart:** 82
- **Handler'ı Olan:** 51 (✅ %62.2)
- **Handler'ı Olmayan:** 31 (❌ %37.8)

## 🎯 Pasif Tiplere Göre Kapsama

| Pasif Tipi | Toplam | Var | Yok | Kapsama |
|------------|--------|-----|-----|---------|
| **ECONOMY** | 10 | 10 | 0 | ✅ %100 |
| **COMBAT** | 21 | 14 | 7 | ⚠️ %66.7 |
| **COMBO** | 8 | 6 | 2 | ⚠️ %75.0 |
| **COPY** | 8 | 5 | 3 | ⚠️ %62.5 |
| **SURVIVAL** | 9 | 6 | 3 | ⚠️ %66.7 |
| **SYNERGY_FIELD** | 26 | 10 | 16 | ❌ %38.5 |

## ❌ Eksik Handler'lar (31 Kart)

### 🔴 SYNERGY_FIELD (16 kart - En düşük kapsama)

1. **Kraken** - Komşu düşman kartların Connection kenarlarına -1 alan etkisi
2. **Opera** - 2+ Sanat kartı varsa tüm Sanat kartlarına +1 Prestige
3. **Baroque** - 2+ Sanat kartı varsa Prestige kenarlarına +1
4. **Kabuki** - Eclipse aktifken komşu müttefik kartlara +1 Secret
5. **Blue Whale** - 3+ Doğa kartı varsa tüm müttefik kartlara +1 Harmony
6. **Coral Reef** - Komşu müttefik Doğa kartlarına tur başına +1 Harmony
7. **Rainforest** - 4+ Doğa kartı varsa tüm Doğa kartlarına +1 Spread
8. **Cordyceps** - Rakip komşu kartlara tur başına -1 Trace
9. **Milky Way** - 3+ Kozmos kartı varsa tüm Kozmos kartlarına +1 Gravity
10. **Andromeda Galaxy** - 4+ Kozmos kartı varsa Gravity kenarlarına +2
11. **Europa** - Komşu müttefik Kozmos kartlarına +1 Harmony
12. **Quasar** - 3+ Kozmos kartı varsa tüm kartlara +1 Spread
13. **Periodic Table** - 4+ Bilim kartı varsa tüm Bilim kartlarına +1 Intelligence +1 Meaning
14. **Higgs Boson** - Boarddayken tüm kartların Gravity kenarlarına +1
15. **Renaissance** - 3+ farklı kategoriden kart varsa tüm kartlara +1 Meaning
16. **Roman Empire** - 4+ Tarih kartı varsa tüm müttefik kartlara +1 Durability

### 🟡 COMBAT (7 kart)

1. **Quetzalcoatl** - Combat kazanılırsa 1 komşu müttefik karta o tur için +1 Speed
2. **Ragnarök** - Combat kazanılırsa rakibin rastgele kartının en yüksek kenarına -1
3. **Flamenco** - Combat kazanılırsa tüm müttefik kartlara o tur için +1 Speed
4. **Asteroid Belt** - Combat kazanılırsa rakip boarduna -1 Size alan etkisi (komşulara)
5. **Quantum Mechanics** - Combat kazanılınca rakibin rastgele 2 kenarı yer değiştirir
6. **Mongol Empire** - Combat kazanılırsa rakip boardundaki 2 komşu karta -1 Speed
7. **Sparta** - Combat kazanılırsa kalıcı +2 Power birikir (maks +4 oyun boyunca)

### 🟢 SURVIVAL (3 kart)

1. **Tardigrade** - Yok edilmeden önce Durability grup kenarları 3'e sıfırlanır, boardda kalır (2 kez)
2. **Betelgeuse** - Yok edilmeden önce patlama: tüm komşu kartların en yüksek kenarına -1
3. **Supernova** - Yok edildiğinde 3 komşu düşman kartın en yüksek kenarına -2

### 🔵 COPY (3 kart)

1. **Event Horizon** - Kopya sayacı tur başına +1 ekstra ilerler (Catalyst etkisini kopyalar)
2. **Charles Darwin** - Her kopya güçlenmesinde sonraki eşik 1 tur erken gelir
3. **DNA** - Kopya güçlenmesinde tüm kopyalara kalıcı +1 Durability

### 🟣 COMBO (2 kart)

1. **Jazz** - Combo eşleşmesi olduğunda +1 altın (maks 2/tur)
2. **Bioluminescence** - Combo eşleşmesi olduğunda komşu müttefik kartlara o tur için +1 Harmony

## ⚠️ Dikkat Edilmesi Gerekenler

### Yanlış Kayıtlı Handler'lar

Aşağıdaki handler'lar kayıtlı ama kart havuzunda yok (muhtemelen isim değişikliği):

- **Midas** → Kart havuzunda "Midas Dokunuşu" olarak var (handler zaten çalışıyor)
- **Ragnarok** → Kart havuzunda "Ragnarök" olarak var (handler YOK)
- **Ragnark** → Typo, düzeltilmeli
- **RagnarÃ¶k** → Encoding hatası, düzeltilmeli

### Ragnarök Handler Sorunu

`Ragnarök` kartı için handler kayıtlı ama çalışmıyor çünkü:
- Handler: `@passive("Ragnarok", "Ragnark", "RagnarÃ¶k")`
- Gerçek kart ismi: `"Ragnarök"` (ö karakteri farklı)

**Çözüm:** Handler'a `"Ragnarök"` ekle veya kart ismini düzelt.

## 🎯 Öncelikli Yapılacaklar

### 1. Yüksek Öncelik (Oynanabilirliği Etkiler)

**SYNERGY_FIELD kartları** - En düşük kapsama (%38.5):
- Milky Way, Andromeda Galaxy, Quasar (Kozmos sinerji grubu)
- Blue Whale, Coral Reef, Rainforest (Doğa sinerji grubu)
- Opera, Baroque (Sanat sinerji grubu)
- Periodic Table, Higgs Boson (Bilim sinerji grubu)

### 2. Orta Öncelik (Denge ve Çeşitlilik)

**COMBAT kartları** - Popüler mekanik:
- Sparta (kalıcı güç birikimi)
- Ragnarök (rastgele debuff)
- Quantum Mechanics (kenar swap - benzersiz mekanik)

**SURVIVAL kartları** - Kritik anlar:
- Tardigrade (2 kez hayatta kalma)
- Betelgeuse, Supernova (patlama efektleri)

### 3. Düşük Öncelik (Niş Mekanikler)

**COPY kartları** - Az kullanılan:
- Event Horizon, Charles Darwin, DNA

**COMBO kartları** - Zaten yüksek kapsama:
- Jazz, Bioluminescence

## 📝 Uygulama Önerileri

### Hızlı Düzeltmeler

1. **Ragnarök handler'ını düzelt:**
   ```python
   @passive("Ragnarok", "Ragnarök", "Ragnark", "RagnarÃ¶k")
   ```

2. **Benzer pattern'leri kullan:**
   - Opera → Olympus pattern'ini kopyala (2+ kategori kontrolü)
   - Milky Way → Isaac Newton pattern'ini kopyala (3+ kategori kontrolü)
   - Periodic Table → Isaac Newton + çift stat buff

### Yeni Handler Şablonları

**Synergy Field (kategori sayısı kontrolü):**
```python
@passive("Milky Way")
def _passive_milky_way(card, trigger, owner, opponent, ctx):
    if trigger == "pre_combat" and owner:
        cosmos_count = sum(1 for c in owner.board.alive_cards() 
                          if c.category == "Cosmos")
        if cosmos_count >= 3:
            for c in owner.board.alive_cards():
                if c.category == "Cosmos" and c.has_stat("Gravity"):
                    c.add_base_stat("Gravity", 1)
        return 1
    return 0
```

**Combat (board-wide buff):**
```python
@passive("Flamenco")
def _passive_flamenco(card, trigger, owner, opponent, ctx):
    if trigger == "combat_win" and owner:
        turn = ctx.get("turn", 1)
        for c in owner.board.alive_cards():
            _add_temp_effect(c, "Speed", 1, turn)
    return 0
```

## 📈 İlerleme Takibi

- [ ] ECONOMY: ✅ %100 (10/10) - TAMAMLANDI
- [ ] COMBAT: ⚠️ %66.7 (14/21) - 7 kart eksik
- [ ] COMBO: ⚠️ %75.0 (6/8) - 2 kart eksik
- [ ] COPY: ⚠️ %62.5 (5/8) - 3 kart eksik
- [ ] SURVIVAL: ⚠️ %66.7 (6/9) - 3 kart eksik
- [ ] SYNERGY_FIELD: ❌ %38.5 (10/26) - 16 kart eksik

**Hedef:** %100 kapsama (82/82 kart)
**Mevcut:** %62.2 kapsama (51/82 kart)
**Kalan:** 31 handler implementasyonu

---

*Rapor oluşturma tarihi: 2026-04-30*
*Test scripti: `test_passive_coverage.py`*
*Detaylı JSON rapor: `passive_coverage_report.json`*
