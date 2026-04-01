from app.models.enums import DecisionType


def make_decision(reputation: int, repeated_ip_count: int) -> dict:
    score = reputation
    reasons: list[str] = []
    if reputation > 80:
        score += 20
        reasons.append(
            "Abuse confidence is above 80, indicating historically malicious or abusive source behavior"
        )
    if repeated_ip_count > 0:
        score += min(20, repeated_ip_count * 5)
        reasons.append(
            f"IP is recurring across {repeated_ip_count} prior alerts, increasing likelihood of coordinated activity"
        )

    if score >= 90:
        decision = DecisionType.block.value
    elif score >= 60:
        decision = DecisionType.escalate.value
    else:
        decision = DecisionType.ignore.value

    confidence = min(0.99, max(0.40, score / 100))
    if not reasons:
        reasons.append("No high-risk telemetry or repetition pattern detected for this alert")
    return {"decision": decision, "confidence": confidence, "reasons": reasons, "score": score}
