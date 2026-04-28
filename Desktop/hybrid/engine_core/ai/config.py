# <<< TRAINED_PARAMS_START >>>
# Bu blok train_strategies.py tarafından otomatik oluşturuldu.
# Kullanım: from engine_core.ai import TRAINED_PARAMS
#           ai = ParameterizedAI(TRAINED_PARAMS)
#
# Phase 1: Tüm stratejiler için varsayılan parametreler.
# train_strategies.py --apply ile bu blok güncellenir.
TRAINED_PARAMS = {
    "economist": {
        # Backward compat params
        "thresh_high":          27.012525825899594,
        "thresh_mid":            5.887870123764179,
        "thresh_low":           11.572130722067811,
        "buy_2_thresh":         15.0,
        # Phase params
        "greed_turn_end":        6.556475060280888,
        "spike_turn_end":       14.773731014667712,
        "greed_gold_thresh":    15.0,
        "spike_r4_thresh":      42.07452062733782,
        "convert_r5_thresh":    80.0,
        "spike_buy_count":       3.1891953600814538,
        "convert_buy_count":     3.6086842743641023,
    },
    "warrior": {
        "power_weight":  1.0,
        "rarity_weight": 0.0,
    },
    "builder": {
        "combo_weight":         0.5,    # combo/synergy skorunun ana ağırlığı
        "power_weight":         0.4,    # power tie-break / güvenlik ağırlığı
        # Economist economy model copied into builder
        "greed_turn_end":        5.0,
        "spike_turn_end":       14.773731014667712,
        "greed_gold_thresh":     8.0,
        "spike_r4_thresh":      42.07452062733782,
        "convert_r5_thresh":    80.0,
        "spike_buy_count":       2.0,
        "convert_buy_count":     3.0,
    },
    "evolver": {
        "evo_near_bonus":     1000.0,
        "evo_one_bonus":       500.0,
        "rarity_weight_mult":   10.0,
        "power_weight":          1.0,
    },
    "balancer": {
        "group_bonus":  5.0,
        "group_thresh": 3.0,
        "power_weight": 1.0,
    },
    "rare_hunter": {
        "fallback_rarity": 3.0,
    },
    "tempo": {
        "power_center_thresh": 45.0,
        "combo_center_weight":  1.5,
    },
    "random": {},
}
# <<< TRAINED_PARAMS_END >>>

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ===================================================================
# AI CONFIGURATION ERROR
# ===================================================================

class AIConfigError(Exception):
    """Raised when AI strategy configuration is invalid or missing.

    This exception is for descriptive error reporting only — the AI module
    remains crash-proof (load_all_strategy_params returns {} on failure).
    AIConfigError can be used by callers who want to distinguish config
    errors from other issues.
    """
    pass


def load_all_strategy_params() -> Dict[str, Dict[str, Any]]:
    """Phase 1: Tüm stratejiler için JSON parametrelerini tek seferde yükle.

    trained_params.json formatı:
        {
            "economist": {"greed_turn_end": 7, ...},
            "warrior":   {"power_weight": 1.2, ...},
            ...
        }

    Crash-proof: herhangi bir hata durumunda {} döner, asla exception fırlatmaz.
    Yükleme sadece ParameterizedAI.__init__() sırasında bir kez yapılır;
    runtime'da JSON'a tekrar erişilmez (zero performance regression).

    File location: project_root/trained_params.json
    """
    try:
        path = Path(__file__).parent.parent.parent / "trained_params.json"
        if not path.exists():
            logger.info("AI config file not found at %s — using defaults only", path)
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.warning("AI config file %s is not a dict (type=%s) — using defaults only",
                           path, type(data).__name__)
            return {}
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    except json.JSONDecodeError as e:
        logger.warning("AI config file has invalid JSON at %s: %s — using defaults only",
                       path, e)
        return {}
    except IOError as e:
        logger.warning("AI config file could not be read at %s: %s — using defaults only",
                       path, e)
        return {}
    except KeyError as e:
        logger.warning("AI config file unexpected structure at %s: KeyError %s — using defaults only",
                       path, e)
        return {}


def load_strategy_params() -> Dict[str, Any]:
    """Backward compat: sadece economist parametrelerini döndürür.

    Phase 0'dan kaladan eski arayüz. Phase 1'de bu fonksiyonu çağıran
    kod varsa çalışmaya devam eder; ancak yeni kod load_all_strategy_params()
    kullanmalıdır.

    .. deprecated::
        Use load_all_strategy_params() instead.
    """
    logger.debug("load_strategy_params() is deprecated — use load_all_strategy_params() instead")
    return load_all_strategy_params().get("economist", {})
