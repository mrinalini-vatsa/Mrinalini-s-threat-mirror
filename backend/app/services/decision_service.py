from app.models.enums import DecisionType


def _confidence_from_alert_id(alert_id: int, low_pct: int, high_pct: int) -> float:
    span = high_pct - low_pct + 1
    return (low_pct + (alert_id % span)) / 100.0


def make_decision(
    *,
    alert_id: int,
    ip_category: str,
    event_type: str,
    repeated_ip_count: int,
    reputation_score: int,
) -> dict:
    """
    Decision rules (non-random):
    - CLEAN → IGNORE, confidence 85–95%
    - SUSPICIOUS first offence → MONITOR, 60–75%
    - SUSPICIOUS repeat → ESCALATE, 75–90%
    - KNOWN_BAD any alert → BLOCK, 90–99%
    - MALWARE_BEACON → BLOCK immediately, 99%
    """
    reasons: list[str] = []
    score = reputation_score

    if event_type == "MALWARE_BEACON":
        reasons.append("Malware beacon stage in attack chain requires immediate containment")
        return {
            "decision": DecisionType.block.value,
            "confidence": 0.99,
            "reasons": reasons,
            "score": max(score, 99),
        }

    if ip_category == "clean":
        reasons.append("Benign-reputation source; treating as low-fidelity false positive")
        return {
            "decision": DecisionType.ignore.value,
            "confidence": _confidence_from_alert_id(alert_id, 85, 95),
            "reasons": reasons,
            "score": min(score, 40),
        }

    if ip_category == "known_bad":
        if reputation_score > 80:
            reasons.append(
                "Abuse confidence is above 80, indicating historically malicious or abusive source behavior"
            )
            score = min(100, score + 20)
        reasons.append("Source IP is in the known-malicious cohort; default stance is block")
        return {
            "decision": DecisionType.block.value,
            "confidence": _confidence_from_alert_id(alert_id, 90, 99),
            "reasons": reasons,
            "score": max(score, 90),
        }

    # suspicious
    if reputation_score > 80:
        reasons.append(
            "Abuse confidence is above 80, indicating historically malicious or abusive source behavior"
        )
        score = min(100, score + 20)
    if repeated_ip_count > 0:
        reasons.append(
            f"IP is recurring across {repeated_ip_count} prior alerts, increasing likelihood of coordinated activity"
        )
        score = min(100, score + min(20, repeated_ip_count * 5))
        return {
            "decision": DecisionType.escalate.value,
            "confidence": _confidence_from_alert_id(alert_id, 75, 90),
            "reasons": reasons,
            "score": score,
        }

    reasons.append("First observation from a suspicious tier source; watch and correlate before hard action")
    return {
        "decision": DecisionType.monitor.value,
        "confidence": _confidence_from_alert_id(alert_id, 60, 75),
        "reasons": reasons,
        "score": score,
    }
