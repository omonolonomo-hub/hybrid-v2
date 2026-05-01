# 🎨 Lobi Satır Arka Plan Düzeltmesi

## 🐛 Sorun

Lobi ekranındaki AI ve human satırlarının arka plan şeritleri orantısızdı:
- Yazılar şeridin üst kısmında kalıyordu
- Şerit yüksekliği dinamik olarak hesaplanıyordu (`row_height * 0.6`)
- Yazılar ile şerit arasında dikey hizalama yoktu

## ✅ Çözüm

### **1. AI Satırları**

**Önceki Kod:**
```python
row_rect = pygame.Rect(row_start_x, row_y, content_width, int(row_height * 0.6))
pygame.draw.rect(surface, (20, 25, 35, 80), row_rect, border_radius=6)

# Yazılar row_y pozisyonunda (şeridin üstünde)
num_surf = self._font_row.render(ai_num, True, GRAY)
surface.blit(num_surf, (row_start_x + 20, row_y))
```

**Yeni Kod:**
```python
# Sabit yükseklik ve yazıları ortalayacak pozisyon
row_bg_height = 40  # Sabit yükseklik
row_bg_y = row_y - 4  # Yazıların biraz üstünden başla
row_rect = pygame.Rect(row_start_x, row_bg_y, content_width, row_bg_height)
pygame.draw.rect(surface, (20, 25, 35, 80), row_rect, border_radius=6)

# Yazılar row_y pozisyonunda (şeridin ortasında)
num_surf = self._font_row.render(ai_num, True, GRAY)
surface.blit(num_surf, (row_start_x + 20, row_y))
```

**Değişiklikler:**
- ✅ Şerit yüksekliği: `row_height * 0.6` → `40px` (sabit)
- ✅ Şerit Y pozisyonu: `row_y` → `row_y - 4` (yazıların üstünde)
- ✅ Yazılar şeridin ortasında konumlanıyor

### **2. Human Satırı**

**Önceki Kod:**
```python
highlight_rect = pygame.Rect(row_start_x, human_y, content_width, int(row_height * 0.6))

# Yazılar human_y pozisyonunda (şeridin üstünde)
arrow_surf = self._font_row.render("►", True, CYAN)
surface.blit(arrow_surf, (row_start_x + 20, human_y))
```

**Yeni Kod:**
```python
# Sabit yükseklik ve yazıları ortalayacak pozisyon
human_bg_height = 44  # AI satırlarından biraz daha yüksek
human_bg_y = human_y - 6  # Yazıların biraz üstünden başla
highlight_rect = pygame.Rect(row_start_x, human_bg_y, content_width, human_bg_height)

# Yazılar human_y pozisyonunda (şeridin ortasında)
arrow_surf = self._font_row.render("►", True, CYAN)
surface.blit(arrow_surf, (row_start_x + 20, human_y))
```

**Değişiklikler:**
- ✅ Şerit yüksekliği: `row_height * 0.6` → `44px` (sabit, AI'dan biraz daha yüksek)
- ✅ Şerit Y pozisyonu: `human_y` → `human_y - 6` (yazıların üstünde)
- ✅ Human satırı AI satırlarından biraz daha belirgin

## 📊 Karşılaştırma

### **Önceki Durum:**
```
┌─────────────────────────────────────┐
│ AI 1 — WARRIOR          [icon]      │  ← Yazı şeridin üstünde
└─────────────────────────────────────┘
     ↑ Şerit çok kısa ve yazı üstte
```

### **Yeni Durum:**
```
┌─────────────────────────────────────┐
│                                     │
│   AI 1 — WARRIOR        [icon]     │  ← Yazı şeridin ortasında
│                                     │
└─────────────────────────────────────┘
     ↑ Şerit yeterli yükseklikte, yazı ortalı
```

## 🎯 Sonuç

### **AI Satırları:**
- Şerit yüksekliği: **40px** (sabit)
- Yazı pozisyonu: Şeridin **ortasında** (Y - 4px offset)
- Görünüm: **Dengeli ve orantılı**

### **Human Satırı:**
- Şerit yüksekliği: **44px** (AI'dan biraz daha yüksek)
- Yazı pozisyonu: Şeridin **ortasında** (Y - 6px offset)
- Görünüm: **Daha belirgin ve vurgulu**

## 📝 Teknik Detaylar

### **Neden Sabit Yükseklik?**
- Dinamik hesaplama (`row_height * 0.6`) ekran boyutuna göre değişiyor
- Sabit değer her zaman tutarlı görünüm sağlıyor
- Font boyutu sabit olduğu için şerit de sabit olmalı

### **Neden Negatif Offset?**
- Yazılar `row_y` pozisyonunda render ediliyor
- Şerit yazıların üstünden başlamalı (`row_y - offset`)
- Bu sayede yazılar şeridin ortasında kalıyor

### **Neden Human Satırı Daha Yüksek?**
- Human satırı oyuncunun kendi satırı (özel)
- Daha belirgin olması için biraz daha yüksek
- Glow efekti de daha fazla yer kaplıyor

## 🎨 Görsel Hiyerarşi

```
AI Satırları:
┌────────────────────────────────┐
│  AI 1 — WARRIOR      [icon]    │  40px yükseklik
└────────────────────────────────┘

Human Satırı:
┌────────────────────────────────┐
│                                │
│  ► SEN — HUMAN                 │  44px yükseklik (daha belirgin)
│                                │
└────────────────────────────────┘
```

---

**Güncelleme:** 2026-04-30
**Versiyon:** 1.2
**Durum:** ✅ Düzeltildi ve Test Edildi
