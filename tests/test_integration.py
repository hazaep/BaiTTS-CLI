"""Tests de integración contra el servidor MultiTTS real (127.0.0.1:8774).

Se saltan automáticamente si el servidor no está disponible.
"""

import json
import os
import wave

import pytest
import requests

from mtts.api import get_voices, text_to_speech

API_URL = "http://127.0.0.1:8774"


def _server_up():
    try:
        r = requests.get(API_URL + "/voices", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _server_up(),
    reason="Servidor MultiTTS no disponible en 127.0.0.1:8774",
)


def test_get_voices_shape():
    data = get_voices(API_URL)
    assert data["success"] is True
    assert "catalog" in data["data"]
    all_voices = []
    for engine in data["data"]["catalog"]:
        all_voices.extend(data["data"]["catalog"][engine])
    assert len(all_voices) > 0
    # Cada voz tiene los campos mínimos
    for v in all_voices[:5]:
        assert "id" in v
        assert "name" in v


def test_text_to_speech_returns_valid_wav():
    audio = text_to_speech(
        API_URL,
        "Hola, esto es una prueba.",
        {"voice": "microsoft_es-MX-DaliaNeural-MiAndroidAccesible"},
    )
    assert isinstance(audio, bytes) and len(audio) > 44  # cabecera WAV mínima
    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"

    with wave.open(__import__("io").BytesIO(audio), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getframerate() == 24000
        assert w.getsampwidth() == 2
        assert w.getnframes() > 0
