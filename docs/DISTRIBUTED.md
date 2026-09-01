# Despliegue distribuido — Docker + nodo Android

> **Fecha:** 2026-08-29
> **Estado:** diseño. La implementación corresponde a una fase posterior al
> roadmap actual (imagen Docker + operación del nodo Android). Se documenta
> ahora para que las Fases 2–3 no tomen decisiones que compliquen este
> despliegue.

## Topología objetivo

```
                          ┌─────────────────────────────────────┐
   clientes (dispositivos)│   rpi4b (servidor, Docker)          │
   ┌──────────┐           │                                     │
   │ dashboard│──HTTP──▶  │  contenedor `mtts` (FastAPI:8100)   │
   │ CLI/API  │           │     │ orquesta, cachea, concatena   │
   └──────────┘           │     │ (no sintetiza por sí solo)    │
                          │     ▼                               │
                          │  red local / Tailscale              │
                          └─────────────────────────────────────┘
                                      │ HTTP (GET /forward, /voices)
                                      ▼
                          ┌─────────────────────────────────────┐
                          │ nodo Android (hub de casa)          │
                          │  APK MultiTTS 1.8.0                 │
                          │  ForwardService :8774 (0.0.0.0)     │
                          │  *fuente real de síntesis*          │
                          └─────────────────────────────────────┘
```

- El **orquestador** (contenedor) y el **motor** (APK) viven en máquinas
  distintas. Hoy el código asume backend local por `--backend`; hay que
  hacer del backend una **configuración de primera clase** (decisión #23).
- El loopback del contenedor **no es** el loopback del host: las reglas de
  auth/bind deben desacoplarse (decisión #24).

---

## 1. Configuración del backend (decisión #23)

`backend_url` se resuelve por orden de prioridad:

1. **Variable de entorno** `MTTS_BACKEND_URL`.
2. **Archivo de config** (ruta por env `MTTS_CONFIG` o default del sistema).
3. **Flag CLI** `--backend` (para dev / sobreescribir puntualmente).
4. **Default de desarrollo**: `http://127.0.0.1:8774`.

```toml
# ejemplo ~/.config/mtts/config.toml
backend_url = "http://192.168.1.50:8774"

[voices.presets]                 # voces preconfiguradas (decisión #27)
narrador  = "microsoft_es-MX-DaliaNeural-MiAndroidAccesible"
juan      = "microsoft_es-MX-JorgeNeural-MiAndroidAccesible"
```

### Por qué un archivo de config (y no solo env)

El catálogo del backend mezcla 7 motores con comportamientos distintos
(offline/online, niveles de loudness, rangos de `speed`/`pitch` óptimos
muy diferentes). Los **valores óptimos difieren por voz**, así que la
config debe poder:

- fijar `backend_url` (env o archivo);
- declarar **voces preconfiguradas** (`presets`) con defaults por voz
  (`speed`, `pitch`, `volume`, `pause_after`);
- ser versionable y compartible entre dispositivos.

> Nota del humano: los ajustes experimentales de `bin/mel` / `bin/mtts`
> no necesitan commit propio; se incluyen en el siguiente commit del
> proyecto.

---

## 2. Bind vs auth desacoplados (decisión #24)

Hoy OPEN_QUESTIONS #17 dice "sin auth en loopback". Con Docker esto se
rompe: un contenedor con `0.0.0.0:8100` ve `127.0.0.1` internamente, pero
está expuesto a la LAN. **Regla nueva:**

| Bind              | Auth |
|-------------------|------|
| `127.0.0.1`       | sin token |
| `0.0.0.0` (o LAN) | **token `Bearer` obligatorio** |

El criterio es la **dirección de bind**, no "estoy en localhost".

---

## 3. Cola y límite de concurrencia (decisión #25)

El motor Android es **serial** (una síntesis a la vez por el servicio
forwarder). Un hub doméstico con varios dispositivos puede disparar varios
`POST /dialog` simultáneos.

- **Cola única global** (worker serial) delante de las llamadas a `/forward`:
  las peticiones concurrentes se encolan, no saturan el backend.
- **Límite de concurrencia**: probablemente **sobra** — el backend responde
  bien (~10.9× tiempo real) y habrá menos de una decena de clientes. Se deja
  como **knob configurable** (`max_concurrent = 3` por defecto), no como
  mecanismo central.

Implementación prevista: un `asyncio.Semaphore`/`Queue` en la capa server
(Fase 3). No aplica a la CLI (que ya es serial).

---

## 4. Estados de salud degradados (decisión #26)

`GET /health` debe distinguir **tres** estados, no un booleano:

| Estado | Significado |
|--------|-------------|
| `ok` | backend alcanzable + síntesis canary válida (formato WAV correcto) |
| `backend_unreachable` | 8774 no responde (nodo Android caído / red) |
| `backend_reachable_but_drift` | 8774 responde pero el WAV canary no valida formato (drift de APK, ver `RISKS.md`) |

**Requisito clave:** el contenedor **debe arrancar y servir** aunque el
backend esté caído. Hoy `api.py` lanza `ConnectionError` tras 3 reintentos
(bien para CLI); el server debe **capturar y reportar** ese estado, no morir.

---

## 5. Voces preconfiguradas vs catálogo del backend (decisión #27)

Se separan dos conceptos que hoy están mezclados:

- **Catálogo del backend** (`GET /voices` de 8774): la verdad del servidor.
  Se reenvía sin modificar.
- **Voces preconfiguradas (presets)**: mapeo local `nombre → {voice, speed,
  pitch, volume, pause_after}` definido en config. Son opinión del usuario
  sobre *cómo* usar una voz, no qué voces existen.

Al consultar presets se obtienen las voces y **valores por defecto** de cada
voz preconfigurada.

---

## 6. Sintaxis: presets + overrides delta (decisión #28)

Se extiende la sintaxis de guion (`DIALOG_SYNTAX.md`) para aprovechar los
presets y permitir **ajustes incrementales** sobre los defaults:

### 6.1 Usar un preset por nombre

```
@narrador = @preset(narrador)
```

En vez de repetir el `ID_VOZ` largo, se referencia el preset de la config.
Si el preset define `speed/pitch/volume/pause_after`, se heredan.

### 6.2 Overrides delta `+n` / `-n`

Sobre un valor base (del cast o del preset), se puede operar con
desplazamientos relativos:

```
juan (speed=-10 volume=+5): Aléjate.          # -10 / +5 sobre el default
narrador (pitch=+3): Era una noche...         # +3 sobre el default del preset
```

- `+n` / `-n` = **umbral relativo** sobre el valor efectivo (resuelto:
  global < preset < cast < override de línea).
- `n` (sin signo) = **valor absoluto**, como hasta ahora.
- Rango válido: `speed`/`pitch`/`volume` hacen clamp a `0–100` tras el
  delta; `pause_after` (ms) no tiene cota superior.
- `pause_after` con `+n` / `-n` = **suma/resta de ms** sobre el valor
  efectivo. `n` sin signo = valor absoluto en ms.

> Esto resuelve el problema real: los motores tienen rangos óptimos
> distintos.

---

## 7. Imagen Docker (bloqueante)

> ⚠️ **Bloqueante:** el desarrollo de la imagen Docker debe realizarse
> **en el server rpi4b**, no en Termux. El target es `arm64v8` (el rpi4b es
> aarch64); construir/probar solo en el teléfono no valida el target real
> (arquitectura, red, volúmenes, mDNS). Ver `ROADMAP.md`.

Especificación objetivo:

- **Base**: `python:3.11-slim` (arm64v8) — Fase 3 requiere FastAPI/uvicorn.
- **Deps**: `requests`, `fastapi`, `uvicorn` (+ `ffmpeg` solo si MP3).
- **Volúmenes**:
  - `~/.cache/mtts` → caché de chunks (persistente entre reinicios).
  - directorio de audio temporal (`/audio/{id}` con TTL) → host bind o volumen.
- **Config**: montar `config.toml` + env `MTTS_BACKEND_URL`.
- **HEALTHCHECK**: `curl /health` (estados degradados de §4).
- **Exposición**: default `127.0.0.1:8100`; `0.0.0.0` solo con token (§2).

---

## 8. Operación del nodo Android

- **IP estable proporcionada por Tailscale**.
- **Keep-alive del forwarder**: Doze / optimización de batería pueden matar
  el servicio con pantalla apagada. Requiere pin/whitelist en el Android.
- **AP isolation** del router: bloquea tráfico device-to-device y haría
  inalcanzable 8774 desde el rpi4b. Tailscale lo resuelve.

---

## 9. Modelo de seguridad

- **8774 no tiene auth y binda `0.0.0.0`** (comportamiento original de la
  APK; no lo cambiamos). Tratarlo como **servicio interno de confianza**:
  red privada o **Tailscale/WireGuard**. El token planeado protege *nuestra*
  API (8100), **no** el motor subyacente.
- Si se expone 8774 a internet, usar túnel cifrado (Tailscale), nunca
  port-forward directo.

---

## 10. Fuera de alcance (no arrastrar ahora)

- Service discovery / auto-descubrimiento de nodos.
- Réplicas múltiples del motor.
- Streaming / range requests del audio.
- Auth sobre 8774 (no es nuestro código).
- Escalado horizontal del orquestador (más de un rpi4b).