"""
game_state.py
-------------
Oyunun tüm anlık durumunu tutan sınıf.
Hiçbir pygame veya UI koduna bağımlı değildir.

DEĞİŞİKLİK (v2.1):
  board artık List değil Dict[(q,r) → kart_dict].
  Bu sayede 37-hex axial grid koordinatlarıyla çalışılır.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import copy

from .card_loader import load_all_cards, build_shop_pool


@dataclass
class GameState:
    # ── Oyun ilerlemesi ──────────────────────────────
    round: int = 1
    max_rounds: int = 8

    # ── Kaynak ──────────────────────────────────────
    gold: int = 10
    hp: int = 150

    # ── Kart havuzu (tüm oyun boyunca sabit) ────────
    all_cards: List[Dict[str, Any]] = field(default_factory=list)

    # ── El: max 6 kart ──────────────────────────────
    hand: List[Dict[str, Any]] = field(default_factory=list)

    # ── Tahta: axial koordinat → kart ───────────────
    # Anahtar: (q, r) tuple  |  Değer: kart dict
    board: Dict[Tuple[int, int], Dict[str, Any]] = field(default_factory=dict)

    # ── Dükkan: 5 kart ──────────────────────────────
    shop: List[Dict[str, Any]] = field(default_factory=list)

    # ── Mevcut ekran ────────────────────────────────
    current_screen: str = "lobby"

    # ── Lobby: seçili strateji ───────────────────────
    player_strategy: str = "builder"

    # ── Mesaj / bildirim ─────────────────────────────
    message: Optional[str] = None
    message_timer: float = 0.0

    def setup(self):
        """Oyun başında bir kere çağrılır."""
        self.all_cards = load_all_cards()
        self.refresh_shop()

    def refresh_shop(self, cost: int = 0):
        """Dükkanı yenile. cost kadar gold öder."""
        if self.gold < cost:
            self.show_message("Yeterli altın yok!")
            return
        self.gold -= cost
        self.shop = build_shop_pool(self.all_cards)

    # ── El işlemleri ─────────────────────────────────

    def buy_card(self, shop_idx: int) -> bool:
        """Dükkandan kart satın al. True = başarılı."""
        if shop_idx >= len(self.shop):
            return False
        card = self.shop[shop_idx]
        if self.gold < card["cost"]:
            self.show_message("Yeterli altın yok!")
            return False
        if len(self.hand) >= 6:
            self.show_message("El dolu! (max 6)")
            return False
        self.gold -= card["cost"]
        self.hand.append(copy.deepcopy(card))
        self.shop.pop(shop_idx)
        return True

    def sell_card(self, hand_idx: int) -> bool:
        """Elden kart sat, yarı altınını geri al."""
        if hand_idx >= len(self.hand):
            return False
        card = self.hand.pop(hand_idx)
        self.gold += max(1, card["cost"] // 2)
        return True

    def place_card(self, hand_idx: int, coord: Tuple[int, int]) -> bool:
        """
        Elden tahtaya kart yerleştir.
        coord: (q, r) axial koordinat, boş olmalı.
        """
        if hand_idx >= len(self.hand):
            return False
        if coord in self.board:
            self.show_message("Bu hex dolu!")
            return False
        card = self.hand.pop(hand_idx)
        self.board[coord] = card
        return True

    def recall_card(self, coord: Tuple[int, int]) -> bool:
        """Tahtadan ele geri al."""
        if coord not in self.board:
            return False
        if len(self.hand) >= 6:
            self.show_message("El dolu!")
            return False
        card = self.board.pop(coord)
        self.hand.append(card)
        return True

    def clear_board(self):
        """Savaştan sonra tahtayı temizle (kartlar kaybolur — savaşa girildi)."""
        self.board.clear()

    # ── Tur akışı ────────────────────────────────────

    def advance_round(self):
        """Savaştan sonra turu ilerlet, gelir ekle, tahtayı sıfırla."""
        self.clear_board()
        self.round += 1
        income = 3 + min(5, self.gold // 10)
        self.gold += income
        self.refresh_shop()
        if self.round > self.max_rounds:
            self.current_screen = "game_over"
        else:
            self.current_screen = "shop"

    def take_damage(self, dmg: int):
        self.hp = max(0, self.hp - dmg)
        if self.hp <= 0:
            self.current_screen = "game_over"

    # ── Yardımcılar ──────────────────────────────────

    def show_message(self, text: str, duration: float = 2.5):
        self.message = text
        self.message_timer = duration

    def tick(self, dt: float):
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = None
