#!/usr/bin/env python3
"""
Event Logger - Detaylı Kart Event Logging Sistemi
Bu modül mevcut logging sisteminden BAĞIMSIZ çalışır.
Sadece ENABLE_DETAILED_LOGGING=True olduğunda aktif olur.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Global flag - default False (mevcut sistem çalışır)
ENABLE_DETAILED_LOGGING = False

# Event log dosya yolu
EVENT_LOG_PATH = "output/logs/simulation_events.jsonl"
COMBAT_LOG_PATH = "output/logs/combat_events.jsonl"

# Global event buffer (performans için)
_event_buffer = []
_combat_buffer = []
_buffer_size = 100  # Her 100 event'te bir flush


class EventLogger:
    """
    Detaylı event logging sistemi.
    Mevcut logging sistemine DOKUNMAZ, sadece ek log üretir.
    """
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.game_id = None
        self.turn = 0
        
        if self.enabled:
            # Log klasörünü oluştur
            Path("output/logs").mkdir(parents=True, exist_ok=True)
            
            # Yeni simülasyon başladığında dosyaları temizle
            if os.path.exists(EVENT_LOG_PATH):
                os.remove(EVENT_LOG_PATH)
            if os.path.exists(COMBAT_LOG_PATH):
                os.remove(COMBAT_LOG_PATH)
    
    def set_game_context(self, game_id: int, turn: int):
        """Oyun context'ini ayarla"""
        self.game_id = game_id
        self.turn = turn
    
    def log_card_purchase(self, player_id: int, card_name: str, 
                         card_rarity: str, cost: int, gold_after: int):
        """Kart satın alma eventi"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'turn': self.turn,
            'event_type': 'card_purchase',
            'player_id': player_id,
            'card_name': card_name,
            'card_rarity': card_rarity,
            'cost': cost,
            'gold_after': gold_after
        }
        
        self._append_event(event)
    
    def log_board_placement(self, player_id: int, card_name: str,
                           position: tuple, board_size: int):
        """Board'a kart yerleştirme eventi"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'turn': self.turn,
            'event_type': 'board_placement',
            'player_id': player_id,
            'card_name': card_name,
            'position': list(position),
            'board_size': board_size
        }
        
        self._append_event(event)
    
    def log_combat(self, player1_id: int, player2_id: int,
                  winner_id: Optional[int], damage: int,
                  player1_board_power: int, player2_board_power: int,
                  combat_duration: int):
        """Combat eventi"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'turn': self.turn,
            'event_type': 'combat',
            'player1_id': player1_id,
            'player2_id': player2_id,
            'winner_id': winner_id,
            'damage': damage,
            'player1_board_power': player1_board_power,
            'player2_board_power': player2_board_power,
            'combat_duration': combat_duration
        }
        
        self._append_combat_event(event)
    
    def log_synergy_trigger(self, player_id: int, card_name: str,
                           synergy_type: str, synergy_value: int):
        """Sinerji tetikleme eventi"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'turn': self.turn,
            'event_type': 'synergy_trigger',
            'player_id': player_id,
            'card_name': card_name,
            'synergy_type': synergy_type,
            'synergy_value': synergy_value
        }
        
        self._append_event(event)
    
    def log_round_result(self, player_id: int, hp: int, gold: int,
                        board_size: int, hand_size: int, result: str):
        """Round sonucu eventi"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'turn': self.turn,
            'event_type': 'round_result',
            'player_id': player_id,
            'hp': hp,
            'gold': gold,
            'board_size': board_size,
            'hand_size': hand_size,
            'result': result
        }
        
        self._append_event(event)
    
    def log_passive_trigger(self, player_id: int, card_name: str,
                           trigger_type: str, effect_value: int):
        """Pasif yetenek tetikleme eventi"""
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'game_id': self.game_id,
            'turn': self.turn,
            'event_type': 'passive_trigger',
            'player_id': player_id,
            'card_name': card_name,
            'trigger_type': trigger_type,
            'effect_value': effect_value
        }
        
        self._append_event(event)
    
    def _append_event(self, event: Dict[str, Any]):
        """Event'i buffer'a ekle, gerekirse flush et"""
        global _event_buffer
        
        _event_buffer.append(event)
        
        # Buffer dolduğunda flush et
        if len(_event_buffer) >= _buffer_size:
            self._flush_events()
    
    def _append_combat_event(self, event: Dict[str, Any]):
        """Combat event'i buffer'a ekle"""
        global _combat_buffer
        
        _combat_buffer.append(event)
        
        if len(_combat_buffer) >= _buffer_size:
            self._flush_combat_events()
    
    def _flush_events(self):
        """Buffer'daki event'leri dosyaya yaz"""
        global _event_buffer
        
        if not _event_buffer:
            return
        
        try:
            with open(EVENT_LOG_PATH, 'a', encoding='utf-8') as f:
                for event in _event_buffer:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
            
            _event_buffer = []
        except Exception as e:
            print(f"Event log yazma hatası: {e}")
    
    def _flush_combat_events(self):
        """Combat buffer'ı flush et"""
        global _combat_buffer
        
        if not _combat_buffer:
            return
        
        try:
            with open(COMBAT_LOG_PATH, 'a', encoding='utf-8') as f:
                for event in _combat_buffer:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
            
            _combat_buffer = []
        except Exception as e:
            print(f"Combat log yazma hatası: {e}")
    
    def flush_all(self):
        """Tüm buffer'ları flush et (simülasyon sonunda)"""
        if self.enabled:
            self._flush_events()
            self._flush_combat_events()
    
    def close(self):
        """Logger'ı kapat ve tüm buffer'ları flush et"""
        self.flush_all()


# Global logger instance
_global_logger: Optional[EventLogger] = None


def init_event_logger(enabled: bool = False) -> EventLogger:
    """
    Global event logger'ı başlat.
    
    Args:
        enabled: True ise detaylı logging aktif olur
    
    Returns:
        EventLogger instance
    """
    global _global_logger, ENABLE_DETAILED_LOGGING
    
    ENABLE_DETAILED_LOGGING = enabled
    _global_logger = EventLogger(enabled=enabled)
    
    return _global_logger


def get_event_logger() -> Optional[EventLogger]:
    """Global event logger'ı al"""
    return _global_logger


def close_event_logger():
    """Global event logger'ı kapat"""
    global _global_logger
    
    if _global_logger:
        _global_logger.close()
        _global_logger = None
