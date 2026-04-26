with open('implementation_plan_v2.md', 'r', encoding='utf-8') as f:
    text = f.read()

# --- Remaining scene references to fix ---

text = text.replace(
    'VersusScene ve CombatScene, ayn\u0131 tur i\u00e7in Phase 1.1 Step 5\u2019te dondurulmu\u015f e\u015fle\u015fme snapshot\u2019\u0131n\u0131 okur.',
    'VersusOverlay ve CombatOverlay, ayn\u0131 tur i\u00e7in Phase 1.1 Step 5\u2019te dondurulmu\u015f e\u015fle\u015fme snapshot\u2019\u0131n\u0131 okur.'
)

text = text.replace(
    'Then `SceneManager.transition_to(ShopScene)`.',
    'Then `ShopScene` is launched directly as the permanent root scene in `main.py`.'
)

text = text.replace(
    '- **Restart button:** Bottom center. Calls `SceneManager.transition_to(LobbyScene)` and resets `GameState`.',
    '- **Restart button:** Bottom center. Calls `GameState.reset()` and re-initializes `ShopScene` in `STATE_PREPARATION`.'
)

text = text.replace(
    '| `EndgameScene` tablo s\u00fctunlar\u0131 |',
    '| `EndgameOverlay` tablo s\u00fctunlar\u0131 |'
)

text = text.replace(
    '23. Implement `VersusOverlay`: `VersusScene` iptal edilip yerine bu Overlay yaz\u0131l\u0131r.',
    '23. Implement `VersusOverlay`: Ba\u011f\u0131ms\u0131z sahne yerine ShopScene \u00fczerinde \u00e7al\u0131\u015fan bir Popup Overlay olarak tasarland\u0131.'
)

text = text.replace(
    '24. Implement `CombatOverlay` & `CombatTerminal`: `CombatScene` iptal edilir.',
    '24. Implement `CombatOverlay` & `CombatTerminal`: Ba\u011f\u0131ms\u0131z sahne yerine ShopScene \u00fczerinde \u00e7al\u0131\u015fan Pop-up olarak tasarland\u0131.'
)

text = text.replace(
    '25. Implement `EndgameOverlay`: `EndgameScene` yerine bu kullan\u0131l\u0131r.',
    '25. Implement `EndgameOverlay`: Ba\u011f\u0131ms\u0131z sahne yerine ShopScene \u00fczerinde \u00e7al\u0131\u015fan Pop-up olarak tasarland\u0131.'
)

text = text.replace(
    '1. Her g\u00f6rev tek deliverable ile s\u0131n\u0131rl\u0131d\u0131r. `VersusScene` ile ba\u015flan\u0131rsa ayn\u0131 onay d\u00f6ng\u00fcs\u00fcnde otomatik olarak `CombatTerminal` veya `CombatScene`\u2019e ge\u00e7ilmez.',
    '1. Her g\u00f6rev tek deliverable ile s\u0131n\u0131rl\u0131d\u0131r. `VersusOverlay` ile ba\u015flan\u0131rsa ayn\u0131 onay d\u00f6ng\u00fcs\u00fcnde otomatik olarak `CombatTerminal` veya `CombatOverlay`\u2019a ge\u00e7ilmez.'
)

text = text.replace(
    '2. Phase 4 i\u00e7in a\u00e7\u0131k bir scene graph kontrat\u0131 gerekiyor. Normal ak\u0131\u015f `ShopScene -> VersusScene -> CombatScene -> ShopScene` olmal\u0131d\u0131r; `CombatScene -> EndgameScene` yaln\u0131zca post-combat elimination/game-over kontrol\u00fcnden sonra \u00e7al\u0131\u015fmal\u0131d\u0131r.',
    '2. Phase 4 i\u00e7in a\u00e7\u0131k bir faz makinesi kontrat\u0131 gerekiyor. Normal ak\u0131\u015f `STATE_PREPARATION -> STATE_VERSUS -> STATE_COMBAT -> STATE_PREPARATION` olmal\u0131d\u0131r; `STATE_ENDGAME` yaln\u0131zca post-combat elimination/game-over kontrol\u00fcnden sonra devreye girmelidir.'
)

text = text.replace(
    '3. `CombatScene` ve `CombatTerminal`, raw engine object\u2019leri de\u011fil normalize edilmi\u015f formatter payload\u2019lar\u0131n\u0131 t\u00fcketmelidir.',
    '3. `CombatOverlay` ve `CombatTerminal`, raw engine object\u2019leri de\u011fil normalize edilmi\u015f formatter payload\u2019lar\u0131n\u0131 t\u00fcketmelidir.'
)

text = text.replace(
    '2. Combat trigger single-fire coverage: `CombatScene` giri\u015findecombat tam bir kez \u00e7\u00f6z\u00fclmeli',
    '2. Combat trigger single-fire coverage: `STATE_COMBAT` faz\u0131na girildi\u011finde combat tam bir kez \u00e7\u00f6z\u00fclmeli'
)
# Also handle version without the typo
text = text.replace(
    '2. Combat trigger single-fire coverage: `CombatScene` giri\u015finde combat tam bir kez \u00e7\u00f6z\u00fclmeli',
    '2. Combat trigger single-fire coverage: `STATE_COMBAT` faz\u0131na girildi\u011finde combat tam bir kez \u00e7\u00f6z\u00fclmeli'
)

text = text.replace(
    '37. **`combat_phase()` \u2192 `CombatScene.on_enter()`:**',
    '37. **`combat_phase()` \u2192 CombatOverlay etkinle\u015fmesi (`STATE_COMBAT`):**'
)

with open('implementation_plan_v2.md', 'w', encoding='utf-8') as f:
    f.write(text)

print('DONE')
