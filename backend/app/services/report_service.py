import json

from app.core.config import get_settings
from app.utils.http import post_json

settings = get_settings()


async def generate_incident_report(payload: dict) -> str:
    if not settings.gemini_api_key:
        return (
            "Summary: Alert analyzed with available telemetry.\n"
            "Evidence: " + json.dumps(payload.get("evidence", {})) + "\n"
            "Decision: " + payload.get("decision", "UNKNOWN") + "\n"
            "Recommendation: Review endpoint and monitor for recurrence."
        )

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Generate a concise SOC incident report with sections: summary, evidence, "
                            "decision, recommendation. Input: " + json.dumps(payload)
                        )
                    }
                ]
            }
        ]
    }
    response = await post_json(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        headers={"x-goog-api-key": settings.gemini_api_key, "Content-Type": "application/json"},
        payload=body,
    )
    candidates = response.get("candidates", [])
    if not candidates:
        return "Summary: No report generated."
    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "Summary: No report generated.")
