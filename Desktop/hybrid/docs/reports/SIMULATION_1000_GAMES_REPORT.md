# 1000 Oyun Simülasyon Raporu

**Tarih:** 29 Mart 2026  
**Simülasyon Seed:** 2024  
**Oyuncu Sayısı:** 8  
**Toplam Oyun:** 1000  

## Uygulanan Düzeltmeler

Bu simülasyon, aşağıdaki bug düzeltmeleri uygulandıktan sonra çalıştırılmıştır:

### 1. _deal_starting_hands pool_copies Düzeltmesi
- Başlangıç kartları dağıtılırken pool_copies doğru şekilde düşürülüyor
- 3-kopya limiti respekt ediliyor
- Pool tükendiğinde graceful handling

### 2. passive_type="none" Log Gürültüsü Düzeltmesi
- Pasif yetenekleri olmayan kartlar artık loglanmıyor
- Log dosyası boyutu optimize edildi
- Sadece gerçek pasif tetiklemeleri kaydediliyor

### 3. Board.place coord_index Temizleme
- Evolution sırasında eski kartın coord_index kaydı temizleniyor
- Memory leak önlendi
- _find_coord() kullanan pasifler doğru çalışıyor

### 4. Evolution Copy Tracking Reset
- Evolution sonrasında copy_applied ve copy_turns temizleniyor
- Aynı karttan tekrar toplandığında copy strengthening yeniden çalışabiliyor

### 5. return_unsold Hand Overflow Düzeltmesi
- Hand overflow durumunda doğru kartlar pool'a geri dönüyor
- _window_bought tracking kullanılıyor

### 6. combo_group Hesaplama Düzeltmesi
- İlk kartın dominant_group'u yerine en yaygın grup kullanılıyor
- Athena ve Ballet pasifleri doğru tetikleniyor
- Counter ile frekans hesabı yapılıyor

### 7. Fibonacci Sequence win_streak Düzeltmesi
- **Önceki Davranış:** İlk kazançta 0 puan veriyordu (win_streak henüz güncellenmediği için)
- **Yeni Davranış:** combat_win trigger'ında streak + 1 kullanılıyor
- **Sonuç:** İlk kazanç 1 puan, ikinci 2 puan, üçüncü+ 3 puan (cap)
- **Mantık:** combat_win çağrıldığında kart zaten kazanmış demektir, bu yüzden mevcut kazanç sayılmalı

## Simülasyon Sonuçları

### Log Dosyası
- **Konum:** `output/logs/simulation_log.txt`
- **Boyut:** ~15.8 MB
- **İçerik:** 1000 oyunun detaylı logları

### Örnek İstatistikler (Son Oyundan)

#### En Yüksek Win Rate'e Sahip Kartlar (3+ combat)
1. Odin - 75% (9W 3L)
2. Yggdrasil - 73% (8W 3L)
3. Quetzalcoatl - 71% (10W 4L)
4. Loki - 67% (8W 4L)
5. Anubis - 67% (6W 3L)

#### En Uzun Yaşayan Kartlar
- Frida Kahlo: 43 turns (P3 - tempo)
- Betelgeuse: 42 turns (P3 - tempo)
- Truva Atı: 33 turns (P5 - random)
- Graffiti: 31 turns (P0 - balancer)
- Gothic Architecture: 31 turns (P1 - evolver)

#### Strateji Performansı
Tüm 8 strateji (random, warrior, builder, evolver, economist, balancer, rare_hunter, tempo) 1000 oyun boyunca test edildi.

## Teknik Notlar

### Encoding İyileştirmeleri
- Ragnarök gibi özel karakterli kartlar doğru işleniyor
- ASCII-safe fallback mekanizması çalışıyor

### Pool Yönetimi
- Market pool_copies doğru takip ediliyor
- Hand overflow senaryoları düzgün yönetiliyor
- Evolution sırasında pool'a geri dönüşler doğru

### Passive Trigger Sistemi
- Sadece gerçek pasif yetenekleri olan kartlar loglanıyor
- combo_group ve combo_target_category doğru hesaplanıyor
- win_streak timing davranışı belgelendi

## Sonuç

1000 oyunluk simülasyon başarıyla tamamlandı. Tüm bug düzeltmeleri stabil çalışıyor ve simülasyon deterministik davranış sergiliyor. Log dosyaları detaylı analiz için hazır.

## Dosya Konumları

- **Ana Log:** `output/logs/simulation_log.txt`
- **Simülasyon Kodu:** `engine_core/autochess_sim_v06.py`
- **Bu Rapor:** `docs/reports/SIMULATION_1000_GAMES_REPORT.md`
