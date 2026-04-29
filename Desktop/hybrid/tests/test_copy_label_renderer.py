"""Tests for CopyLabelRenderer."""

import pygame
import pytest

from v2.ui.copy_label_renderer import CopyLabelRenderer


@pytest.fixture
def renderer():
    """Create a CopyLabelRenderer instance."""
    return CopyLabelRenderer()


@pytest.fixture
def surface():
    """Create a test surface."""
    # pygame.init() is handled by session-scoped conftest.py fixture
    return pygame.Surface((800, 600))


def test_renderer_initializes_with_empty_cache(renderer):
    """Test that renderer starts with an empty cache."""
    assert len(renderer._cache) == 0


def test_invalidate_clears_cache(renderer):
    """Test that invalidate() clears the cache."""
    # Manually add something to cache
    renderer._cache[("TestCard", 2)] = pygame.Surface((50, 20))
    assert len(renderer._cache) == 1
    
    renderer.invalidate()
    assert len(renderer._cache) == 0


def test_render_with_empty_slots(renderer, surface):
    """Test rendering with no cards (all None)."""
    rects = [pygame.Rect(10, 10, 100, 120) for _ in range(3)]
    names = [None, None, None]
    copies = {}
    
    # Should not raise any errors
    renderer.render(surface, rects, names, copies)
    assert len(renderer._cache) == 0


def test_render_creates_cache_entries(renderer, surface):
    """Test that rendering creates cache entries for unique cards."""
    rects = [
        pygame.Rect(10, 10, 100, 120),
        pygame.Rect(120, 10, 100, 120),
        pygame.Rect(230, 10, 100, 120),
    ]
    names = ["CardA", "CardB", "CardA"]
    copies = {"CardA": 2, "CardB": 1}
    
    renderer.render(surface, rects, names, copies)
    
    # Should have 2 cache entries: (CardA, 2) and (CardB, 1)
    assert len(renderer._cache) == 2
    assert ("CardA", 2) in renderer._cache
    assert ("CardB", 1) in renderer._cache


def test_render_reuses_cache(renderer, surface):
    """Test that rendering reuses cached surfaces."""
    rects = [pygame.Rect(10, 10, 100, 120)]
    names = ["CardA"]
    copies = {"CardA": 2}
    
    # First render
    renderer.render(surface, rects, names, copies)
    cached_surface = renderer._cache[("CardA", 2)]
    
    # Second render with same data
    renderer.render(surface, rects, names, copies)
    
    # Should be the same surface object (reused)
    assert renderer._cache[("CardA", 2)] is cached_surface


def test_render_updates_cache_on_count_change(renderer, surface):
    """Test that cache updates when copy count changes."""
    rects = [pygame.Rect(10, 10, 100, 120)]
    names = ["CardA"]
    
    # First render with count=1
    copies = {"CardA": 1}
    renderer.render(surface, rects, names, copies)
    assert ("CardA", 1) in renderer._cache
    assert len(renderer._cache) == 1
    
    # Second render with count=2
    copies = {"CardA": 2}
    renderer.render(surface, rects, names, copies)
    assert ("CardA", 2) in renderer._cache
    assert len(renderer._cache) == 2  # Both entries exist


def test_render_handles_missing_copy_count(renderer, surface):
    """Test that rendering handles cards not in copies_by_name dict."""
    rects = [pygame.Rect(10, 10, 100, 120)]
    names = ["UnknownCard"]
    copies = {}  # Card not in dict
    
    # Should default to 0 copies
    renderer.render(surface, rects, names, copies)
    assert ("UnknownCard", 0) in renderer._cache


def test_render_with_mixed_slots(renderer, surface):
    """Test rendering with mix of empty and filled slots."""
    rects = [
        pygame.Rect(10, 10, 100, 120),
        pygame.Rect(120, 10, 100, 120),
        pygame.Rect(230, 10, 100, 120),
        pygame.Rect(340, 10, 100, 120),
    ]
    names = ["CardA", None, "CardB", None]
    copies = {"CardA": 3, "CardB": 1}
    
    renderer.render(surface, rects, names, copies)
    
    # Should only cache the non-None cards
    assert len(renderer._cache) == 2
    assert ("CardA", 3) in renderer._cache
    assert ("CardB", 1) in renderer._cache
