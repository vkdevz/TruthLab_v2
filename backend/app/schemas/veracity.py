from enum import Enum


class VeracityLabel(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    MISLEADING = "MISLEADING"
    OUTDATED = "OUTDATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class StanceType(str, Enum):
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    NEUTRAL = "NEUTRAL"


class ModalityType(str, Enum):
    TEXT = "TEXT"
    URL = "URL"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
