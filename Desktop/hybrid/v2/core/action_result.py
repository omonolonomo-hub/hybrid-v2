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
