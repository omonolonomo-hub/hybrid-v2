"""
asset_loader.py
───────────────
Combat Scene + Shop için kart asset yükleyici.

Özellikler:
  - Her kart için ön yüz (_front.png) + arka yüz (_back.png) çifti
  - Türkçe karakter normalizasyonu ile fuzzy isim eşleştirme
  - Eksik yüz → procedural neon hex placeholder (pygame.Surface)
  - FlipAnimator: shop ve board için 3D kart çevirme animasyonu
  - on_enter() → tek seferlik pre-load, sonra cache'den okuma
  - on_exit() → clear() ile bellek temizleme

Kullanım:
    loader = AssetLoader(CARDS_DIR, target_size=(120, 120))
    loader.preload(card_names)                      # on_enter()'da

    faces = loader.get(card_name)                   # CardFaces nesnesi
    screen.blit(faces.front, rect)                  # ön yüz
    screen.blit(faces.back, rect)                   # arka yüz

    # Flip animasyonu (shop veya board):
    animator = FlipAnimator(duration=0.4)
    animator.start()
    surf = animator.get_surface(faces, dt)          # draw()'da her frame
"""

import os
import re
import math
import pygame
from dataclasses import dataclass
from typing import Optional


# ─── Kart Boyutu Sabiti ───────────────────────────────────────────────────────
#
# Board'daki kartlar için boyut (combat scene)
#   card_width  = 140px
#   card_height = 160px
#
# Shop'taki kartlar için daha büyük boyut
#   card_width  = 200px (shop'ta daha büyük)
#   card_height = 230px
#
CARD_SIZE: tuple = (140, 160)  # Default for board
SHOP_CARD_SIZE: tuple = (200, 230)  # Larger for shop


# ─── Veri Yapıları ────────────────────────────────────────────────────────────

@dataclass
class CardFaces:
    """Bir kartın ön ve arka yüzü."""
    front: pygame.Surface
    back:  pygame.Surface
    name:  str
    is_placeholder: bool = False


# ─── Türkçe Normalizasyon ─────────────────────────────────────────────────────

_TR_MAP = str.maketrans(
    "şŞğĞüÜöÖçÇıİ",
    "sSgGuUoOcCiI"
)

def _normalize(name: str) -> str:
    name = name.lower().translate(_TR_MAP)
    name = re.sub(r"[_\-\s]+", " ", name)
    return name.strip()


def _normalize_stem(filename: str) -> str:
    """
    'ates_ejderi_front.png' → 'ates ejderi'
    'ates_ejderi_back.png'  → 'ates ejderi'
    'ates_ejderi.png'       → 'ates ejderi'  (suffix yok → ön yüz kabul)
    """
    stem = os.path.splitext(filename)[0]
    stem = re.sub(r"[_\-\s]*(front|back)$", "", stem, flags=re.IGNORECASE)
    return _normalize(stem)


# ─── Neon Hex Placeholder ─────────────────────────────────────────────────────

def _make_neon_placeholder(size: tuple, card_name: str,
                            is_back: bool = False) -> pygame.Surface:
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    hue = sum(ord(c) for c in card_name) % 360
    if is_back:
        neon  = _hsv_to_rgb(hue, 0.4, 0.6)
        fill  = _hsv_to_rgb(hue, 0.3, 0.15)
        label = "?"
    else:
        neon  = _hsv_to_rgb(hue, 1.0, 1.0)
        fill  = _hsv_to_rgb(hue, 0.8, 0.25)
        label = _get_initials(card_name)

    cx, cy = w // 2, h // 2
    r = min(w, h) // 2 - 4

    corners = [(cx + r * math.cos(math.radians(60*i)),
                cy + r * math.sin(math.radians(60*i))) for i in range(6)]
    inner   = [(cx + (r-5) * math.cos(math.radians(60*i)),
                cy + (r-5) * math.sin(math.radians(60*i))) for i in range(6)]

    pygame.draw.polygon(surf, (*fill, 180), corners)
    pygame.draw.polygon(surf, (*neon, 255), corners, 2)
    pygame.draw.polygon(surf, (*neon,  80), inner,   1)

    if not pygame.font.get_init():
        pygame.font.init()
    try:
        font = pygame.font.SysFont("consolas", max(12, h // 5), bold=True)
    except Exception:
        font = pygame.font.Font(None, max(12, h // 5))

    txt = font.render(label, True, (*neon, 255))
    surf.blit(txt, txt.get_rect(center=(cx, cy)))
    return surf


def _hsv_to_rgb(h, s, v) -> tuple:
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    r, g, b = [(c,x,0),(x,c,0),(0,c,x),(0,x,c),(x,0,c),(c,0,x)][int(h/60)%6]
    return (int((r+m)*255), int((g+m)*255), int((b+m)*255))


def _get_initials(name: str) -> str:
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    return name[:2].upper() if name else "?"


# ─── AssetLoader ──────────────────────────────────────────────────────────────

class AssetLoader:
    """
    Parametreler
    ────────────
    cards_dir   : _front.png ve _back.png dosyalarının bulunduğu dizin
    target_size : (w, h) — tüm yüzler bu boyuta scale edilir
    """

    def __init__(self, cards_dir: str, target_size: tuple = CARD_SIZE):
        self.cards_dir   = cards_dir
        self.target_size = target_size

        self._cache:    dict[str, CardFaces] = {}
        # normalize(kart_adı) → {"front": path, "back": path}
        self._file_map: dict[str, dict]      = {}

        self._loaded_pairs:  list[str] = []
        self._partial_pairs: list[str] = []
        self._missing_pairs: list[str] = []
        self._scanned = False

    # ── Dizin Tarama ──────────────────────────────────────────────────────────

    def _scan_directory(self) -> None:
        if not os.path.isdir(self.cards_dir):
            print(f"[AssetLoader] UYARI: Dizin bulunamadı → {self.cards_dir}")
            self._scanned = True
            return

        for fname in os.listdir(self.cards_dir):
            if not fname.lower().endswith(".png"):
                continue

            lower = fname.lower()
            face  = "back" if "_back" in lower else "front"

            norm_key  = _normalize_stem(fname)
            full_path = os.path.join(self.cards_dir, fname)

            if norm_key not in self._file_map:
                self._file_map[norm_key] = {}
            self._file_map[norm_key][face] = full_path

        tam   = sum(1 for v in self._file_map.values() if len(v) == 2)
        eksik = len(self._file_map) - tam
        print(f"[AssetLoader] {len(self._file_map)} kart tarandı "
              f"({tam} tam çift, {eksik} eksik yüzlü).")
        self._scanned = True

    # ── Ana API ───────────────────────────────────────────────────────────────

    def preload(self, card_names: list[str]) -> None:
        """on_enter()'da çağrılır."""
        if not self._scanned:
            self._scan_directory()
        for name in card_names:
            norm = _normalize(name)
            if norm not in self._cache:
                self._cache[norm] = self._build_faces(name, norm)
        self.print_report()

    def get(self, card_name: str) -> CardFaces:
        """draw()'da çağrılır. Her zaman geçerli CardFaces döner."""
        norm = _normalize(card_name)
        if norm in self._cache:
            return self._cache[norm]
        if not self._scanned:
            self._scan_directory()
        faces = self._build_faces(card_name, norm)
        self._cache[norm] = faces
        return faces

    def clear(self) -> None:
        """on_exit()'te çağrılır."""
        self._cache.clear()
        self._loaded_pairs.clear()
        self._partial_pairs.clear()
        self._missing_pairs.clear()
        print("[AssetLoader] Cache temizlendi.")

    # ── Yükleme Mantığı ───────────────────────────────────────────────────────

    def _build_faces(self, original_name: str, norm: str) -> CardFaces:
        paths = self._file_map.get(norm) or self._partial_match(norm) or {}

        front = self._load_surface(paths.get("front"), original_name, is_back=False)
        back  = self._load_surface(paths.get("back"),  original_name, is_back=True)
        has_placeholder = not paths.get("front") or not paths.get("back")

        if paths.get("front") and paths.get("back"):
            self._loaded_pairs.append(original_name)
        elif paths.get("front") or paths.get("back"):
            self._partial_pairs.append(original_name)
        else:
            self._missing_pairs.append(original_name)

        return CardFaces(front=front, back=back,
                         name=original_name, is_placeholder=has_placeholder)

    def _load_surface(self, path: Optional[str], card_name: str,
                      is_back: bool) -> pygame.Surface:
        if path:
            try:
                surf = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(surf, self.target_size)
            except pygame.error as e:
                print(f"[AssetLoader] Yüklenemedi ({path}): {e}")
        return _make_neon_placeholder(self.target_size, card_name, is_back)

    def _partial_match(self, norm: str) -> Optional[dict]:
        for file_norm, paths in self._file_map.items():
            if norm in file_norm or file_norm in norm:
                return paths
        card_tokens = set(norm.split())
        best_score, best_paths = 0.0, None
        for file_norm, paths in self._file_map.items():
            if not card_tokens:
                continue
            overlap = len(card_tokens & set(file_norm.split())) / len(card_tokens)
            if overlap > best_score:
                best_score, best_paths = overlap, paths
        return best_paths if best_score >= 0.6 else None

    # ── Raporlama ─────────────────────────────────────────────────────────────

    def print_report(self) -> None:
        total = len(self._loaded_pairs) + len(self._partial_pairs) + len(self._missing_pairs)
        print(
            f"\n[AssetLoader] ─── Yükleme Raporu ───────────────────\n"
            f"  Toplam kart           : {total}\n"
            f"  ✓ Tam çift (ön + arka): {len(self._loaded_pairs)}\n"
            f"  ⚠ Eksik bir yüzü var : {len(self._partial_pairs)}\n"
            f"  ✗ Tam placeholder     : {len(self._missing_pairs)}\n"
        )
        if self._partial_pairs:
            print("  Eksik yüzü olanlar:")
            for n in self._partial_pairs:
                print(f"    ⚠ {n}")
        if self._missing_pairs:
            print("  Hiç asset bulunamayanlar:")
            for n in self._missing_pairs:
                print(f"    ✗ {n}")
        print("[AssetLoader] ──────────────────────────────────────\n")

    def get_missing(self) -> list[str]:
        return list(self._missing_pairs + self._partial_pairs)

    def is_fully_loaded(self) -> bool:
        return not self._partial_pairs and not self._missing_pairs


# ─── FlipAnimator ─────────────────────────────────────────────────────────────

class FlipAnimator:
    """
    Kart çevirme animasyonu — shop ve combat board için.

    3D illüzyonu: kart önce yatay küçülür (ön yüz kapanır),
    sonra ters yönde büyür (arka yüz açılır).

    Kullanım:
        animator = FlipAnimator(duration=0.4)
        animator.start()

        # draw() içinde her frame:
        surf = animator.get_surface(faces, dt)
        screen.blit(surf, rect.topleft)
    """

    def __init__(self, duration: float = 0.4):
        self.duration      = duration
        self._progress     = 0.0
        self._active       = False
        self._showing_back = False

    def start(self) -> None:
        """Yeni flip başlatır. Zaten aktifse sıfırdan başlar."""
        self._progress     = 0.0
        self._active       = True
        self._showing_back = False

    def reset(self) -> None:
        """Animasyonu iptal eder, ön yüze döner."""
        self._progress     = 0.0
        self._active       = False
        self._showing_back = False

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def showing_back(self) -> bool:
        return self._showing_back

    def get_surface(self, faces: CardFaces, dt: float) -> pygame.Surface:
        """
        Her frame çağrılır.

        dt    : geçen süre saniye cinsinden (clock.tick / 1000.0)
        faces : AssetLoader.get() sonucu
        """
        if not self._active:
            return faces.back if self._showing_back else faces.front

        self._progress = min(1.0, self._progress + dt / self.duration)

        # İlk yarı → ön yüz daralır  (scale_x: 1.0 → 0.0)
        # İkinci yarı → arka yüz açılır (scale_x: 0.0 → 1.0)
        if self._progress < 0.5:
            scale_x = 1.0 - (self._progress / 0.5)
            source  = faces.front
            self._showing_back = False
        else:
            scale_x = (self._progress - 0.5) / 0.5
            source  = faces.back
            self._showing_back = True

        if self._progress >= 1.0:
            self._active = False
            return faces.back

        w, h  = source.get_size()
        new_w = max(1, int(w * scale_x))        # sıfıra bölme önlemi
        scaled = pygame.transform.scale(source, (new_w, h))

        # Orijinal boyutta canvas, ortaya yerleştir → rect sabit kalır
        result = pygame.Surface((w, h), pygame.SRCALPHA)
        result.fill((0, 0, 0, 0))
        result.blit(scaled, ((w - new_w) // 2, 0))
        return result

    def get_progress(self) -> float:
        """0.0 → 1.0"""
        return self._progress
