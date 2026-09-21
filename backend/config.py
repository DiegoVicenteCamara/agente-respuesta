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


settings = Settings()