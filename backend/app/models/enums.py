import enum


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStateType(str, enum.Enum):
    new = "NEW"
    enriched = "ENRICHED"
    analyzed = "ANALYZED"
    resolved = "RESOLVED"


class DecisionType(str, enum.Enum):
    ignore = "IGNORE"
    escalate = "ESCALATE"
    block = "BLOCK"
