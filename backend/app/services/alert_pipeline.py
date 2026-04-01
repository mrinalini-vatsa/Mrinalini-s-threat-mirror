import logging
import random
import time
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.decision import Decision
from app.models.enrichment import Enrichment
from app.models.enums import AlertStateType, DecisionType, Severity
from app.services.correlation_service import correlate_alert
from app.services.decision_service import make_decision
from app.services.enrichment_service import enrich_ip
from app.services.metrics_service import metrics_store
from app.services.state_service import add_state

logger = logging.getLogger(__name__)

KNOWN_BAD = [
    "185.220.101.4",
    "185.220.101.47",
    "103.45.67.89",
    "91.108.4.1",
    "45.33.32.156",
    "198.199.119.1",
    "162.247.74.27",
    "171.25.193.20",
]

SUSPICIOUS = [
    "62.171.188.15",
    "77.247.181.162",
    "89.234.157.254",
    "198.51.100.22",
    "203.0.113.45",
    "61.177.172.1",
    "180.76.15.143",
    "42.112.36.91",
]

CLEAN = [
    "8.8.8.8",
    "1.1.1.1",
    "104.21.45.67",
    "172.217.16.142",
    "13.107.42.14",
    "52.84.12.34",
]

KNOWN_BAD_SET = frozenset(KNOWN_BAD)
SUSPICIOUS_SET = frozenset(SUSPICIOUS)
CLEAN_SET = frozenset(CLEAN)

USERS = [
    "admin",
    "dev-01",
    "dev-02",
    "svc-api",
    "svc-payment",
    "svc-auth",
    "svc-db",
    "svc-proxy",
    "u-1001",
    "u-1088",
    "u-2001",
    "u-3045",
    "intern-01",
    "contractor-99",
    "backup-svc",
]

# Ordered attack narrative per IP (never skip steps).
CHAIN_EVENTS = ("PORT_SCAN", "LOGIN_FAILURE", "PRIV_ESCALATION", "MALWARE_BEACON")

_SEVERITY_ORDER = (Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL)

_CHAIN_COOLDOWN_SECONDS = 120.0

_ip_attack_state: dict[str, dict] = {}


def _severity_max(a: Severity, b: Severity) -> Severity:
    return _SEVERITY_ORDER[max(_SEVERITY_ORDER.index(a), _SEVERITY_ORDER.index(b))]


def _severity_bump(sev: Severity, levels: int) -> Severity:
    idx = _SEVERITY_ORDER.index(sev) + levels
    return _SEVERITY_ORDER[min(idx, len(_SEVERITY_ORDER) - 1)]


def _ip_category(ip: str) -> Literal["known_bad", "suspicious", "clean"]:
    if ip in KNOWN_BAD_SET:
        return "known_bad"
    if ip in SUSPICIOUS_SET:
        return "suspicious"
    return "clean"


def _pick_weighted_ip() -> str:
    r = random.random()
    if r < 0.5:
        pool = KNOWN_BAD
    elif r < 0.8:
        pool = SUSPICIOUS
    else:
        pool = CLEAN

    now = time.monotonic()
    available = [ip for ip in pool if _ip_attack_state.get(ip, {}).get("cooldown_until", 0) <= now]
    if not available:
        available = [ip for ip in pool]
    return random.choice(available)


def _ensure_state(ip: str) -> dict:
    if ip not in _ip_attack_state:
        _ip_attack_state[ip] = {
            "next_step": 0,
            "login_failure_emissions": 0,
            "cooldown_until": 0.0,
        }
    return _ip_attack_state[ip]


def _compute_severity(
    *,
    category: Literal["known_bad", "suspicious", "clean"],
    step_index: int,
    login_failure_emissions_before: int,
    prior_db_alert_count: int,
) -> Severity:
    if category == "clean":
        return Severity.LOW

    if step_index == 0:
        base = Severity.LOW
    elif step_index == 1:
        base = Severity.MEDIUM if login_failure_emissions_before == 0 else Severity.HIGH
    elif step_index == 2:
        base = Severity.HIGH
    else:
        base = Severity.CRITICAL

    if category == "known_bad":
        base = _severity_max(base, Severity.MEDIUM)

    if prior_db_alert_count > 0:
        bumps = 2 if category == "known_bad" else 1
        base = _severity_bump(base, bumps)

    return base


def _advance_chain_after_emit(ip: str, step_index: int) -> None:
    st = _ensure_state(ip)
    if step_index == 1:
        st["login_failure_emissions"] = st.get("login_failure_emissions", 0) + 1
    if step_index == len(CHAIN_EVENTS) - 1:
        st["next_step"] = 0
        st["cooldown_until"] = time.monotonic() + _CHAIN_COOLDOWN_SECONDS
    else:
        st["next_step"] = step_index + 1


async def generate_random_alert(session: AsyncSession) -> Alert:
    ip = _pick_weighted_ip()
    category = _ip_category(ip)
    st = _ensure_state(ip)
    step_index = int(st["next_step"])
    if step_index < 0 or step_index >= len(CHAIN_EVENTS):
        step_index = 0
        st["next_step"] = 0

    event_type = CHAIN_EVENTS[step_index]

    prior_count_result = await session.scalar(
        select(func.count()).select_from(Alert).where(Alert.ip_address == ip)
    )
    prior_db_alert_count = int(prior_count_result or 0)

    lf_before = int(st.get("login_failure_emissions", 0)) if step_index == 1 else 0
    severity = _compute_severity(
        category=category,
        step_index=step_index,
        login_failure_emissions_before=lf_before,
        prior_db_alert_count=prior_db_alert_count,
    )

    alert = Alert(
        ip_address=ip,
        user_id=random.choice(USERS),
        event_type=event_type,
        severity=severity,
    )
    session.add(alert)
    await session.flush()
    _advance_chain_after_emit(ip, step_index)

    await add_state(session, alert.id, AlertStateType.new, "Alert generated by autonomous worker")
    logger.info(
        "alert generated",
        extra={"alert_id": alert.id, "step": "alert_generation", "execution_time_ms": 0},
    )
    return alert


async def process_alert(session: AsyncSession, alert: Alert) -> None:
    start = time.perf_counter()
    try:
        enrich_start = time.perf_counter()
        enrichment_data = await enrich_ip(alert.ip_address)
        enrich_elapsed_ms = (time.perf_counter() - enrich_start) * 1000
        logger.info(
            "enrichment completed",
            extra={"alert_id": alert.id, "step": "enrichment", "execution_time_ms": round(enrich_elapsed_ms, 2)},
        )
        session.add(
            Enrichment(
                alert_id=alert.id,
                reputation_score=enrichment_data["reputation_score"],
                country=enrichment_data["country"],
                isp=enrichment_data["isp"],
                source=enrichment_data["source"],
            )
        )
        await add_state(session, alert.id, AlertStateType.enriched, "Enrichment completed")

        corr_start = time.perf_counter()
        repeated_count = await correlate_alert(session, alert)
        corr_elapsed_ms = (time.perf_counter() - corr_start) * 1000
        logger.info(
            "correlation completed",
            extra={"alert_id": alert.id, "step": "correlation", "execution_time_ms": round(corr_elapsed_ms, 2)},
        )
        decision_payload = make_decision(
            alert_id=alert.id,
            ip_category=_ip_category(alert.ip_address),
            event_type=alert.event_type,
            repeated_ip_count=repeated_count,
            reputation_score=enrichment_data["reputation_score"],
        )
        session.add(
            Decision(
                alert_id=alert.id,
                decision=DecisionType(decision_payload["decision"]),
                confidence=decision_payload["confidence"],
                reasons=decision_payload["reasons"],
                score=decision_payload["score"],
            )
        )
        await add_state(session, alert.id, AlertStateType.analyzed, "Decision engine completed")
        await session.commit()
        if decision_payload["decision"] == DecisionType.block.value:
            await metrics_store.record_blocked_alert()
        total_elapsed_ms = (time.perf_counter() - start) * 1000
        await metrics_store.record_processing_time(total_elapsed_ms)
        logger.info(
            "alert processed",
            extra={
                "alert_id": alert.id,
                "step": "pipeline_complete",
                "execution_time_ms": round(total_elapsed_ms, 2),
            },
        )
    except Exception:
        await session.rollback()
        await metrics_store.record_failure()
        logger.exception(
            "alert processing failed",
            extra={"alert_id": alert.id, "step": "pipeline_error", "execution_time_ms": 0},
        )
        raise


async def get_severity_distribution(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(select(Alert.severity))
    distribution: dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for row in rows.scalars().all():
        distribution[row.value] = distribution.get(row.value, 0) + 1
    return distribution
