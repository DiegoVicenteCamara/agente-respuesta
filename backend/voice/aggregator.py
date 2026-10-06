"""Acumulador de interrupciones proactivas por voz (issue #47).

Agrupa los eventos ``info`` que llegan en ráfaga en una sola intervención
hablada. Lógica pura y testeable junto a ``notifier.py``:

- ``silent`` (y todo lo que ``notifier.build_spoken_update`` calla) nunca
  se habla ni se acumula.
- ``info`` se acumula; ``flush()`` combina lo pendiente en un único texto.
- ``urgent`` interrumpe de inmediato y vacía el lote pendiente: devuelve
  primero el texto urgente y justo después el lote (sin perderse), o
  fusionado si se prefiere hablarlo en una sola llamada (ver ``add``).

El timeout (ventana de agregación) lo gestiona el listener
(``backend/voice/agent.py``) con ``NOTIFY_AGGR_WINDOW_MS``; aquí solo se
acumula y se combina texto.
"""

from backend.voice import notifier


def _raw_message(payload: dict) -> str:
    return str(payload.get("message", "")).strip()


def combine_infos(messages: list[str]) -> str | None:
    """Combina N mensajes ``info`` en un único texto a hablar."""
    clean = [str(m).strip() for m in messages if str(m).strip()]
    if not clean:
        return None
    if len(clean) == 1:
        return f"Disculpa que te interrumpa, {clean[0]}"
    joined = "; ".join(clean)
    return f"Disculpa que te interrumpa, tengo {len(clean)} avances: {joined}"


class UpdateAggregator:
    """Acumula eventos ``info`` para hablarlos en una sola intervención."""

    def __init__(self) -> None:
        self._pending: list[str] = []

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def add(self, payload: dict) -> list[str]:
        """Procesa un evento; devuelve los textos a hablar de inmediato.

        - ``silent`` / no hablable -> ``[]`` (ni habla ni acumula).
        - ``info`` hablable -> se acumula, devuelve ``[]`` (hablará en flush).
        - ``urgent`` hablable -> devuelve ``[urgente]`` o
          ``[urgente, lote]`` si había lote pendiente (el lote se vacía y se
          anuncia justo después, sin perderse).
        """
        try:
            text = notifier.build_spoken_update(payload)
        except (TypeError, AttributeError):
            return []
        if not text:
            return []
        try:
            priority = notifier.classify(payload)
        except (TypeError, AttributeError):
            priority = notifier.INFO
        if priority == notifier.URGENT:
            urgent_text = text
            pending_text = self.flush()
            if pending_text:
                return [urgent_text, pending_text]
            return [urgent_text]
        if priority == notifier.SILENT:
            return []
        # info (o prioridad desconocida hablable): acumular mensaje crudo.
        raw = _raw_message(payload)
        if not raw:
            return []
        self._pending.append(raw)
        return []

    def flush(self) -> str | None:
        """Vacía el lote pendiente en un único texto, o ``None`` si vacío."""
        if not self._pending:
            return None
        messages = self._pending
        self._pending = []
        return combine_infos(messages)
