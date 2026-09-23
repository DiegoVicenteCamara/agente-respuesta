"""Earcon (tono previo) antes de cada interrupción proactiva por voz.

El tono se reproduce a través del ``AgentSession`` (``session.say`` con
frames de audio propios), de modo que lo oye la persona en la llamada
LiveKit y no suena por el altavoz del servidor.

Política (no cambia ``notifier``): suena solo para prioridades ``info`` /
``urgent``; los eventos ``silent`` (y todo lo que ``notifier`` calla)
permanecen mudos. Desactivado por defecto (``EARCON_ENABLED``).
"""

import logging
import math
import struct
import wave
from collections.abc import AsyncIterator
from pathlib import Path

from livekit import rtc

from backend.config import settings
from backend.voice import notifier

logger = logging.getLogger(__name__)

#: Prioridades que disparan el earcon. ``silent`` nunca suena.
EARCON_PRIORITIES = frozenset({notifier.INFO, notifier.URGENT})

SAMPLE_RATE = 24000
NUM_CHANNELS = 1
TONE_FREQUENCY_HZ = 880.0
TONE_DURATION_MS = 300
FRAME_SAMPLES = 240  # 10 ms a 24 kHz


def should_play(payload: dict) -> bool:
    """Dice si este evento debe sonar (flag activo + prioridad audible)."""
    if not settings.earcon_enabled:
        return False
    try:
        priority = notifier.classify(payload)
    except (AttributeError, TypeError):
        return False
    return priority in EARCON_PRIORITIES


async def synthesize_tone(
    duration_ms: int = TONE_DURATION_MS,
    frequency_hz: float = TONE_FREQUENCY_HZ,
    sample_rate: int = SAMPLE_RATE,
) -> AsyncIterator[rtc.AudioFrame]:
    """Genera un tono sinusoidal como frames de audio PCM int16 mono."""
    total = int(sample_rate * duration_ms / 1000)
    amplitude = int(0.3 * 32767)
    pcm = bytearray()
    for i in range(total):
        sample = int(amplitude * math.sin(2 * math.pi * frequency_hz * i / sample_rate))
        pcm += struct.pack("<h", sample)
    bytes_per_frame = FRAME_SAMPLES * NUM_CHANNELS * 2
    for offset in range(0, len(pcm), bytes_per_frame):
        chunk = bytes(pcm[offset : offset + bytes_per_frame])
        n = len(chunk) // (NUM_CHANNELS * 2)
        if n == 0:
            break
        yield rtc.AudioFrame(
            data=chunk,
            sample_rate=sample_rate,
            num_channels=NUM_CHANNELS,
            samples_per_channel=n,
        )


async def load_audio_frames(path: str | Path) -> AsyncIterator[rtc.AudioFrame]:
    """Lee un .wav PCM y lo trocea en frames; falla si no es PCM int16/8bit."""
    with wave.open(str(path), "rb") as wav:
        sample_rate = wav.getframerate()
        num_channels = wav.getnchannels()
        sampwidth = wav.getsampwidth()
        if sampwidth not in (1, 2):
            raise ValueError(f"Earcon WAV no soportado (sampwidth={sampwidth})")
        frames_per_chunk = 240
        while True:
            raw = wav.readframes(frames_per_chunk)
            if not raw:
                break
            if sampwidth == 1:
                # PCM 8-bit sin signo -> int16
                raw = b"".join(
                    struct.pack("<h", (b - 128) * 256) for b in raw
                )
            n = len(raw) // (num_channels * 2)
            if n == 0:
                break
            yield rtc.AudioFrame(
                data=raw,
                sample_rate=sample_rate,
                num_channels=num_channels,
                samples_per_channel=n,
            )


def _audio_source() -> AsyncIterator[rtc.AudioFrame]:
    """Elige el asset configurado o el tono sintetizado de respaldo."""
    configured = (settings.earcon_path or "").strip()

    async def _gen() -> AsyncIterator[rtc.AudioFrame]:
        if configured:
            try:
                async for frame in load_audio_frames(configured):
                    yield frame
                return
            except (OSError, wave.Error, ValueError, EOFError) as exc:
                logger.warning(
                    "Earcon %s ilegible (%s); uso tono sintetizado",
                    configured,
                    exc,
                )
        async for frame in synthesize_tone():
            yield frame

    return _gen()


async def play_earcon(session, payload: dict) -> bool:
    """Reproduce el earcon por la sesión si el evento lo requiere.

    Devuelve ``True`` si se emitió el tono. Nunca eleva excepciones:
    un earcon roto no debe impedir la interrupción hablada posterior.
    """
    if not should_play(payload):
        return False
    try:
        handle = session.say(
            " ",
            audio=_audio_source(),
            allow_interruptions=False,
            add_to_chat_ctx=False,
        )
        wait = getattr(handle, "wait_for_playout", None)
        if wait is not None:
            await wait()
        else:
            await handle
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Fallo al reproducir el earcon")
        return False
