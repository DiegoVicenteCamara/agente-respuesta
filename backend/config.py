import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class Settings:
    def __init__(self) -> None:
        self.livekit_url: str = _get("LIVEKIT_URL")
        self.livekit_api_key: str = _get("LIVEKIT_API_KEY")
        self.livekit_api_secret: str = _get("LIVEKIT_API_SECRET")
        self.openai_api_key: str = _get("OPENAI_API_KEY")
        self.openai_realtime_model: str = _get("OPENAI_REALTIME_MODEL", "gpt-realtime")
        self.openai_realtime_voice: str = _get("OPENAI_REALTIME_VOICE", "coral")
        self.openai_planner_model: str = _get("OPENAI_PLANNER_MODEL", "gpt-4o-mini")
        self.tavily_api_key: str = _get("TAVILY_API_KEY")
        self.redis_url: str = _get("REDIS_URL", "redis://localhost:6379/0")
        self.event_channel: str = _get("EVENT_CHANNEL", "agent_updates")
        self.agent_name: str = _get("AGENT_NAME", "agente-respuesta")
        self.http_port: int = int(_get("HTTP_PORT", "7860"))
        self.token_ttl: timedelta = timedelta(hours=1)
        self.typesafe_api_key: str = _get("TYPESAFE_API_KEY")
        self.typesafe_model: str = _get("TYPESAFE_MODEL", "jev-latest")
        self.typesafe_base_url: str = _get("TYPESAFE_BASE_URL", "https://api.typesafe.ai")
        self.openai_fast_model: str = _get("OPENAI_FAST_MODEL", "gpt-4o-mini")
        self.openai_advanced_model: str = _get("OPENAI_ADVANCED_MODEL", "gpt-4o")
        self.routing_risk_fast: float = float(_get("ROUTING_RISK_FAST", "0.5"))
        self.routing_risk_critical: float = float(_get("ROUTING_RISK_CRITICAL", "1.5"))
        self.routing_injection_threshold: float = float(
            _get("ROUTING_INJECTION_THRESHOLD", "0.85")
        )
        self.routing_confidence_min: float = float(_get("ROUTING_CONFIDENCE_MIN", "0.6"))
        self.routing_timeout_ms: int = int(_get("ROUTING_TIMEOUT_MS", "2000"))


settings = Settings()