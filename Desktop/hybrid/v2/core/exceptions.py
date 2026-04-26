# ---------------------------------------------------------------------------
# Autochess Hybrid — Özel Exception Hiyerarşisi
#
# Kural: Tüm istisna yakalama işlemleri AutochessException veya alt sınıfları
#        üzerinden yapılmalıdır.  Gerçek RuntimeError/Exception yakalamak
#        isteniyorsa açıkça yazgılmalı; kazanımlı (implicit) yakalama yasaktır.
#
# Hiyerarşi:
#   AutochessException
#   ├── EngineException
#   │   └── IllegalActionError
#   ├── UIException
#   │   └── AssetLoadError
#   └── DatabaseError
# ---------------------------------------------------------------------------


class AutochessException(Exception):
    """Tüm oyuna özel istisnanın temel sınıfı."""


class EngineException(AutochessException):
    """Motor (engine_core) içindeki dahili hatalar için."""


class UIException(AutochessException):
    """UI bileşenlerinin başlatma veya render hataları için."""


class AssetLoadError(UIException):
    """Gerekli oyun varlığı (ses, görsel) yüklenemediğinde.

    Dikkat: Artık RuntimeError'dan türetilmiyor.  Yakalamak için
    ``except AssetLoadError`` veya ``except AutochessException`` kullanın.
    """


class IllegalActionError(EngineException):
    """Oyuncu kural ihlali yapan bir eylem denediğinde."""


class DatabaseError(AutochessException):
    """Kart/pasif veritabanı sorgusu başarısız olduğunda.

    Tipik sebep: ``CardDatabase.get()`` ``initialize()`` öncesinde çağrıldı.
    Dikkat: Artık RuntimeError'dan türetilmiyor.  Yakalamak için
    ``except DatabaseError`` veya ``except AutochessException`` kullanın.
    """
