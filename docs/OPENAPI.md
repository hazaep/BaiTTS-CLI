# API REST local — Contrato (Fase 3)

Servicio HTTP local (FastAPI) que orquesta el servidor MultiTTS (8774) y
expone OpenAPI. Base: `http://127.0.0.1:8100` por defecto.

> Estado: **diseño**. La implementación corresponde a la Fase 3 del roadmap.
> Se documenta ahora para que CLI y API compartan el mismo contrato.
> Decisiones consolidadas en [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) y
> extensiones en [`ADDITIONS.md`](ADDITIONS.md).

## Endpoints

| Método | Ruta          | Respuesta | Descripción |
|--------|---------------|-----------|-------------|
| GET    | `/health`     | JSON      | Estado del servicio + canary de síntesis (valida formato WAV) |
| GET    | `/voices`     | JSON      | Catálogo de voces (reenvío de 8774) |
| POST   | `/tts`        | audio     | Síntesis simple |
| POST   | `/dialog`     | audio/JSON| Guion multi-personaje → audio |
| GET    | `/audio/{id}` | audio     | Audio temporal (TTL ~1 h) |
| GET    | `/docs`       | HTML      | Swagger UI (FastAPI) |
| GET    | `/openapi.json`| JSON     | Especificación OpenAPI |

### Bind y auth

- **Default bind `127.0.0.1`** (loopback). El servidor 8774 de la APK binda
  `0.0.0.0` sin auth; **no** heredamos esa exposición por defecto.
- Flag `--bind 0.0.0.0` para exponer a la LAN.
- En loopback: **sin auth** (el token es fricción sin beneficio).
- Si se expone (flag): exigir **token simple** `Authorization: Bearer <token>`
  (un `if` en un middleware, no un subsistema). Ver `ADDITIONS.md` §5.

### `GET /health` — canary de síntesis

No se conforma con "¿8774 responde?". Ejecuta una síntesis corta
("hola", voz offline fija) y valida la respuesta:

1. Llamar a `/forward` con texto fijo y voz offline conocida.
2. Parsear con `wave` (o `audio.py`).
3. Validar: cabecera `RIFF/WAVE`, **1 canal, 24 000 Hz, 16-bit**, duración > 0.
4. `ok` solo si todo se cumple; si no, reportar qué falló (alcance, status,
   formato).

Es la mitigación principal del drift de formato de la APK. Ver `RISKS.md`.

## Modelos

### `POST /tts`

Request:

```json
{
  "text": "Hola mundo",
  "voice": "microsoft_es-MX-DaliaNeural-MiAndroidAccesible",
  "speed": 40,
  "pitch": 27,
  "volume": 45,
  "format": "wav",
  "cache": true
}
```

- `speed`, `pitch`, `volume` opcionales (defaults del servidor).
- `format`: `"wav"` (default) o `"mp3"` (requiere `ffmpeg`).
- `cache`: `true` (default) o `false` para forzar re-síntesis.

Response: `audio/wav` (o `audio/mpeg`) con el binario.

### `POST /dialog`

Request:

```json
{
  "script": "narrador: Era una noche...\n[pausa 800]\njuan (speed=-10): Hola.",
  "cast": {
    "narrador": {
      "voice": "microsoft_es-MX-DaliaNeural-MiAndroidAccesible",
      "speed": 40, "pitch": 27, "volume": 45, "pause_after": 400
    },
    "juan": {
      "preset": "juan",
      "speed": "+2"
    }
  },
  "format": "wav",
  "lrc": true,
  "cache": true,
  "normalize": false
}
```

- `script`: el guion en la sintaxis de `docs/DIALOG_SYNTAX.md`. El cast puede
  ir inline con `@personaje = ...` o `@personaje = @preset(nombre)` o en el
  campo `cast` (ambos se fusionan **por campo**; `cast` tiene prioridad).
- `cast.<personaje>.preset`: referencia a una voz preconfigurada del archivo
  de config (`config.toml`). Hereda `voice`, `speed`, `pitch`, `volume` y
  `pause_after` del preset.
- Los valores en `cast` y en los overrides del guion aceptan sintaxis
  **absoluta** (`40`) o **relativa** (`"+2"`, `"-10"`). Los deltas se aplican
  sobre el valor efectivo resuelto. Ver `DISTRIBUTED.md` §6.
- `lrc`: si `true`, la respuesta incluye el LRC.
- `cache`: `true` (default) o `false` (re-síntesis forzada).
- `normalize`: `false` (default) o `true` (normalización de loudness).

Response (cuando `lrc: false`): `audio/wav` (o `audio/mpeg`).

Response (cuando `lrc: true`): `application/json`

```json
{
  "audio_url": "/audio/a1b2c3d4",
  "audio_url_ttl_seconds": 3600,
  "lrc": "[ar:...]\n[00:00.00]Era una noche...",
  "chunks": [
    { "speaker": "narrador", "text": "Era una noche...", "start_ms": 0, "duration_ms": 2400,
      "voice": "microsoft_es-MX-DaliaNeural-MiAndroidAccesible", "speed": 40, "pitch": 27, "volume": 45 },
    { "speaker": "juan", "text": "Hola.", "start_ms": 3200, "duration_ms": 700,
      "voice": "microsoft_es-MX-JorgeNeural-MiAndroidAccesible", "speed": 42, "pitch": 27, "volume": 48 }
  ]
}
```

- **Entrega por URL temporal**, no base64 embebido: un WAV de 10 min ≈ 28 MB,
  en base64 = 37 MB dentro de un JSON. Ver `ADDITIONS.md` §4.
- `id` aleatorio, TTL configurable (default 1 h), purga al expirar.
- Opcional `?inline=true` en `POST /dialog` para quien quiera el binario
  directo.
- El array `chunks` incluye `voice/speed/pitch/volume` por chunk: alimenta la
  ETA del dashboard y la gestión de cast.

## Decisiones (consolidadas)

- **Framework:** FastAPI + uvicorn (OpenAPI automático).
- **Puerto:** `8100` (8774 es del MultiTTS).
- **Bind:** `127.0.0.1` por defecto; exponer es opt-in con token.
- **Auth:** sin auth en loopback; `Bearer` token si se expone.
- **Entrega de audio + LRC:** URL temporal + contenido LRC en la misma
  respuesta (no base64).
- **Healthcheck:** canary de síntesis con validación de formato WAV.
