# AUTOCHESS HYBRID — Game Design Document
### v0.6 · Mart 2026 · 700+ simülasyon destekli

> **8 Oyuncu · 101 Kart · 19 Hex · Hex-Grid Autochess**
> Her oyuncu 3 rastgele ◆ kartla lobiye girer. Amaç: rakiplerin canını sıfırlamak.

---

## İÇİNDEKİLER

1. [Oyun Tanımı ve Temel Prensipler](#1)
2. [Başlangıç — Lobi ve Başlangıç Elleri](#2)
3. [Kart Sistemi](#3)
4. [Kare Kart Sistemi (Catalyst / Eclipse)](#4)
5. [Board ve Hex Grid](#5)
6. [Tur Yapısı](#6)
7. [Alan Etkisi Sistemi](#7)
8. [Combat Sistemi](#8)
9. [Combo Sistemi](#9)
10. [Hasar ve Can Sistemi](#10)
11. [Ekonomi Sistemi](#11)
12. [Puan ve Eşleştirme](#12)
13. [Map Olayları](#13)
14. [Threshold Sistemi](#14)
15. [Strateji Yolları (v0.6 Dengeli)](#15)
16. [Kart Havuzu](#16)
17. [Örnek Oyun Turu](#17)
18. [Simülasyon Verileri ve Denge Notu](#18)
19. [Hızlı Başvuru](#19)
20. [Değişiklik Geçmişi](#20)

---

## 1. Oyun Tanımı ve Temel Prensipler {#1}

Autochess Hybrid, hex-grid üzerinde oynanan otomatik savaş (autochess) ve kart koleksiyon oyununun birleşimidir. 8 kişilik lobide her oyuncunun kendi ayrı board kopyası vardır. Kartlar ortak havuzdan market aracılığıyla satın alınır, hex hücrelere yerleştirilir ve combatlar otomatik çözülür.

| Oyuncu Sayısı | Başlangıç Canı | Board Boyutu | Kart Havuzu |
|---|---|---|---|
| 8 kişilik lobi | **150** | Yarıçap-2 (19 hücre) | 101 kart |

### 1.1 Temel Prensipler

**Açık Board Sistemi**
Her oyuncunun board'u diğerleri tarafından görülebilir. Eclipse kare kartı bu kuralın tek istisnasıdır.

**Eş Zamanlı Combat**
Kartlar sıraya girmez. Aynı koordinattaki iki kart 6 kenarını eş zamanlı karşılaştırır.

**Can Sistemi**
Başlangıç canı: **150**. Turu kaybeden oyuncu hasar formülüne göre can kaybeder. Canı sıfırlanan oyuncu elenir.

> ℹ️ **v0.6:** Başlangıç canı 100'den 150'ye çıkarıldı — geç oyun stratejilerine alan açmak için.

---

## 2. Başlangıç — Lobi ve Başlangıç Elleri {#2}

> ⭐ **v0.6 ile eklendi:** Her oyuncu lobi başında 3 rastgele ◆ (en düşük nadir) kartla başlar.

Maç başlamadan önce, tüm oyunculara (insan ve AI dahil) 101 kartlık havuzdan rastgele seçilen 3 adet ◆ (Yaygın) kart dağıtılır. Bu kartlar birinci tur geliri alınmadan önce elde hazır bulunur.

| Kural | Detay |
|---|---|
| Başlangıç kart sayısı | 3 adet |
| Başlangıç kart nadirliği | ◆ (Yaygın) — yalnızca en düşük kademe |
| Seçim yöntemi | Havuzdan rastgele, her oyuncuya bağımsız |
| 1. tur öncesi yerleşim | Oyuncu ister hepsini, ister bir kısmını board'a koyabilir |

> ℹ️ Başlangıç elleri sayesinde 1. tur beraberlik zinciri kırılmıştır — tüm oyuncular ilk turdan itibaren puan üretir.

---

## 3. Kart Sistemi {#3}

### 3.1 Statlar ve Gruplar

Her kart 12 statın 6'sını taşır. Statlar 3 gruba ayrılır:

| Grup | Statlar | Avantaj |
|---|---|---|
| **VARLIK** | Güç / Dayanıklılık / Boyut / Hız | BAĞLANTI'yı yener |
| **ZİHİN** | Anlam / Sır / Zeka / İz | VARLIK'ı yener |
| **BAĞLANTI** | Çekim / Uyum / Yayılım / Prestij | ZİHİN'i yener |

> ℹ️ Grup avantajı: Kazanan grubun kenarı rakibe karşı +1 combat bonusu alır.

### 3.2 Kenar Yerleşimi

Bir kartın seçilen 6 statı, kartın 6 hex kenarına sırayla atanır. Kuzey'den başlayarak saat yönünde: **K, KD, GD, G, GB, KB**.

### 3.3 Nadirlik ve Stat Tavanı

| Nadirlik | İsim | Stat Tavanı | Maliyet | Kart Sayısı |
|---|---|---|---|---|
| ◆ | Yaygın | 30 | 1 altın | 35 |
| ◆◆ | Nadir | 36 | 2 altın | 28 |
| ◆◆◆ | Epik | 42 | 3 altın | 20 |
| ◆◆◆◆ | Efsanevi | 48 | **8 altın** | 12 |
| ◆◆◆◆◆ | Tanrısal | 54 | **10 altın** | 6 |

> ⚠️ **v0.6:** ◆◆◆◆ maliyet 4→8, ◆◆◆◆◆ maliyet 5→10 altına çıkarıldı. Nadir kart avantajı ham güçte korundu, hasar formülünden rarity bonusu kaldırıldı.

### 3.4 Pasif Yetenek Tipleri

| Pasif Tipi | Tetikleyici |
|---|---|
| `combat` | Combat kazanıldığında veya kaybedildiğinde |
| `combo` | Belirli sayıda combo eşleşme oluştuğunda |
| `kopya` | Kopya güçlenme gerçekleştiğinde |
| `ekonomi` | Her tur başı veya market işlemi sonrası |
| `hayatta_kalma` | Kart yok edilmeden önce devreye girer |
| `sinerjik_alan` | Board'da bulunduğu sürece komşu kartları etkiler |

### 3.5 Kopya Güçlenme Sistemi

Aynı kartın birden fazla kopyası biriktirildiğinde eşik turuna ulaşıldığında kart güçlenir:

| Kopya | Normal Eşik | Catalyst ile | Etki |
|---|---|---|---|
| 2. kopya | 4. tur | 3. tur | En yüksek kenara +2 kalıcı |
| 3. kopya | 7. tur | 6. tur | En yüksek kenara +3 kalıcı |

> ℹ️ **v0.6 Bug Fix:** Eşik kontrolü `t ==` yerine `t >=` ile çalışır. Geç alınan kartlar artık güçlenmeyi atlamıyor.
> ℹ️ Eşik sayacı, 2. kopyanın satın alındığı turdan itibaren başlar.

---

## 4. Kare Kart Sistemi (Catalyst / Eclipse) {#4}

Her oyuncunun elinde 3 adet kare kart bulunur: kişisel destesinden 2 kart, map destesinden 1 kart.

> ⚠️ Kare kartlar **YALNIZCA 1. tur** board'a konulabilir. 1. tur konulmazsa kalıcı olarak silinir.

### 4.1 Catalyst

| Özellik | Açıklama |
|---|---|
| Kopya eşiği | 2. kopya: 4. tur → 3. tur \| 3. kopya: 7. tur → 6. tur |
| Combo bonusu | Tüm combo puanları ×2 olur |
| Süre | Kalıcı — kaldırılamaz |

### 4.2 Eclipse

| Özellik | Açıklama |
|---|---|
| Board gizleme | Kendi board'un diğer oyuncular tarafından görünmez olur |
| Eclipse pasifleri | Bazı kartlar Eclipse aktifken ek bonus üretir |
| Süre | Kalıcı — kaldırılamaz |

---

## 5. Board ve Hex Grid {#5}

### 5.1 Yapı
Board yarıçap-2 altıgen griddir **(19 hex hücre)**. Her oyuncunun kendi bağımsız board kopyası vardır. Aynı koordinattaki kartlar combat yapar.

### 5.2 Koordinat Sistemi
Axial koordinat sistemi (q, r). Merkez (0,0). Hex yönleri: K, KD, GD, G, GB, KB — 0-5 indeks, saat yönünde.

### 5.3 Kare Hücre
Board'daki 1 adet kare hücre yalnızca Catalyst veya Eclipse için ayrılmıştır. Normal kartlar bu hücreye konamaz.

---

## 6. Tur Yapısı {#6}

| Faz | İçerik |
|---|---|
| **1. Hazırlama** | Market'ten kart satın al. Kartları board'a yerleştir veya taşı. Kare kartlar (yalnızca 1. tur). |
| **2. Alan Etkisi** | Komşu kartların grup alan etkileri snapshot bazlı hesaplanır ve uygulanır. |
| **3. Combat** | 6 kenar eş zamanlı çözülür. Kill ve combo puanları hesaplanır. |
| **4. Hasar** | Turu kaybeden oyuncu can kaybeder. Beraberlikte kimse can kaybetmez, +1 altın. |
| **5. Gelir** | Sabit gelir + faiz alınır. Pasif ekonomi efektleri uygulanır. |

> ℹ️ Alan etkisi her zaman combat öncesinde, snapshot üzerinden hesaplanır.

---

## 7. Alan Etkisi Sistemi {#7}

Bir kartın dominant grup özelliği komşu hücreli kartları etkiler. Etki o turun snapshot'ı üzerinden, temastan önce uygulanır.

| Grup | Alan Etkisi | Hedef | Açıklama |
|---|---|---|---|
| VARLIK | Baskı: En yüksek VARLIK statı −1 | Komşu rakip kart | Fiziksel varlık çevresini ezer |
| ZİHİN | Nötr: Grup avantajı bu tur çalışmaz | Komşu rakip kart | Zihin rakibin avantajını okur |
| BAĞLANTI | +1 Uyum yayar | Komşu dost kart | Bağlantı kendi ağını güçlendirir |

> ℹ️ Combat sırası: Alan etkisi (snapshot) → Temas → Puan hesabı

---

## 8. Combat Sistemi {#8}

### 8.1 Kenar Çarpışması

Bir hex kartın 6 kenarı, aynı anda kendi yönlerindeki koordinattaki rakip kartla karşılışır. Her kenar çarpışması:

1. Yüksek değer kazanır.
2. Kazanan grubun kenarı rakibin o gruptaki kenarını yeniyorsa **+1 grup avantajı bonusu** uygulanır.
3. Combo bonusu varsa o yönde uygulanır.
4. Kaybeden tarafın o kenarın değeri 1 azalır (sıfıra düşebilir).

### 8.2 Kart Yok Edilmesi

Bir grubun board'daki karta ait tüm kenarları sıfırlanırsa kart board'dan kaldırılır. Kısmi kayıplar kartı yok etmez.

> ℹ️ **v0.6 Bug Fix:** Yok edilme için **en az 2 stata sahip** bir grubun tamamının sıfırlanması gerekir. Tek-stat gruba sahip kartlar (101 kartın 66'sı) artık ilk combat kaybında anında yok olmuyor.

### 8.3 Kill Puanı

| Olay | Puan |
|---|---|
| Rakip kart yok edildi | **+8 puan** (kill sahibine) |

### 8.4 Grup Avantaj Matrisi

| Saldıran Grup | → | Savunan Grup | Bonus |
|---|---|---|---|
| VARLIK | ⇒ | BAĞLANTI | +1 combat |
| ZİHİN | ⇒ | VARLIK | +1 combat |
| BAĞLANTI | ⇒ | ZİHİN | +1 combat |

---

## 9. Combo Sistemi {#9}

### 9.1 Eşleşme Koşulu

Komşu iki dost kartın **dominant grupları aynıysa** eşleşme gerçekleşir.

> ⭐ **v0.6:** Combo koşulu kenar bazlı eşleşmeden **kart-grup bazlı** eşleşmeye değiştirildi. İki komşu kartın dominant grubu aynıysa combo tetiklenir — uygulamada çok daha tutarlı ve işlevsel.

**Örnek:** A kart dominant grubu VARLIK, B kart dominant grubu VARLIK → eşleşme.

### 9.2 Eşleşme Bonusu

| Bonus Türü | Değer |
|---|---|
| Puan bonusu | +1 puan (o tur için, eşleşen çift başına) |
| Combat bonusu | +1 combat bonusu (her iki karta, karşılıklı kenarlara) |

### 9.3 Catalyst Etkisi

Catalyst kare kartı aktifken tüm combo puanları **×2** olur.

---

## 10. Hasar ve Can Sistemi {#10}

### 10.1 Başlangıç Canı: 150

### 10.2 Hasar Formülü

```
HASAR = |Kazanan Puanı − Kaybeden Puanı| + ⌊Canlı Kart Sayısı / 2⌋
```

> ℹ️ **v0.6:** Rarity hasar bonusu (◆◆◆◆×2, ◆◆◆◆◆×3) kaldırıldı. Snowball etkisi azaltıldı; alive_count yarıya indirildi. Nadir kartın avantajı ham güçte korundu.

### 10.3 Can Bonusları

| Koşul | Bonus |
|---|---|
| HP < 75 | +1 altın (tur geliri ekstrası) |
| HP < 45 | +3 altın (tur geliri ekstrası) |
| Beraberlik | Her iki oyuncuya +1 altın, can kaybı yok |

---

## 11. Ekonomi Sistemi {#11}

| Gelir Türü | Değer |
|---|---|
| Sabit tur geliri | +3 altın |
| Faiz | Her 10 altın için +1 (maks +5) |
| Win streak bonusu | Her 3 ardışık kazanç için +1 altın |
| HP cezası bonusu | HP < 75 → +1 \| HP < 45 → +3 |
| Beraberlik | +1 altın (her iki oyuncuya) |
| Market yenileme | −2 altın |

### 11.1 Kart Maliyetleri

| Nadirlik | Maliyet | Not |
|---|---|---|
| ◆ Yaygın | 1 altın | — |
| ◆◆ Nadir | 2 altın | — |
| ◆◆◆ Epik | 3 altın | — |
| ◆◆◆◆ Efsanevi | **8 altın** | v0.6: 4→8 |
| ◆◆◆◆◆ Tanrısal | **10 altın** | v0.6: 5→10 |

> ℹ️ Ekonomist stratejisi: faiz geliri ×1.5 bonus alır (maks +8). Altın biriktirildiğinde geç oyun güçlü ◆◆◆◆ kartlarına erişim sağlar.

---

## 12. Puan ve Eşleştirme {#12}

### 12.1 Puan Bileşenleri

| Kaynak | Puan |
|---|---|
| Kill (rakip kart yok etme) | +8 puan |
| Combo eşleşmesi (dost komşu, aynı dominant grup) | +1 puan/eşleşme + combat bonusu |
| Grup sinerji bonusu | 3 kart→+1, 5 kart→+2, 8+ kart→+3 **(toplam max: 4)** |
| Catalyst aktifken combo | Tüm combo puanları ×2 |

### 12.2 Swiss Eşleştirme

Oyuncular her tur canlarına göre sıralanır ve en yakın HP'li çiftler eşleştirilir. Eşit HP gruplarında rastgele karıştırma uygulanır — aynı çift arka arkaya karşılaşmaz.

---

## 13. Map Olayları {#13}

Her maç başında oyuncular bir olay öğrenir. Olay o maç boyunca aktiftir.

| Olay | Etki | Stratejik Önemi |
|---|---|---|
| **Zaman Döngüsü** | Tüm kartların kopya güçlenme sayacı o tur +1 ilerler | Evrimci avantajlı |
| **Kaos Dalgası** | Tüm board'lardaki kartlar rastgele 1 pozisyon döner (Mitoloji 4 kart engeller) | Rotasyon planlaması zorlaşır |
| **Evrensel Çekim** | O tur tüm alan etkileri 2 hex'e uzanır (normal: 1) | BAĞLANTI kartları güçlü olur |
| **Büyük Sıfırlama** | Market ücretsiz yenilenir; o tur kart alınmazsa +3 altın bonus | Fırsat vs sabır testi |

---

## 14. Threshold Sistemi {#14}

Belirli sayıda aynı kategoriden kart sahada bulunduğunda küçük bonuslar devreye girer.

| Kategori | 2 Kart Bonusu | 4 Kart Bonusu |
|---|---|---|
| Mitoloji & Tanrılar | Sahada Mitoloji kart varken +1 Prestij | Beraberlikte +1 ekstra puan |
| Sanat & Kültür | Reroll'da 1 kart sonraki tura saklanabilir | Yok edilen kart kopya sayacı 1'den başlar |
| Doğa & Canlılar | Her tur +1 Uyum biriktirir (maks +2) | Kopya güçlenme eşiği −1 tur |
| Kozmos | Tüm Kozmos kartlara +1 Boyut | Singularity beraberliğinde Kozmos kazanır |
| Bilim | Aktif ZİHİN alan etkisi +1 ek | Her 5 turda rakip kartın 1 statı görülür |
| Tarih & Medeniyetler | Market yenileme 1 altın indirimli | Yok edilen Tarih kartı 1 altın bırakır |

> ℹ️ Threshold bonusları oyunun seyrini belirlemez — küçük konfor bonuslarıdır.

---

## 15. Strateji Yolları (v0.6 Dengeli) {#15}

700+ simülasyona dayalı güncel kazanma oranları:

| Strateji | Kazanma % | Ort. Hasar | Profil |
|---|---|---|---|
| ⏩ Tempo | **%30.6** | 229.8 | Geç oyun lider — dengeleme devam ediyor |
| ⚔ Savaşçı | %17.4 | 169.3 | Stabil, güçlü |
| 🧬 Evrimci | %12.0 | 163.6 | ✅ v0.6'da güçlendirildi |
| 💰 Ekonomist | %11.9 | 102.9 | ✅ v0.6'da güçlendirildi |
| 🔗 İnşacı | %9.1 | 215.9 | ✅ Combo düzeltmesi ile oyuna girdi |
| ⚖ Balansçı | %8.4 | 144.0 | Dengeli |
| 💎 Nadir-avcı | %6.4 | 101.8 | Artık geç oyun stratejisi |
| 🎲 Rastgele | %4.1 | 125.2 | Referans |

### ⚔ Savaşçı
Yüksek güçlü kartları toplayarak kill puanı biriktirmeyi hedefler. Her kill +8 puan.
**Önerilen kartlar:** Ragnarök, World War II, Sparta, Mantis Shrimp, Komodo Dragon, Kraken

### 🔗 İnşacı
Komşu kartlar arasında aynı dominant gruptan eşleşmeler kurarak combo puanı biriktirir. Catalyst ile birlikte oynanırsa combo puanları ×2.
**Önerilen kartlar:** Coral Reef, Rainforest, Bioluminescence, Silk Road, Impressionism, Jazz

### 🧬 Evrimci
Aynı kartın kopyalarını toplayarak kopya güçlenme eşiklerine ulaşır. Kopya eşiğine yakın kartlara öncelik verilir.
**Önerilen kartlar:** Coelacanth, Fungus, Baobab, Charles Darwin, DNA, Tardigrade

### 💰 Ekonomist
Altın biriktirerek faiz geliri elde eder (×1.5 bonus). Biriken altın 20+ olduğunda ◆◆◆ kartlara, 30+ olduğunda ◆◆◆◆ kartlara geçiş yapar.
**Önerilen kartlar:** Midas, Exoplanet, Algorithm, Industrial Revolution, Printing Press, Babylon

### ⏩ Tempo
Güçlü ◆◆◆ kartları erken alarak baskı kurar. En güçlü kartları merkeze, zayıf kartları kenara yerleştirir.
**Önerilen kartlar:** Yüksek total_power'a sahip orta nadirlikteki kartlar.

### 💎 Nadir-avcı
◆◆◆◆ ve ◆◆◆◆◆ kartları hedefler. Yeni maliyetlerle (8/10 altın) geç oyun stratejisine dönüştü — ilk 3 turda ◆◆◆ fallback kullanır.
**Önerilen kartlar:** Albert Einstein, E=mc², Black Hole, Coelacanth, Black Death, Mantis Shrimp

---

## 16. Kart Havuzu {#16}

### 16.1 Kategori Dağılımı

| Kategori | Kart Sayısı |
|---|---|
| Mitoloji & Tanrılar | 17 |
| Sanat & Kültür | 17 |
| Doğa & Canlılar | 17 |
| Kozmos | 17 |
| Bilim | 17 |
| Tarih & Medeniyetler | 16 |
| **TOPLAM** | **101** |

### 16.2 Nadirlik Dağılımı

| Nadirlik | Kart Sayısı | Ort. Total Güç |
|---|---|---|
| ◆ Yaygın | 35 | 29.0 |
| ◆◆ Nadir | 28 | 32.8 |
| ◆◆◆ Epik | 20 | 38.0 |
| ◆◆◆◆ Efsanevi | 12 | 44.3 |
| ◆◆◆◆◆ Tanrısal | 6 | 49.3 |
| **TOPLAM** | **101** | — |

---

## 17. Örnek Oyun Turu {#17}

8 oyunculu bir lobide tipik bir oyunun tur tur özeti. **Oyuncu: Evrimci stratejisi.**

---

### 🎴 Lobi — Maç Başlangıcı

Her oyuncu 3 rastgele ◆ kart aldı.
- **Evrimci'nin eli:** Platypus (◆), Graffiti (◆), Shadow Puppetry (◆)
- **Karar:** 3 kartı da board'a koy — ilk turdan puan üret.

---

### Tur 1 — İlk Combat

| | Evrimci | Rakip (Savaşçı) |
|---|---|---|
| Gelir | +3 altın (toplam: 3) | +3 altın |
| Market alımı | Platypus görüldü → **2. kopya!** 1 altın harcandı | Minotaur aldı (1 altın) |
| Board | 3 kart (Platypus ×2, Graffiti) | 4 kart |
| Sinerji | +3 puan | +3 puan |
| **Sonuç** | **Beraberlik** — +1 altın her ikisine | Beraberlik |

---

### Tur 2 — Kopya Takibi

| | Evrimci | Rakip (Tempo) |
|---|---|---|
| Gelir | +3 altın (toplam: 4) | +3 altın |
| Market alımı | Platypus yok — Axolotl (◆◆, 2 altın) aldı | Komodo Dragon (◆◆◆, 3 altın) aldı |
| Board | 4 kart | 6 kart, güçlü merkez |
| Combat | Kill yok, combo: +1 puan | Kill: 1 (+8 puan) |
| Hasar alındı | Tempo kazandı → **−8 hasar** | — |
| **HP** | **Evrimci: 142** | Tempo: 150 |

---

### Tur 3 — Ekonomi Büyüyor

| | Evrimci | Rakip (Ekonomist) |
|---|---|---|
| Gelir | +3 altın (toplam: 5) | +3 altın + ×1.5 faiz bonusu |
| Market alımı | Axolotl 2. kopya bulundu! Aldı (2 altın) | Altın biriktiriyor |
| Board | 5 kart | 4 kart |
| Combat | Kill: 1 (+8), Sinerji: +3 → **Evrimci kazandı** | Kill yok, Sinerji: +3 |
| Hasar verilen | 11−3 = 8 hasar | |
| **HP** | Evrimci: 142 | **Ekonomist: 142** |

---

### Tur 4 — 🔥 İlk Kopya Güçlenmesi

- **Platypus ×2:** copy_turns >= 4 → en yüksek kenara **+2 kalıcı**
- **Axolotl ×2:** copy_turns >= 4 → en yüksek kenara **+2 kalıcı**
- Market alımı: DNA (◆◆◆, 3 altın) — yeni kopya yolu açıldı
- Board: 6 kart, güçlenmiş Platypus ve Axolotl
- Combat: Kill: 2 (+16), Combo: 2 (+2), Sinerji: +4 → **22 puan**
- Hasar: 22−6 = 16 + 3 canlı kart = **19 hasar**
- **HP: Evrimci 142 ✅ | Rakip 131**

---

### Tur 7 — Geç Oyun ve 3. Kopya Eşiği

- 6 oyuncu hayatta (2 oyuncu erken elendi)
- **Platypus ×3:** copy_turns >= 7 → en yüksek kenara **+3 kalıcı**
- Board: 8 kart, Platypus dominant
- Tempo rakibi: 12 kart, ◆◆◆ ağırlıklı — çok güçlü
- Combat: Kill: 1 (+8), Combo: 4 (+4), Sinerji: +4 = 16 puan
- Hasar alındı: Tempo kazandı → **−10 hasar**
- **HP: Evrimci 110 | Tempo 135**

---

### Tur 10–15 — Final

Evrimci 3 kopya güçlenmesiyle birikimli avantaj kazandı. Ekonomist geç oyunda ◆◆◆◆ kartlara erişip güçlendi. Tempo baskısını korusa da 150 HP dengesi sayesinde oyun uzadı.

**Final 3:** Evrimci, Tempo, Savaşçı — son 2 tur kazananı belirledi.

> ℹ️ Bu örnek oyun v0.6'nın temel dinamiklerini göstermektedir: erken tur başlangıç elleri, kopya güçlenme eşikleri ve ekonomist'in altın biriktirme → geç oyun geçiş döngüsü.

---

## 18. Simülasyon Verileri ve Denge Notu {#18}

`autochess_sim_v06.py` ile 700 oyunluk (8 oyuncu/oyun) simülasyon sonuçları:

| Strateji | Kazanma % | Ort. Hasar | Ort. Kill | Ort. HP |
|---|---|---|---|---|
| Tempo | **30.6%** | 229.8 | 24.5 | 17.6 |
| Savaşçı | 17.4% | 169.3 | 20.9 | 5.3 |
| Evrimci | 12.0% | 163.6 | 19.7 | 4.2 |
| Ekonomist | 11.9% | 102.9 | 16.5 | 2.6 |
| İnşacı | 9.1% | 215.9 | 18.2 | 4.5 |
| Balansçı | 8.4% | 144.0 | 19.0 | 2.4 |
| Nadir-avcı | 6.4% | 101.8 | 15.9 | 2.0 |
| Rastgele | 4.1% | 125.2 | 14.4 | 1.2 |

| Oyun Süresi | Değer |
|---|---|
| Ortalama tur | 26.5 |
| En kısa oyun | 20 tur |
| En uzun oyun | 33 tur |

### ⚠️ Denge Notu — Sonraki Hedef

Tempo stratejisi %30.6 ile hâlâ dominant. Orta nadir (◆◆◆) kartların erken oyun ham gücü dengelenmelidir.

**Önerilen sonraki adımlar:**
- Tempo stratejisine özel kısıtlama: merkez hücre bonusunun azaltılması
- ◆◆◆ kart maliyetinin 3→4 altına çıkarılması (test edilmeli)
- İnşacı'nın combo hasarının kill'e yaklaştırılması için combo başına +1.5 puan

---

## 19. Hızlı Başvuru {#19}

| Kural | Değer |
|---|---|
| Başlangıç canı | 150 |
| Başlangıç kartları (lobi) | 3 adet ◆ (Yaygın) |
| Kill puanı | +8 puan |
| Combo eşleşmesi (aynı dominant grup) | +1 puan + +1 combat bonusu |
| Grup avantajı | +1 combat bonusu |
| Catalyst combo bonusu | ×2 tüm combo puanları |
| Grup sinerji bonusu (maks) | Max +4 (3 kart→+1, 5→+2, 8+→+3) |
| 2. kopya eşiği (normal / Catalyst) | 4. tur / 3. tur (t >= eşik) |
| 3. kopya eşiği (normal / Catalyst) | 7. tur / 6. tur (t >= eşik) |
| 2. kopya güçlenme | En yüksek kenara +2 kalıcı |
| 3. kopya güçlenme | En yüksek kenara +3 kalıcı |
| Kart yok edilme koşulu | Min 2 stata sahip grup tamamen sıfırlandığında |
| Kare kart konulma zamanı | Yalnızca 1. tur |
| Market yenileme ücreti | 2 altın |
| Sabit tur geliri | 3 altın |
| Faiz | Her 10 altın için +1 (maks +5) |
| Ekonomist faiz bonusu | ×1.5 (maks +8) |
| Beraberlik | Can kaybı yok \| +1 altın her iki oyuncuya |
| Hasar formülü | \|Kazanan − Kaybeden\| + ⌊Canlı Kart / 2⌋ |
| Her oyuncuya market görünümü | Bağımsız (oyuncular aynı kartları görmez) |
| Alan etkisi sırası | Snapshot → Alan etkisi → Temas → Puan |
| Oyun sonu güvencesi | 50 tur limiti |

---

## 20. Değişiklik Geçmişi {#20}

| Versiyon | Değişiklikler |
|---|---|
| **v0.6** (Mart 2026) | Başlangıç elleri: her oyuncu 3×◆ kartla başlar. ◆◆◆◆ maliyet 8, ◆◆◆◆◆ maliyet 10. Rarity hasar bonusu kaldırıldı. Combo sistemi kart-grup bazlı. Sinerji maks +4. HP 150. Ekonomist ×1.5 faiz. Evrimci kopya öncelik skoru. 3 kritik bug düzeltildi. |
| **v0.5** (Mart 2026) | Kill puanı +8 sabit. Alan etkisi sistemi. Threshold sistemi. Lobi/deck building. Map olayları. |
| **v0.4** (Mart 2026) | Üçgen kartlar kaldırıldı. Kare hücre sistemi. Swiss eşleştirme. |
| **v0.3** | 12 stat sistemi, 3 grup matrisi. Açık board sistemi. |
| **v0.2** | İlk lobi ve kart havuzu taslağı. |

---

*AUTOCHESS HYBRID GDD v0.6 · Tüm haklar saklıdır.*
