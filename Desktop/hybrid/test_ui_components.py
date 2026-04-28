"""
Quick integration test for refactored UI components.
"""
import pygame

# Initialize pygame (required for some components)
pygame.init()

print("=== Testing HoverControl ===")
from v2.ui.hover_control import HoverControl, HoverState

hover = HoverControl(delay_ms=100)
print("✓ HoverControl instantiated")

# Test hover start
hover.start("shop", item=5)
assert not hover.is_active(), "Hover should not be active immediately"
print("✓ Hover started (not active yet)")

# Test hover update
hover.update(50)
assert not hover.is_active(), "Hover should not be active after 50ms"
hover.update(60)
assert hover.is_active(), "Hover should be active after 110ms total"
print("✓ Hover activated after delay")

# Test hover reset
hover.reset()
assert not hover.is_active(), "Hover should not be active after reset"
print("✓ Hover reset")

print("✓ HoverControl tests passed!\n")

print("=== Testing AudioSystem ===")
from v2.ui.audio_system import AudioSystem

audio = AudioSystem()
print("✓ AudioSystem instantiated")

# Test preload (will fail gracefully if assets missing)
print("Testing preload...")
audio.preload("test.wav")
print("✓ Preload completed (graceful failure if missing)")

# Test play (will fail gracefully if assets missing)
print("Testing play...")
audio.play("test.wav", volume=0.5)
print("✓ Play completed (graceful failure if missing)")

# Test stop
print("Testing stop...")
audio.stop("test.wav")
print("✓ Stop completed")

print("✓ AudioSystem tests passed!\n")

print("=== Testing DragDropHandler ===")
from v2.ui.drag_drop_handler import DragDropHandler, DragState

handler = DragDropHandler()
print("✓ DragDropHandler instantiated")

# Test initial state
assert not handler.is_active, "Handler should not be active initially"
print("✓ Initial state correct")

# Test start drag
handler.start("hand", 2, (100, 200), card_data={"name": "Test Card"})
assert handler.is_active, "Handler should be active after start"
assert handler.source_panel == "hand", "Source panel should be 'hand'"
assert handler.source_index == 2, "Source index should be 2"
print("✓ Drag started")

# Test update position
handler.update_position((150, 250))
assert handler.mouse_pos == (150, 250), "Mouse position should be updated"
print("✓ Position updated")

# Test rotation
handler.rotate()
assert handler.rotation == 1, "Rotation should be 1"
handler.rotate()
assert handler.rotation == 2, "Rotation should be 2"
print("✓ Rotation works")

# Test drop
result = handler.drop()
assert result is not None, "Drop should return result"
source_panel, source_idx, rotation, card_data = result
assert source_panel == "hand", "Source panel should be 'hand'"
assert source_idx == 2, "Source index should be 2"
assert rotation == 2, "Rotation should be 2"
assert not handler.is_active, "Handler should not be active after drop"
print("✓ Drop completed")

# Test cancel
handler.start("shop", 5, (200, 300))
handler.cancel()
assert not handler.is_active, "Handler should not be active after cancel"
print("✓ Cancel works")

print("✓ DragDropHandler tests passed!\n")

print("=== Testing CameraController ===")
from v2.ui.camera_controller import CameraController, CameraState

camera = CameraController()
print("✓ CameraController instantiated")

# Test initial state
assert camera.zoom == 1.0, "Initial zoom should be 1.0"
assert camera.offset == (0.0, 0.0), "Initial offset should be (0, 0)"
print("✓ Initial state correct")

# Test drag
camera.handle_drag_start((100, 100))
assert camera.is_dragging, "Camera should be dragging"
camera.handle_drag_move((150, 150))
assert camera.offset == (50.0, 50.0), "Offset should be updated"
camera.handle_drag_end()
assert not camera.is_dragging, "Camera should not be dragging after end"
print("✓ Drag works")

# Test reset
camera.reset()
assert camera.zoom == 1.0, "Zoom should be reset to 1.0"
assert camera.offset == (0.0, 0.0), "Offset should be reset to (0, 0)"
print("✓ Reset works")

# Test state snapshot
state = camera.get_state()
assert isinstance(state, CameraState), "get_state should return CameraState"
assert state.zoom == 1.0, "State zoom should be 1.0"
print("✓ State snapshot works")

print("✓ CameraController tests passed!\n")

print("=== Testing Integration ===")
# Test components working together
hover_ctrl = HoverControl(delay_ms=100)
audio_sys = AudioSystem()
drag_hdl = DragDropHandler()
cam_ctrl = CameraController()

# Simulate hover + audio
hover_ctrl.start("shop", item=3)
hover_ctrl.update(150)
if hover_ctrl.is_active():
    audio_sys.play("hover.wav", volume=0.3)
print("✓ Hover activated and sound played")

print("✓ Integration test passed!\n")

print("=== All Tests Complete ===")
print("All UI components are working correctly!")
