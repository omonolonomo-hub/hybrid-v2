import os

def process_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. Update hex_grid.py
hex_grid_replacements = [
    ("import pygame.gfxdraw", "import pygame.gfxdraw\nfrom v2.constants import CameraState"),
    ("def render_synergy_lines(\n    surface: pygame.Surface,\n    adjacency_pairs: list,\n) -> None:", 
     "def render_synergy_lines(\n    surface: pygame.Surface,\n    adjacency_pairs: list,\n    camera: CameraState,\n) -> None:"),
    ("x1, y1 = axial_to_pixel(*coord_a)", "x1, y1 = axial_to_pixel(*coord_a, camera)"),
    ("x2, y2 = axial_to_pixel(*coord_b)", "x2, y2 = axial_to_pixel(*coord_b, camera)"),
    
    ("def render_synergy_preview(\n    surface: pygame.Surface,\n    hover_coord: tuple,\n    card_name: str,\n    board_cards: dict,\n    drag_rotation: int = 0,\n    board_rotations: dict = None,\n    card_data: any = None,\n) -> None:",
     "def render_synergy_preview(\n    surface: pygame.Surface,\n    hover_coord: tuple,\n    card_name: str,\n    board_cards: dict,\n    drag_rotation: int = 0,\n    board_rotations: dict = None,\n    card_data: any = None,\n    camera: CameraState = None,\n) -> None:"),
    ("cx, cy  = axial_to_pixel(q, r)", "cx, cy  = axial_to_pixel(q, r, camera)"),
    ("nx, ny = axial_to_pixel(*nb)", "nx, ny = axial_to_pixel(*nb, camera)"),
    ("zoom = GridMath.camera.zoom", "zoom = camera.zoom"),
    
    ("def render_ghost_preview(surface: pygame.Surface, card_name: str, mouse_pos: tuple[int, int], rotation: int = 0, card_data=None):",
     "def render_ghost_preview(surface: pygame.Surface, card_name: str, mouse_pos: tuple[int, int], rotation: int = 0, card_data=None, camera: CameraState = None):"),
    ("cx, cy = axial_to_pixel(q, r)", "cx, cy = axial_to_pixel(q, r, camera)"),
    
    ("def render_hex_grid(surface: pygame.Surface, board_cards: dict | None = None):",
     "def render_hex_grid(surface: pygame.Surface, board_cards: dict | None = None, camera: CameraState = None):"),
    ("mouse_q, mouse_r = pixel_to_axial(*mouse_pos)", "mouse_q, mouse_r = pixel_to_axial(*mouse_pos, camera)"),
    
    ("def axial_to_pixel(q: int, r: int) -> tuple[float, float]:",
     "def axial_to_pixel(q: int, r: int, camera: CameraState) -> tuple[float, float]:"),
    ("off_x = GridMath.camera.offset_x", "off_x = camera.offset_x"),
    ("off_y = GridMath.camera.offset_y", "off_y = camera.offset_y"),
    
    ("def pixel_to_axial(px: float, py: float) -> tuple[int, int]:",
     "def pixel_to_axial(px: float, py: float, camera: CameraState) -> tuple[int, int]:")
]
process_file(r"v2\ui\hex_grid.py", hex_grid_replacements)

# 2. Update shop.py
shop_replacements = [
    ("from v2.constants import Layout, Screen, Colors, Config, GridMath, Typography", 
     "from v2.constants import Layout, Screen, Colors, Config, GridMath, Typography, CameraState"),
    ("self._anim_timer = 0.0", "self._anim_timer = 0.0\n        self.camera = CameraState()"),
    ("GridMath.camera", "self.camera"),
    ("cx, cy = axial_to_pixel(*coord)", "cx, cy = axial_to_pixel(*coord, self.camera)"),
    ("from v2.ui.hex_grid import render_ghost_preview, render_hex_grid, \\\n            render_synergy_lines, render_synergy_preview, pixel_to_axial",
     "from v2.ui.hex_grid import render_ghost_preview, render_hex_grid, \\\n            render_synergy_lines, render_synergy_preview, pixel_to_axial"),
    ("render_hex_grid(surface, self._current_public_state().board_cards)", "render_hex_grid(surface, self._current_public_state().board_cards, self.camera)"),
    ("render_synergy_lines(surface, self._current_public_state().adjacency_pairs)", "render_synergy_lines(surface, self._current_public_state().adjacency_pairs, self.camera)"),
    ("render_ghost_preview(surface, card_name, self.drag_state[\"mouse_pos\"], rotation=drag_rot, card_data=card_data)",
     "render_ghost_preview(surface, card_name, self.drag_state[\"mouse_pos\"], rotation=drag_rot, card_data=card_data, camera=self.camera)"),
    ("render_synergy_preview(\n                    surface,\n                    pixel_to_axial(*self.drag_state[\"mouse_pos\"]),\n                    card_name,\n                    self._current_public_state().board_cards,\n                    drag_rotation=drag_rot,\n                    board_rotations=self._current_public_state().board_rotations,\n                    card_data=card_data\n                )",
     "render_synergy_preview(\n                    surface,\n                    pixel_to_axial(*self.drag_state[\"mouse_pos\"], self.camera),\n                    card_name,\n                    self._current_public_state().board_cards,\n                    drag_rotation=drag_rot,\n                    board_rotations=self._current_public_state().board_rotations,\n                    card_data=card_data,\n                    camera=self.camera\n                )"),
     ("axial_to_pixel(*coord, self.camera, self.camera)", "axial_to_pixel(*coord, self.camera)") # fix potential double inject
]
process_file(r"v2\scenes\shop.py", shop_replacements)

print("Refactoring complete.")
