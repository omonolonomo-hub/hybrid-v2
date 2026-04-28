"""
HoverControl - Hover delay ve panel görünürlük state yönetimi.

Self-contained component, sadece dt ve item bilgisi alır.
"""
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class HoverState:
    """Hover durumu için immutable state."""
    panel: Optional[str] = None  # "shop", "board", "hand", vb.
    item: Any = None  # slot_idx, coord, vb.
    elapsed_ms: int = 0
    active: bool = False


class HoverControl:
    """
    Hover delay ve panel görünürlük kontrolü.
    
    Kullanım:
        hover = HoverControl(delay_ms=150)
        
        # Her frame:
        hover.update(dt_ms)
        
        # Mouse hover başladığında:
        hover.start("shop", slot_idx=2)
        
        # Hover aktif mi kontrol et:
        if hover.is_active():
            state = hover.get_state()
            # Panel göster...
        
        # Mouse hover bittiğinde:
        hover.reset()
    """

    def __init__(self, delay_ms: int = 150):
        """
        Args:
            delay_ms: Hover aktif olmadan önce bekleme süresi (ms)
        """
        self._delay_ms = delay_ms
        self._state = HoverState()

    def start(self, panel: str, item: Any = None) -> None:
        """
        Hover başlat.
        
        Args:
            panel: Panel adı ("shop", "board", "hand")
            item: Panel-specific item (slot_idx, coord, vb.)
        """
        # Aynı item üzerindeyse state'i koru
        if self._state.panel == panel and self._state.item == item:
            return
        
        # Yeni hover başlat
        self._state = HoverState(panel=panel, item=item, elapsed_ms=0, active=False)

    def update(self, dt_ms: int) -> None:
        """
        Hover timer'ı güncelle.
        
        Args:
            dt_ms: Delta time (milliseconds)
        """
        if self._state.panel is not None and not self._state.active:
            self._state.elapsed_ms += dt_ms
            if self._state.elapsed_ms >= self._delay_ms:
                self._state.active = True

    def reset(self) -> None:
        """Hover state'ini sıfırla."""
        self._state = HoverState()

    def is_active(self) -> bool:
        """Hover aktif mi?"""
        return self._state.active and self._state.panel is not None

    def get_state(self) -> HoverState:
        """Mevcut hover state'ini döndür."""
        return self._state

    def get_panel(self) -> Optional[str]:
        """Aktif panel adını döndür."""
        return self._state.panel if self.is_active() else None

    def get_item(self) -> Any:
        """Aktif item'ı döndür."""
        return self._state.item if self.is_active() else None

    @property
    def delay_ms(self) -> int:
        """Hover delay süresi."""
        return self._delay_ms

    @delay_ms.setter
    def delay_ms(self, value: int) -> None:
        """Hover delay süresini güncelle."""
        self._delay_ms = max(0, value)
