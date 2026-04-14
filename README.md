# 🎮 Autochess Hybrid - Simulation Engine

## 📖 Proje Tanımı

Autochess Hybrid, hex-grid tabanlı otomatik savaş (autochess) oyun motoru simülasyonudur. 8 oyunculu lobide 101 kartlık havuzdan stratejik kart seçimleri yapılır ve otomatik combatlar çözülür.

## 📁 Dizin Yapısı

```
hybrid/
├── engine_core/          # Oyun motoru çekirdeği
│   ├── autochess_sim_v06.py
│   └── game_factory.py   # Game initialization (NEW)
├── gameplay/             # Oyun mekaniği ve stratejiler
├── scenes/               # Scene-based architecture (NEW)
│   ├── lobby_scene.py
│   ├── game_loop_scene.py  # Turn orchestration (NEW)
│   ├── shop_scene.py
│   ├── combat_scene.py
│   └── game_over_scene.py  # Winner display (NEW)
├── ui/                   # UI components (NEW)
│   ├── hud_renderer.py   # HUD rendering utilities
│   └── hand_panel.py     # Hand card display
├── core/                 # Core game state
│   ├── core_game_state.py
│   └── input_state.py
├── assets/               # Oyun varlıkları
│   └── data/
│       ├── cards.json
│       └── passives.txt
├── scripts/              # Yardımcı scriptler
│   ├── simulation/       # Simülasyon scriptleri
│   ├── translation/      # Çeviri araçları
│   ├── validation/       # Doğrulama scriptleri
│   └── refactoring/      # Refactoring araçları
├── tools/                # Geliştirici araçları
├── tests/                # Test suite
│   ├── unit/            # Birim testleri
│   ├── integration/     # Entegrasyon testleri
│   └── qa/              # QA testleri
├── docs/                 # Dokümantasyon
│   ├── design/          # Tasarım dokümanları
│   ├── reports/         # Raporlar (QA, debug, refactoring)
│   ├── kpi/             # KPI raporları
│   └── guides/          # Kullanım kılavuzları
├── output/               # Simülasyon çıktıları
│   ├── logs/            # Log dosyaları
│   ├── results/         # Simülasyon sonuçları
│   └── reports/         # Otomatik raporlar
├── .kiro/                # Kiro specs and configuration
│   └── specs/
│       └── run-game-scene-integration/  # Migration spec
├── main.py               # Entry point (scene-based)
├── run_game.py           # Legacy entry point (deprecated)
├── MIGRATION.md          # Migration guide (NEW)
└── external/             # Harici projeler
    └── unity_tutorial/
```

## 🚀 Kurulum

### Gereksinimler
- Python 3.14+
- pip (Python paket yöneticisi)

### Adımlar

```bash
# Virtual environment oluştur
python -m venv .venv

# Aktif et (Windows)
.venv\Scripts\activate

# Aktif et (Linux/Mac)
source .venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

## 💻 Kullanım

### Oyunu Çalıştırma

```bash
# Scene-based architecture (önerilen)
python main.py

# Legacy sistem (deprecated)
python run_game.py
```

**Kontroller:**
- `SPACE` - Tur ilerlet
- `F` - Hızlı mod (otomatik tur)
- `1-8` - Oyuncular arası geçiş
- `S` - Shop ekranını aç
- `R` - Kartı döndür (seçili kart varken)
- `ESC` - İptal / Çıkış

### Simülasyon Çalıştırma

```bash
# 500 oyunluk simülasyon
python scripts/simulation/run_simulation.py

# Benchmark testi
python scripts/simulation/bench_sim.py

# Batch analizi
python scripts/simulation/analyze_all_batches.py
```

### Test Çalıştırma

```bash
# Tüm testleri çalıştır
pytest

# Verbose mode
pytest -v

# Belirli test dosyası
pytest tests/unit/test_simulation.py

# Coverage raporu
pytest --cov=engine_core tests/
```

## 📚 Dokümantasyon

- **Game Design Document:** `docs/design/Autochess_Hybrid_GDD_v06.md`
- **Migration Guide:** `MIGRATION.md` - Scene-based architecture migration
- **Spec Files:** `.kiro/specs/run-game-scene-integration/`
  - `requirements.md` - Functional requirements (30 requirements)
  - `design.md` - Architecture design and gap analysis
  - `tasks.md` - Implementation tasks (39 tasks across 4 phases)
- **QA Reports:** `docs/reports/qa/`
- **KPI Reports:** `docs/kpi/`
- **Kullanım Kılavuzu:** `docs/guides/CURSOR_BASLANGIC.md`

## 🏗️ Mimari

### Scene-Based Architecture (NEW)

Oyun, modüler scene-based mimariye geçiş yapıyor. Her scene belirli bir oyun fazından sorumludur:

```
SceneManager
├── LobbyScene          # Strateji seçimi
├── GameLoopScene       # Tur orkestrasyon merkezi (YENİ)
├── ShopScene           # Kart satın alma
├── CombatScene         # Hex board'da kart yerleştirme
└── GameOverScene       # Kazanan gösterimi ve yeniden başlatma (YENİ)
```

**Scene Geçiş Akışı:**
```
Lobby → GameLoop → Shop → Combat → GameLoop → GameOver
  ↑                                              ↓
  └──────────────── Restart ────────────────────┘
```

**Detaylı bilgi için:** `MIGRATION.md`

### Legacy System

Eski monolitik `run_game.py` sistemi hala kullanılabilir ancak deprecated durumda:

```bash
# Legacy sistem (deprecated)
python run_game.py

# Yeni scene-based sistem (önerilen)
python main.py  # USE_SCENE_ARCHITECTURE=True
```

## 🎯 Özellikler

- ✅ 8 oyunculu autochess simülasyonu
- ✅ 101 kart havuzu
- ✅ Hex-grid tabanlı combat sistemi
- ✅ Pasif yetenek sistemi
- ✅ AI stratejileri
- ✅ KPI tracking ve analiz
- ✅ Kapsamlı test suite
- 🔄 Scene-based architecture (migration in progress)

## 🔧 Geliştirme

### Import Path'leri

Tüm import'lar yeni dizin yapısına göre güncellenmiştir:

```python
# Engine core
from engine_core.autochess_sim_v06 import AutochessGame

# Assets
cards_path = "assets/data/cards.json"
passives_path = "assets/data/passives.txt"
```

### Yeni Özellik Ekleme

1. Kodu `engine_core/` veya `gameplay/` altına ekle
2. Testleri `tests/unit/` veya `tests/integration/` altına ekle
3. Dokümantasyonu `docs/` altında güncelle
4. `pytest` ile testleri çalıştır

## 📊 Versiyon

- **Engine:** v0.6
- **Python:** 3.14+
- **Son Güncelleme:** Mart 2026
- **Reorganizasyon:** 28 Mart 2026

## 📝 Lisans

Tüm haklar saklıdır.

## 🤝 Katkıda Bulunma

1. Yeni özellikler için önce test yaz
2. Code style: PEP 8
3. Commit mesajları: Türkçe veya İngilizce
4. Pull request öncesi tüm testlerin geçtiğinden emin ol

## 📧 İletişim

Sorularınız için issue açabilirsiniz.
