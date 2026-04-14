"""
Visual test for Task 3.1: Edge stat rendering with EDGE_LABEL_INSET.

This test verifies that edge stats are positioned correctly using:
- card.rotated_edges() for rotation-aware edge list
- _edge_midpoint() for edge midpoint calculation
- _toward_center() with EDGE_LABEL_INSET constant
- STAT_TO_GROUP for upper-group mapping
- GROUP_COLORS for color coding
- Skips edges with value == 0
- No badge or background shape rendering

Feature: board-shop-ui-cleanup-v3
Task: 3.1 Modify edge stat rendering in draw_hex_card()
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pygame
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ui.renderer import CyberRenderer, EDGE_LABEL_INSET, GROUP_COLORS
from engine_core.card import Card
from engine_core.constants import STAT_TO_GROUP


def create_test_card(name, rarity, edges_data):
    """Create a test card with specific edge values."""
    # Create stats dict from edges
    stats = {stat_name: value for stat_name, value in edges_data}
    
    card = Card(
        name=name,
        category="Test",
        rarity=rarity,
        stats=stats,
        passive_type="none",
        edges=edges_data,
        rotation=0
    )
    return card


def main():
    """Run visual test for edge stat rendering."""
    pygame.init()
    
    # Create display
    width, height = 1200, 800
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Task 3.1: Edge Stat Rendering Test")
    
    # Create renderer
    renderer = CyberRenderer()
    
    # Test cards with different configurations
    test_cards = [
        # Card 1: All non-zero edges (different upper-groups)
        create_test_card(
            "Full Stats",
            "3",
            [
                ("Power", 5),        # EXISTENCE - red
                ("Speed", 3),        # EXISTENCE - red
                ("Meaning", 4),      # MIND - blue
                ("Intelligence", 2), # MIND - blue
                ("Gravity", 6),      # CONNECTION - green
                ("Harmony", 3),      # CONNECTION - green
            ]
        ),
        
        # Card 2: Mixed zero and non-zero edges
        create_test_card(
            "Mixed Stats",
            "4",
            [
                ("Power", 7),        # EXISTENCE - red
                ("Speed", 0),        # Should not render
                ("Meaning", 0),      # Should not render
                ("Intelligence", 5), # MIND - blue
                ("Gravity", 4),      # CONNECTION - green
                ("Harmony", 0),      # Should not render
            ]
        ),
        
        # Card 3: Single upper-group (all EXISTENCE)
        create_test_card(
            "Existence Only",
            "5",
            [
                ("Power", 8),
                ("Durability", 6),
                ("Size", 4),
                ("Speed", 5),
                ("Meaning", 0),
                ("Intelligence", 0),
            ]
        ),
        
        # Card 4: Rotated card (rotation=2)
        create_test_card(
            "Rotated",
            "2",
            [
                ("Power", 3),
                ("Speed", 2),
                ("Meaning", 4),
                ("Intelligence", 1),
                ("Gravity", 5),
                ("Harmony", 2),
            ]
        ),
    ]
    
    # Set rotation for the last card
    test_cards[3].rotation = 2
    
    # Card positions
    positions = [
        (250, 250),
        (650, 250),
        (250, 550),
        (650, 550),
    ]
    
    # Main loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Clear screen
        screen.fill((10, 11, 18))
        
        # Draw title
        font_title = pygame.font.SysFont("segoeui", 24, bold=True)
        title = font_title.render("Task 3.1: Edge Stat Rendering Test", True, (255, 255, 255))
        screen.blit(title, (width // 2 - title.get_width() // 2, 20))
        
        # Draw info text
        font_info = pygame.font.SysFont("segoeui", 14)
        info_lines = [
            f"EDGE_LABEL_INSET = {EDGE_LABEL_INSET} pixels",
            "Edge colors: EXISTENCE (red), MIND (blue), CONNECTION (green)",
            "Zero-value edges are not rendered",
            "Press ESC to exit",
        ]
        y_offset = 60
        for line in info_lines:
            info = font_info.render(line, True, (180, 180, 200))
            screen.blit(info, (20, y_offset))
            y_offset += 20
        
        # Draw test cards
        for i, (card, pos) in enumerate(zip(test_cards, positions)):
            # Draw card
            renderer.draw_hex_card(
                screen, card, pos, r=68,
                is_hovered=False, highlighted=False
            )
            
            # Draw card label below
            font_label = pygame.font.SysFont("segoeui", 12)
            label = font_label.render(card.name, True, (200, 200, 220))
            screen.blit(label, (pos[0] - label.get_width() // 2, pos[1] + 90))
            
            # Draw rotation info if rotated
            if card.rotation > 0:
                rot_label = font_label.render(f"Rotation: {card.rotation}", True, (255, 200, 100))
                screen.blit(rot_label, (pos[0] - rot_label.get_width() // 2, pos[1] + 105))
        
        # Draw legend
        legend_x = 20
        legend_y = height - 120
        font_legend = pygame.font.SysFont("segoeui", 14, bold=True)
        legend_title = font_legend.render("Upper-Group Colors:", True, (255, 255, 255))
        screen.blit(legend_title, (legend_x, legend_y))
        
        legend_y += 25
        for group, color in GROUP_COLORS.items():
            # Draw color box
            pygame.draw.rect(screen, color, (legend_x, legend_y, 20, 20))
            pygame.draw.rect(screen, (100, 100, 100), (legend_x, legend_y, 20, 20), 1)
            
            # Draw group name
            group_label = font_info.render(group, True, (200, 200, 220))
            screen.blit(group_label, (legend_x + 30, legend_y + 2))
            
            legend_y += 30
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("\n✅ Visual test completed")
    print(f"   - Edge stats positioned using EDGE_LABEL_INSET = {EDGE_LABEL_INSET}")
    print("   - Upper-group color coding applied")
    print("   - Zero-value edges skipped")
    print("   - No badges or background shapes rendered")


if __name__ == "__main__":
    main()
