"""Telefonía SIP/PSTN: entrada real y llamadas salientes.

Diseño: el plano de voz (<800 ms, LiveKit) sigue desacoplado del plano de
ejecución (Celery) vía el bus Redis. Este módulo solo envuelve el acceso a
la API SIP de LiveKit:

- **Entrante:** LiveKit encamina la llamada del trunk inbound a una room
  normal vía dispatch rule, así que el mismo ``voice_entrypoint`` atiende
  WebRTC y PSTN. Aquí solo se detecta el número llamante
  (``extract_caller_phone``) para una posible rellamada.
- **Saliente:** ``place_outbound_call`` crea un participante SIP
  (``CreateSIPParticipant``) en la room indicada.

Todo el acceso a red pasa por un cliente inyectable para que los tests
usen mocks (cero coste real).
"""

import logging
import re
import uuid

from backend.config import settings

logger = logging.getLogger(__name__)

_E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")

# Número llamante por clave de sesión (``tools._session_key`` o room name).
CALLERS: dict[str, str] = {}


class SIPConfigError(RuntimeError):
    """La telefonía SIP no está configurada (trunk / flag)."""


def sip_enabled() -> bool:
    """Indica si las llamadas salientes están habilitadas y configuradas."""
    return bool(settings.sip_enabled and settings.sip_trunk_id)


def normalize_phone(raw: str) -> str:
    """Valida y normaliza un número a E.164 (``+`` + país + dígitos)."""
    phone = re.sub(r"[\s\-().]", "", (raw or "").strip())
    if not phone.startswith("+"):
        raise ValueError(
            f"Número inválido {raw!r}: usa formato E.164 (ej. +34910000000)"
        )
    if not _E164_RE.match(phone):
        raise ValueError(
            f"Número inválido {raw!r}: usa formato E.164 (ej. +34910000000)"
        )
    return phone


def register_caller(session_key: str, phone_number: str) -> str:
    """Guarda el número llamante para una posible rellamada al colgar."""
    phone = normalize_phone(phone_number)
    CALLERS[session_key] = phone
    return phone


def pop_caller(session_key: str) -> str | None:
    """Consume el número registrado (lo elimina del registro)."""
    return CALLERS.pop(session_key, None)


def peek_caller(session_key: str) -> str | None:
    """Consulta el número registrado sin eliminarlo."""
    return CALLERS.get(session_key)


def pending_callback_for(session_key: str) -> str | None:
    """Devuelve el teléfono a rellamar si quedan subagentes pendientes.

    Hay rellamada cuando la sesión tiene una tarea Celery activa en
    ``tools.ACTIVE_TASKS`` y un número llamante registrado.
    """
    from backend.voice import tools

    if session_key not in tools.ACTIVE_TASKS:
        return None
    return CALLERS.get(session_key)


def snapshot_active_task_ids() -> set[str]:
    """Foto de los task_id activos (para difuminar por job al colgar)."""
    from backend.voice import tools

    return {str(entry["task_id"]) for entry in tools.ACTIVE_TASKS.values()}


def session_pending_task_ids(before: set[str]) -> list[str]:
    """Task_ids creados durante la sesión que siguen activos al colgar."""
    from backend.voice import tools

    current = {str(entry["task_id"]) for entry in tools.ACTIVE_TASKS.values()}
    return sorted(tid for tid in current if tid not in before)


def extract_caller_phone(room) -> str | None:
    """Extrae el número llamante SIP de los participantes remotos de la room.

    Busca atributos típicos del participante SIP (``sip.phoneNumber``,
    ``sip_phone_number``, ``phoneNumber``) o identidades con formato E.164.
    Devuelve ``None`` si no hay origen SIP (p. ej. navegador WebRTC).
    """
    participants = []
    try:
        remote = getattr(room, "remote_participants", None)
        if isinstance(remote, dict):
            participants = list(remote.values())
        elif remote is not None:
            participants = list(remote)
    except TypeError:
        return None
    for participant in participants:
        candidates: list[str] = []
        attributes = getattr(participant, "attributes", None) or {}
        if isinstance(attributes, dict):
            for key in ("sip.phoneNumber", "sip_phone_number", "phoneNumber", "phone_number"):
                value = attributes.get(key)
                if value:
                    candidates.append(str(value))
        for attr in ("identity", "name"):
            value = getattr(participant, attr, None)
            if value:
                candidates.append(str(value))
        for candidate in candidates:
            try:
                return normalize_phone(candidate)
            except ValueError:
                continue
    return None


def _build_request(phone_number: str, room_name: str, participant_identity: str):
    from livekit.api import CreateSIPParticipantRequest

    return CreateSIPParticipantRequest(
        room_name=room_name,
        participant_identity=participant_identity,
        sip_trunk_id=settings.sip_trunk_id,
        sip_call_to=phone_number,
    )


def _default_api_client():
    from livekit.api import LiveKitAPI

    return LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )


async def place_outbound_call(
    phone_number: str,
    room_name: str,
    participant_identity: str | None = None,
    api_client=None,
) -> dict:
    """Marca al número indicado vía ``CreateSIPParticipant`` (llamada saliente).

    Args:
        phone_number: destino en E.164.
        room_name: room donde debe entrar el participante SIP.
        participant_identity: identidad del participante SIP (auto si None).
        api_client: cliente LiveKit inyectable (tests); por defecto LiveKitAPI.

    Raises:
        SIPConfigError: si la telefonía SIP no está configurada.
        ValueError: si el teléfono no es E.164 válido.
        RuntimeError: si LiveKit rechaza la marcación.
    """
    phone = normalize_phone(phone_number)
    if not room_name or not room_name.strip():
        raise ValueError("room_name no puede estar vacío")
    if not sip_enabled():
        raise SIPConfigError(
            "SIP no configurado: define SIP_ENABLED=true y SIP_TRUNK_ID en .env"
        )
    identity = participant_identity or f"callback-{uuid.uuid4().hex[:8]}"
    request = _build_request(phone, room_name.strip(), identity)
    client = api_client
    owned = False
    if client is None:
        client = _default_api_client()
        owned = True
    try:
        info = await client.sip.create_sip_participant(request)
        logger.info("Llamada saliente a %s en room %s", phone, room_name)
    except SIPConfigError:
        raise
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("No se pudo marcar al %s", phone)
        raise RuntimeError(f"No se pudo llamar al {phone}: {exc}") from exc
    finally:
        if owned:
            aclose = getattr(client, "aclose", None)
            if aclose is not None:
                try:
                    await aclose()
                except Exception:  # noqa: BLE001
                    pass
    participant_id = getattr(info, "participant_id", "") or ""
    return {
        "phone_number": phone,
        "room": room_name.strip(),
        "participant_identity": identity,
        "participant_id": participant_id,
    }
