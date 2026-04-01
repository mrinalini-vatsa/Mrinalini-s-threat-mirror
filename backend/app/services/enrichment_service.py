import logging
import random
import time

from app.core.config import get_settings
from app.utils.http import fetch_json

logger = logging.getLogger(__name__)
settings = get_settings()
_CACHE_TTL_SECONDS = 300
_enrichment_cache: dict[str, tuple[float, dict]] = {}


async def enrich_ip(ip_address: str) -> dict:
    now = time.time()
    cached = _enrichment_cache.get(ip_address)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        logger.info(
            "enrichment cache hit",
            extra={"alert_id": None, "step": "enrichment_cache", "execution_time_ms": 0},
        )
        return cached[1]

    if random.random() < 0.10:
        logger.error(
            "simulated enrichment failure",
            extra={"alert_id": None, "step": "enrichment_simulation", "execution_time_ms": 0},
        )
        raise RuntimeError("Simulated enrichment failure")

    if not settings.abuseipdb_api_key:
        result = {"reputation_score": 10, "country": "Unknown", "isp": "Unknown", "source": "Mock"}
        _enrichment_cache[ip_address] = (time.time(), result)
        return result

    abuseipdb_data = await fetch_json(
        "https://api.abuseipdb.com/api/v2/check",
        headers={"Key": settings.abuseipdb_api_key, "Accept": "application/json"},
        params={"ipAddress": ip_address, "maxAgeInDays": "90"},
    )
    abuse_data = abuseipdb_data.get("data", {})
    reputation = int(abuse_data.get("abuseConfidenceScore", 0))
    country = abuse_data.get("countryCode", "Unknown")
    isp = abuse_data.get("isp", "Unknown")

    if settings.virustotal_api_key:
        try:
            vt_data = await fetch_json(
                f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}",
                headers={"x-apikey": settings.virustotal_api_key},
            )
            stats = vt_data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            malicious = int(stats.get("malicious", 0))
            reputation = min(100, reputation + malicious * 5)
        except Exception:
            logger.exception("VirusTotal enrichment failed, continuing with AbuseIPDB signal")

    result = {"reputation_score": reputation, "country": country, "isp": isp, "source": "AbuseIPDB+VT"}
    _enrichment_cache[ip_address] = (time.time(), result)
    return result
