from enum import IntEnum

class ActionResult(IntEnum):
    OK              = 0
    ERR_INSUFFICIENT_GOLD  = 1
    ERR_SLOT_OCCUPIED      = 2
    ERR_POOL_EMPTY         = 3
    ERR_INVALID_COORD      = 4
    ERR_PLACE_LOCKED       = 5
    ERR_INVALID_HAND_IDX   = 6
    ERR_NOT_IN_PREP_PHASE  = 7
    ERR_NOT_OWNER          = 8
    ERR_ENGINE_EXCEPTION   = 99

class GameState:
    _instance = None

    def __init__(self):
        self._engine = None
        self._board: dict[tuple[int, int], str] = {}       # (q,r) → card_name
        self._board_rotations: dict[tuple[int, int], int] = {}  # (q,r) → rotation (0-5)
        self.place_locked: bool = False
        self._pairings_cache: list[tuple[int, int]] = []
        self.view_index: int = 0                           # Current player index being viewed
        self._phase: str = "STATE_PREPARATION"             # Global game phase

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = GameState()
        return cls._instance

    def hook_engine(self, engine):
        """MockGame veya gerçek engine_core motorunu UI'a bağlar."""
        self._engine = engine

    def get_gold(self, player_index: int = None) -> int:
        if player_index is None: player_index = self.view_index
        if not self._engine:
            return 0
        try:
            return self._engine.players[player_index].gold
        except (AttributeError, IndexError):
            return 0

    def get_hp(self, player_index: int = None) -> int:
        if player_index is None: player_index = self.view_index
        if not self._engine:
            return 0
        try:
            return self._engine.get_hp(player_index)
        except (AttributeError, TypeError, IndexError):
            try:
                return int(self._engine.players[player_index].hp)
            except (AttributeError, IndexError):
                return 0

    def get_shop(self, player_index: int = None) -> list:
        """Dükkan penceresi: 5 elemanlı liste [card_name | None]"""
        if player_index is None: player_index = self.view_index
        if not self._engine:
            return [None] * 5
        try:
            # Gerçek engine Game'in market window'u player-specific tutulur
            return self._engine.get_shop_window(player_index)
        except AttributeError:
            # Gerçek engine: market._player_windows[pid] üzerinden oku
            try:
                pid     = self._engine.players[player_index].pid
                window  = self._engine.market._player_windows.get(pid, [])
                # None kontrolü: satın alınan slotlar None olabilir
                names   = [c.name if c is not None else None for c in window]
                return names + [None] * (5 - len(names))
            except Exception:
                return [None] * 5

    def get_hand(self, player_index: int = None) -> list:
        """El: HAND_MAX_CARDS elemanlı liste [card_name | None]"""
        if player_index is None: player_index = self.view_index
        if not self._engine:
            return [None] * 6
        try:
            return self._engine.get_hand(player_index)
        except AttributeError:
            # Gerçek engine.get_hand yok: direkt player.hand'den oku
            try:
                hand = self._engine.players[player_index].hand
                names = [c.name if hasattr(c, 'name') else c for c in hand if c is not None]
                return names + [None] * (6 - len(names))
            except Exception:
                return [None] * 6

    def buy_card(self, player_index: int, card_id: int, cost: int) -> ActionResult:
        """Kullanıcının kart alım isteğini motora iletir ve güvenli Enum yanıtı döner."""
        if player_index != 0:
            return ActionResult.ERR_NOT_OWNER
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION
        player = self._engine.players[player_index]
        if player.gold >= cost:
            player.gold -= cost
            return ActionResult.OK
        return ActionResult.ERR_INSUFFICIENT_GOLD

    # ── Phase Management ────────────────────────────────────────────────
    def get_phase(self) -> str:
        return self._phase
        
    def set_phase(self, phase: str):
        self._phase = phase

    def buy_card_from_slot(self, player_index: int, slot_index: int) -> ActionResult:
        if player_index != 0:
            return ActionResult.ERR_NOT_OWNER
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION
        # Dead player guard (Zombie Spectator fix)
        try:
            player = self._engine.players[player_index]
            if not getattr(player, 'alive', True):
                return ActionResult.ERR_NOT_IN_PREP_PHASE
        except (IndexError, AttributeError):
            pass
        # Try engine method first (MockGame has it)
        try:
            ok = self._engine.buy_card_from_slot(player_index, slot_index)
            return ActionResult.OK if ok else ActionResult.ERR_POOL_EMPTY
        except AttributeError:
            # Real engine has no buy_card_from_slot — use market directly
            try:
                from engine_core.constants import CARD_COSTS
                player = self._engine.players[player_index]
                pid = player.pid
                window = self._engine.market._player_windows.get(pid, [])
                if slot_index >= len(window) or window[slot_index] is None:
                    return ActionResult.ERR_POOL_EMPTY
                
                card = window[slot_index]
                # Use correct cost table (rarity "1".."5") not a nonexistent card.cost field
                cost = CARD_COSTS.get(card.rarity, 2)
                if player.gold < cost:
                    return ActionResult.ERR_INSUFFICIENT_GOLD
                
                # player.buy_card handles gold deduction, stat updates, and HAND_LIMIT FIFO drops
                # NOTE: buy_card internally checks gold >= cost again and only proceeds if true
                player.buy_card(card, market=self._engine.market,
                                trigger_passive_fn=getattr(self._engine, "trigger_passive_fn", None))
                
                window[slot_index] = None  # DO NOT POP — replace with None so UI slots don't shift
                
                return ActionResult.OK
            except Exception as e:
                print(f"[GameState] buy_card_from_slot hata: {e}")
                import traceback; traceback.print_exc()
                return ActionResult.ERR_ENGINE_EXCEPTION


    def reroll_market(self, player_index: int = 0) -> ActionResult:
        if player_index != 0:
            return ActionResult.ERR_NOT_OWNER
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION
        try:
            ok = self._engine.reroll_market(player_index)
            print(f"[DEBUG]     engine.reroll_market({player_index}) -> ok={ok}")
            return ActionResult.OK if ok else ActionResult.ERR_INSUFFICIENT_GOLD
        except Exception as e:
            print(f"[GameState] reroll_market HATA: {e}")
            import traceback; traceback.print_exc()
            return ActionResult.ERR_ENGINE_EXCEPTION

    def toggle_lock_shop(self, player_index: int = 0) -> None:
        if player_index != 0:
            return # Gated
        if self._engine:
            self._engine.toggle_lock_shop(player_index)

    # ── Board / Placement ───────────────────────────────────────────────

    def get_board_cards(self, player_index: int = None) -> dict:
        """Board üzerindeki kartlar.
        
        Gerçek engine bağlıysa: {(q, r): {"name": str, "stats": dict, "rotation": int}}
        Aksi halde (MockGame): {(q, r): card_name_str} — geriye dönük uyumlu.
        """
        if player_index is None: player_index = self.view_index
        if self._engine and hasattr(self._engine, 'players'):
            try:
                if player_index < 0 or player_index >= len(self._engine.players):
                    return {}
                grid = self._engine.players[player_index].board.grid
                result = {}
                for coord, card in grid.items():
                    # card is a real Card object — extract dynamic stats
                    result[coord] = {
                        "name": card.name,
                        "stats": {k: v for k, v in card.stats.items()},
                        "rotation": getattr(card, 'rotation', 0),
                    }
                if player_index == 0:
                    # Keep _board in sync for legacy callers expecting plain strings (Player 0 only)
                    self._board = {c: v["name"] for c, v in result.items()}
                    self._board_rotations = {c: v["rotation"] for c, v in result.items()}
                return result
            except Exception:
                pass
        return self._board if player_index == 0 else {}

    def get_player_composition(self, player_index: int = 0) -> dict[str, int]:
        """İlgili oyuncunun tahtasındaki kategori dağılımını döner."""
        from v2.core.card_database import CardDatabase
        db = CardDatabase.get()
        
        # SynergyHud/MinimapHud ile uyumlu olan kategori anahtarları
        inventory = {}
        board_cards = self.get_board_cards(player_index)
        
        # Normalleştirme sözlüğü (SynergyHud._CAT_MAPPING ile senkron)
        mapper = {
            "Mythology & Gods":     "MYTHOLOGY",
            "Art & Culture":        "ART",
            "Nature & Biology":     "NATURE",
            "Nature & Creatures":   "NATURE",
            "Cosmos & Space":       "COSMOS",
            "Cosmos":               "COSMOS",
            "Science":              "SCIENCE",
            "Science & Technology": "SCIENCE",
            "History":              "HISTORY",
            "History & Civilizations": "HISTORY",
        }

        for info in board_cards.values():
            name = info.get("name") if isinstance(info, dict) else info
            card = db.lookup(name)
            if card:
                raw_cat = card.category
                # Normalize et: "Science" -> "SCIENCE"
                cat = mapper.get(raw_cat, raw_cat.upper().split(" & ")[0])
                inventory[cat] = inventory.get(cat, 0) + 1
        
        return inventory

    def get_board_rotations(self) -> dict[tuple[int, int], int]:
        """Board üzerindeki kartların rotasyonları: {(q, r): rotation (0-5)}"""
        return self._board_rotations

    def place_card(self, hand_index: int, coord: tuple[int, int],
                   rotation: int = 0, player_index: int = 0) -> 'ActionResult':
        """
        Elden kartı board'a yerleştirir.
        Spec Section 2.1 — tek kart/tur kuralı (place_locked).
        """
        if player_index != 0:
            return ActionResult.ERR_NOT_OWNER
        if self.place_locked:
            return ActionResult.ERR_PLACE_LOCKED
        if coord in self._board:
            return ActionResult.ERR_SLOT_OCCUPIED
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION

        player = self._engine.players[0]
        # UI ile engine indexlerinin kaymamasini sagla: None'lari temizle (Compact)
        player.hand = [c for c in player.hand if c is not None]
        
        if hand_index < 0 or hand_index >= len(player.hand):
            return ActionResult.ERR_INVALID_HAND_IDX

        raw = player.hand.pop(hand_index)
        card_name = getattr(raw, "name", raw)
        
        if card_name is None:
            return ActionResult.ERR_INVALID_HAND_IDX

        self._board[coord] = card_name
        self._board_rotations[coord] = rotation % 6
        # Engine board sync (gerçek Card nesnesi varsa — Section 2.4 çift-yazma sözleşmesi)
        if hasattr(raw, 'rotation'):      # gerçek Card nesnesi (MockGame'de string, skip)
            raw.rotation = rotation % 6
            player.board.place(coord, raw)
        self.place_locked = True  # Tur başı 1 kart kuralı tekrar aktif edildi
        return ActionResult.OK

    def reset_turn(self) -> None:
        """Tur başında state'i temizler."""
        self.place_locked = False
        # [FIX] Pasif loglarını her tur başında temizle ki UI'ya 'hayalet' veya 'mükerrer' log sızmasın.
        if self._engine and hasattr(self._engine, 'players'):
            try:
                self._engine.players[0].passive_buff_log.clear()
            except (AttributeError, IndexError):
                pass

    def get_adjacency_pairs(self) -> list[tuple]:
        """
        Board'daki komşu kart çiftleri için karşılıklı KENAR bilgilerini döndürür.
        Dönen format: [(coord_a, coord_b, group_a, group_b), ...]
          group_a = A'nın B'ye bakan kenarının stat grubu
          group_b = B'nin A'ya bakan kenarının stat grubu
        Her çift yalnızca bir kez görünür (dedupe).
        Motor gibi: card.edges[dir] = (stat_name, value), rotation=0 varsayımı.
        """
        from v2.core.card_database import CardDatabase
        from v2.constants import ENGINE_HEX_DIRS, OPP_DIR, STAT_TO_GROUP

        try:
            db = CardDatabase.get()
        except RuntimeError:
            return []

        pairs: list[tuple] = []
        seen:  set = set()

        for coord, card_name in self._board.items():
            data = db.lookup(card_name)
            if not data:
                continue
            edges_a = list(data.stats.items())   # [(stat_name, val), ...] len=6, orijinal sıra
            if len(edges_a) < 6:
                continue
            rot_a = self._board_rotations.get(coord, 0)

            q, r = coord
            for dir_idx, (dq, dr) in enumerate(ENGINE_HEX_DIRS):
                nb = (q + dq, r + dr)
                if nb not in self._board:
                    continue

                pair_key = (min(coord, nb), max(coord, nb))
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                nb_data = db.lookup(self._board[nb])
                if not nb_data:
                    continue
                edges_b = list(nb_data.stats.items())
                if len(edges_b) < 6:
                    continue
                rot_b = self._board_rotations.get(nb, 0)

                # Rotation uygulaması:
                # Kart rot adım döndürülmüşse, dir_idx yönündeki gerçek kenar
                # orijinal karttaki (dir_idx - rot) % 6 indexindedir.
                real_idx_a = (dir_idx - rot_a) % 6
                real_idx_b = (OPP_DIR[dir_idx] - rot_b) % 6

                group_a = STAT_TO_GROUP.get(edges_a[real_idx_a][0], "")
                group_b = STAT_TO_GROUP.get(edges_b[real_idx_b][0], "")
                pairs.append((coord, nb, group_a, group_b))

        return pairs

    # ── Yeni accessor'lar (Phase 3c / Section 2.4) ──────────────────────────

    def commit_human_turn(self) -> None:
        """
        Oyuncu 'Hazır' dediğinde çalışır.
        Time-Dilation Fix: preparation_phase() yerine start_turn/finish_turn split kullanır.
        Faiz ve Evolution sadece bir kez uygulanır.
        """
        try:
            if self._engine:
                # Use split orchestration if engine supports it
                if hasattr(self._engine, 'finish_turn'):
                    self._engine.finish_turn()
                else:
                    # Legacy fallback — only for MockGame
                    self._engine.preparation_phase()
            self.freeze_pairings()
        except Exception as e:
            print(f"[GameState] commit_human_turn hatası: {e}")

    def get_turn(self) -> int:
        try:
            return self._engine.turn
        except Exception:
            return 1

    def get_alive_pids(self) -> list:
        try:
            return [p.pid for p in self._engine.players if getattr(p, 'alive', True)]
        except Exception:
            return list(range(8))

    def get_display_name(self, player_index: int = 0) -> str:
        """Phase 5: Oyuncu görüncü adı (UI label). Format: P{pid}."""
        try:
            pid = self._engine.players[player_index].pid
            return f"P{pid}"
        except Exception:
            return f"P{player_index}"

    def get_strategy(self, player_index: int = 0) -> str:
        """Phase 5: Oyuncunun strateji adını döndürür."""
        try:
            return self._engine.players[player_index].strategy
        except Exception:
            return "unknown"

    def get_win_streak(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].win_streak
        except Exception:
            return 0

    def get_copies(self, card_name: str, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].copies.get(card_name, 0)
        except Exception:
            return 0

    def get_copy_strengthening_milestones(self) -> list[dict]:
        """Returns pending copy-strengthening milestones for the current turn.

        This is an integration point for UI feedback when copy thresholds
        (turns 4/7) cause board cards to strengthen.
        """
        milestones: list[dict] = []
        if not self._engine:
            return milestones

        try:
            player = self._engine.players[0]
            turn = self.get_turn()
            thresholds = [4, 7]
            if turn not in thresholds:
                return milestones

            copies = getattr(player, "copies", {})
            copy_applied = getattr(player, "copy_applied", {})
            board_names = set(self.get_board_cards().values())

            for card_name, count in copies.items():
                if card_name not in board_names:
                    continue

                applied = copy_applied.get(card_name, {"2": False, "3": False})

                if turn == thresholds[0] and count >= 2 and not applied.get("2", False):
                    milestones.append({
                        "card": card_name,
                        "trigger": "copy_2",
                        "count": count,
                        "turn": turn,
                    })
                if turn == thresholds[1] and count >= 3 and not applied.get("3", False):
                    milestones.append({
                        "card": card_name,
                        "trigger": "copy_3",
                        "count": count,
                        "turn": turn,
                    })
        except Exception:
            pass

        return milestones

    def is_alive(self, player_index: int = 0) -> bool:
        try:
            return bool(self._engine.players[player_index].alive)
        except Exception:
            return True

    def get_total_pts(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].total_pts
        except Exception:
            return 0

    def get_turn_pts(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].turn_pts
        except Exception:
            return 0

    def get_last_combat_results(self) -> list:
        try:
            return self._engine.last_combat_results
        except Exception:
            return []

    def get_passive_buff_log(self, player_index: int = 0) -> list:
        try:
            return self._engine.players[player_index].passive_buff_log
        except Exception:
            return []

    def get_stats(self, player_index: int = 0) -> dict:
        try:
            return self._engine.players[player_index].stats
        except Exception:
            return {"wins": 0, "losses": 0, "draws": 0,
                    "market_rolls": 0, "evolutions": 0, "win_streak_max": 0}

    def has_catalyst(self, player_index: int = 0) -> bool:
        try:
            return bool(self._engine.players[player_index].board.has_catalyst)
        except Exception:
            return False

    def has_eclipse(self, player_index: int = 0) -> bool:
        try:
            return bool(self._engine.players[player_index].board.has_eclipse)
        except Exception:
            return False

    def get_interest_multiplier(self, player_index: int = 0) -> float:
        try:
            return float(self._engine.players[player_index].interest_multiplier)
        except Exception:
            return 1.0

    def get_turns_played(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].turns_played
        except Exception:
            return 0

    def get_prefix_bonus(self, player_index: int = 0) -> int:
        """Calculate the sum of all _prefix stats on the player's board, divided by 6."""
        try:
            # Phase 4 stub: implement real loop across board once Card.stats are exposed properly
            return getattr(self._engine.players[player_index], "_prefix_bonus", 0)
        except Exception:
            return 0

    def freeze_pairings(self) -> None:
        """
        Call swiss_pairs exactly once per turn and cache result.
        Stores both PID pairs (for UI display) and actual Player objects
        (for passing to combat_phase to prevent RNG re-roll — Blind Matchup fix).
        """
        try:
            pairs = self._engine.swiss_pairs()
            self._pairings_cache = [(a.pid, b.pid) for a, b in pairs]
            self._cached_pairs = pairs  # real Player objects for combat_phase(pairs=)
        except Exception:
            self._pairings_cache = []
            self._cached_pairs = []

    def get_current_opponent(self, player_index: int = 0) -> int:
        """Return the PID of the opponent the human is matched against this turn.
        Returns -1 if no match found.
        """
        try:
            human_pid = self._engine.players[player_index].pid
            for pid_a, pid_b in self._pairings_cache:
                if pid_a == human_pid:
                    return pid_b
                if pid_b == human_pid:
                    return pid_a
        except Exception:
            pass
        return -1


    def format_combat_logs(self, pid: int = 0) -> list[str]:
        """Phase 4: Engine loglarını Terminal Overlay stiline çevirir.
        Phase 5e Fix: Erken tur hasar sınırlarını (cap/penalty) açıkça gösterir."""
        lines = []
        try:
            # 1. Passive Buff Logları
            buffs = self.get_passive_buff_log(pid)
            for log in buffs:
                if "delta" in log and log.get("delta", 0) > 0:
                    delta = log["delta"]
                    trigger = log.get("trigger", "Combat")
                    lines.append(f"-> {trigger.upper()} tetiği ateşledi: +{delta} Puan")

            # 2. Results
            results = self.get_last_combat_results()
            if not results:
                return lines

            match = None
            for r in results:
                if r.get("pid_a") == pid or r.get("pid_b") == pid:
                    match = r
                    break
            
            if match:
                is_a = match["pid_a"] == pid
                opp_pid = match["pid_b"] if is_a else match["pid_a"]
                my_pts  = match["pts_a"] if is_a else match["pts_b"]
                opp_pts = match["pts_b"] if is_a else match["pts_a"]

                lines.append(f"SEN: Toplam Savaş Puanı = {my_pts}")
                lines.append(f"P{opp_pid}: Toplam Savaş Puanı = {opp_pts}")

                winner_pid = match.get("winner_pid")
                dmg = match.get("dmg", 0)
                turn = self.get_turn()

                # --- Phase 5e: Damage cap/penalty transparency ---
                if winner_pid not in (-1, pid):  # we lost
                    if turn <= 10:
                        lines.append(f"  (Erken Oyun Sınırı — Tur {turn}: max 15 hasar)")
                    if turn <= 5:
                        lines.append(f"  (Tur Penaltısı — Tur {turn}: hasar x0.5 uygulandı)")
                    elif turn <= 15:
                        mult = round(0.5 + (turn - 5) * 0.05, 2)
                        lines.append(f"  (Tur Çarpanı — Tur {turn}: hasar x{mult} uygulandı)")

                if match.get("draws", 0) > 0 or my_pts == opp_pts:
                    lines.append("SONUÇ: Berabere kalındı!")
                elif winner_pid == pid:
                    lines.append(f"SONUÇ: VICTORY! {dmg} Hasar vurdun!")
                else:
                    lines.append(f"SONUÇ: DEFEAT! -{dmg} HP Hasar aldın.")

        except Exception as e:
            lines.append(f"[SYS_ERROR] {e}")

        return lines

    def get_rarity_probabilities(self) -> dict[str, float]:
        """Dükkanda kart çıkma olasılıklarını (şu anki tura göre) hesapla."""
        if not self._engine or not self._engine.market:
            return {"1": 100.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0}
        
        from engine_core.market import _rarity_weight
        turn = self._engine.turn
        
        weights = {}
        total_w = 0.0
        for r in ["1", "2", "3", "4", "5"]:
            w = _rarity_weight(r, turn)
            weights[r] = w
            total_w += w
            
        if total_w <= 0: return {"1": 100.0}
        
        # Normalize to %
        return {r: (w / total_w) * 100.0 for r, w in weights.items()}

    def get_player_stats(self) -> list[dict]:
        """Phase 4: Sona eren oyunun skor tablosunu hazırlayıp HP/Puan durumuna göre sıralar."""
        try:
            players = self._engine.players
            stats = []
            for idx, p in enumerate(players):
                stats.append({
                    "name": self.get_display_name(idx),
                    "strategy": self.get_strategy(idx),
                    "hp": p.hp,
                    "total_pts": p.total_pts,
                    "alive": p.alive
                })
            
            # Sıralama: Önce hayatta olanlar (HP'ye göre yüksekten düşüğe), sonra ölenler (toplam puana göre yüksekten düşüğe)
            # Python sort stabildir, o yüzden puanla sıralayıp, sonra alive olup olmamakla sıralayabiliriz. Veya key kullanabiliriz.
            stats.sort(key=lambda x: (x["alive"], x["hp"], x["total_pts"]), reverse=True)
            
            # Rank ata
            for i, s in enumerate(stats):
                s["rank"] = i + 1
                
            return stats
        except Exception:
            return []

    def get_current_pairings(self) -> list:
        """Stored snapshot; MUST NOT reroll swiss pairs."""
        return self._pairings_cache

    def get_pool_copies(self) -> dict:
        try:
            return dict(self._engine.market.pool_copies)
        except Exception:
            return {}

    def get_passive_buff_log(self, player_index: int = 0) -> list:
        """Passive ability activation history for the UI feed."""
        if not self._engine:
            return []
        try:
            return self._engine.players[player_index].passive_buff_log
        except (AttributeError, IndexError):
            return []

    # ── Phase 7: Live Tactical Info ───────────────────────────────────
    def get_card_info(self, player_index: int, source: str, key: any):
        """
        Motor üzerindeki gerçek Card nesnesini bulur ve UI için CardData'ya dönüştürür.
        Bu sayede Prestige, Power gibi canlı stat değişimleri InfoBox'ta görünür.
        """
        if not self._engine or player_index >= len(self._engine.players):
            return None

        from v2.core.card_database import CardDatabase, CardData
        player = self._engine.players[player_index]
        card_obj = None

        try:
            if source == "shop":
                # Market windows PID bazlı tutulur
                pid = player.pid
                market = self._engine.market
                if pid in market._player_windows:
                    window = market._player_windows[pid]
                    if isinstance(key, int) and 0 <= key < len(window):
                        card_obj = window[key]

            elif source == "hand":
                if isinstance(key, int) and 0 <= key < len(player.hand):
                    card_obj = player.hand[key]

            elif source == "board":
                # key = (q, r) axial coordinate
                card_obj = player.board.grid.get(key)
        except Exception as e:
            print(f"[GameState] get_card_info error locating card: {e}")
            return None

        if not card_obj:
            # print(f"[DEBUG] get_card_info: Card NOT FOUND at {source}/{key}")
            return None

        # MetadataLookup (Evolved önekini temizle)
        raw_name = card_obj.name
        lookup_name = raw_name
        if raw_name.startswith("Evolved "):
            lookup_name = raw_name.replace("Evolved ", "", 1)
        
        base_data = CardDatabase.get().lookup(lookup_name)
        if not base_data:
            print(f"[DEBUG] get_card_info: Metadata NOT FOUND for {lookup_name}")
            return None

        # print(f"[DEBUG] get_card_info: Loading {raw_name} from {source} (Stats: {card_obj.stats.get('Prestige', 0)}P)")

        # Engine'den güncel statları alarak yeni bir CardData snapshot'ı oluştur
        live_data = CardData(
            name=raw_name, # "Evolved ..." ismini koru
            category=base_data.category,
            rarity=str(card_obj.rarity),
            stats=dict(card_obj.stats), # CANLI STATLAR
            passive_type=base_data.passive_type,
            passive_effect=base_data.passive_effect,
            synergy_group=base_data.synergy_group
        )
        return live_data
