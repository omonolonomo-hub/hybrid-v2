"""
Test script to verify hex card flip animations.
Creates sample card images and tests the flip animation.
"""

import pygame
import math
import sys

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Hex Card Flip Animation Test")
clock = pygame.time.Clock()

# Colors
NEON_CYAN = (0, 242, 255)
NEON_PINK = (255, 0, 255)
BG_COLOR = (10, 11, 18)

# Card dimensions
CARD_W = 220
CARD_H = 360

def create_hex_card(color, label):
    """Create a hexagonal card placeholder."""
    surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    
    center_x = CARD_W // 2
    center_y = CARD_H // 2
    hex_radius = min(CARD_W, CARD_H) // 3
    
    # Calculate hex points
    hex_points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = center_x + hex_radius * math.cos(angle)
        y = center_y + hex_radius * math.sin(angle)
        hex_points.append((x, y))
    
    # Draw filled hex
    pygame.draw.polygon(surf, (20, 25, 40), hex_points)
    pygame.draw.polygon(surf, color, hex_points, 3)
    
    # Draw label
    font = pygame.font.SysFont("consolas", 24, bold=True)
    text = font.render(label, True, color)
    text_rect = text.get_rect(center=(center_x, center_y))
    surf.blit(text, text_rect)
    
    return surf

# Create card images
card_front = create_hex_card(NEON_CYAN, "FRONT")
card_back = create_hex_card(NEON_PINK, "BACK")

# Animation state
flip_value = 0.0
target_flip = 0.0

print("=" * 60)
print("HEX CARD FLIP ANIMATION TEST")
print("=" * 60)
print("Controls:")
print("  - Hover mouse over card to flip")
print("  - ESC to quit")
print()

running = True
while running:
    dt = clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Get mouse position
    mx, my = pygame.mouse.get_pos()
    
    # Card position
    card_x = 400 - CARD_W // 2
    card_y = 300 - CARD_H // 2
    card_rect = pygame.Rect(card_x, card_y, CARD_W, CARD_H)
    
    # Check if mouse is over card
    if card_rect.collidepoint(mx, my):
        target_flip = 1.0
    else:
        target_flip = 0.0
    
    # Smooth interpolation
    flip_value += (target_flip - flip_value) * 0.1
    
    # Clear screen
    screen.fill(BG_COLOR)
    
    # Calculate flip scale (FULL 180 degree rotation)
    scale_x = abs(math.cos(flip_value * math.pi))
    show_back = flip_value > 0.5
    
    # Select which side to show
    if show_back:
        card_surf = card_back
    else:
        card_surf = card_front
    
    # Scale the card
    scaled_width = max(2, int(CARD_W * scale_x))
    scaled_surf = pygame.transform.scale(card_surf, (scaled_width, CARD_H))
    
    # Center the scaled card
    scaled_x = card_x + (CARD_W - scaled_width) // 2
    
    # Draw the card
    screen.blit(scaled_surf, (scaled_x, card_y))
    
    # Draw info
    font = pygame.font.SysFont("consolas", 16)
    info_text = font.render(f"Flip Value: {flip_value:.2f} | Scale X: {scale_x:.2f}", True, (255, 255, 255))
    screen.blit(info_text, (10, 10))
    
    side_text = font.render(f"Showing: {'BACK' if show_back else 'FRONT'}", True, (255, 255, 255))
    screen.blit(side_text, (10, 30))
    
    pygame.display.flip()

pygame.quit()
sys.exit(0)
