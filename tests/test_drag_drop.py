import pytest
import pygame
from v2.scenes.shop import ShopScene
from v2.constants import Layout

@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()

def test_drag_initiates_on_hand_slot_click():
    """El (HandPanel) kismindaki bir slota sol tıklandığında sürükleme başlamalıdır."""
    scene = ShopScene()
    
    # 0. index slotun ortasina tiklama eventi simule edelim
    target_slot = scene.hand_panel.card_rects[0]
    click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=target_slot.center)
    
    scene.handle_event(click_event)
    
    # Drag state active olmali
    assert scene.drag_state["is_dragging"] is True, "Tıklama eventi sürükleme modunu tetiklemedi."
    assert scene.drag_state["source_panel"] == "hand"
    assert scene.drag_state["source_index"] == 0
    assert scene.drag_state["card_rect"] is not None

def test_drag_updates_position_on_mouse_motion():
    """Sürükleme anında fare hareket ettiğinde kartın konumu (mouse_pos) güncellenmelidir."""
    scene = ShopScene()
    
    # Drag state zorla acalim
    scene.drag_state["is_dragging"] = True
    scene.drag_state["mouse_pos"] = (0, 0)
    
    # Fareyi 500, 500 konumuna goturelim
    motion_event = pygame.event.Event(pygame.MOUSEMOTION, pos=(500, 500))
    scene.handle_event(motion_event)
    
    assert scene.drag_state["mouse_pos"] == (500, 500), "Motion eventi mouse_pos state degiskenini guncellemedi."

def test_drag_snaps_back_on_invalid_drop():
    """Gecersiz bir alana (bosta bir yer) sol tik birakildiginda drag state temizlenmelidir (Snap-Back)."""
    scene = ShopScene()
    
    # Drag state zorla acik goster
    scene.drag_state["is_dragging"] = True
    scene.drag_state["source_panel"] = "hand"
    scene.drag_state["source_index"] = 2
    
    # Fareyi rastgele bir yerde birak
    drop_event = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(200, 200))
    scene.handle_event(drop_event)
    
    # Drag state tamamen temizlenmeli
    assert scene.drag_state["is_dragging"] is False, "Drop event drag statini False yapmadi."
    assert scene.drag_state["source_panel"] is None
    assert scene.drag_state["source_index"] == -1
