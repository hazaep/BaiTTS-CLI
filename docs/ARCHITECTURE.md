# Arquitectura del proyecto

> **Fase 1 completada (2026-08-29).** Código migrado a `src/mtts/`, legacy
> preservado con historial en `legacy/`, paquete instalable con `pip install -e .`.
> El resto de módulos (`audio.py`, `cache.py`, `voices.py`, `dialog/`,
> `server/app.py`) corresponden a las Fases 2–3.

Objetivo: migrar la CLI actual (un solo directorio de scripts sueltos) a un
**paquete Python instalable y mantenible**, con un núcleo compartido entre la
CLI y la futura API REST / dashboard.

## Estado actual del layout

```
~/.bildung/multi-tts/
├── pyproject.toml              # metadatos + entry points ✅ Fase 1
├── README.md                   # actualizado (flag --backend)
├── src/
│   └── mtts/
│       ├── __init__.py         # ✅ Fase 1
│       ├── api.py              # ✅ Fase 1 (cliente HTTP)
│       ├── lrc.py              # ✅ Fase 1 (generación LRC)
│       ├── process.py          # ✅ Fase 1 (orquestación alto nivel)
│       ├── tts.py              # ✅ Fase 1 (síntesis + combine WAV)
│       ├── utils.py            # ✅ Fase 1 (blacklist, split, codificación)
│       ├── cli/
│       │   ├── __init__.py     # ✅ Fase 1
│       │   ├── args.py         # ✅ Fase 1 (flag --backend)
│       │   └── main.py         # ✅ Fase 1 (entry point mtts)
│       └── server/
│           ├── __init__.py     # ✅ Fase 1 (placeholder)
│           └── app.py          # ✅ Fase 1 (stub Fase 3)
├── tests/
│   ├── test_regression.py      # ✅ Fase 1 (16 unitarios)
│   └── test_integration.py     # ✅ Fase 1 (2 contra servidor real)
├── bin/                        # ✅ Fase 1 (shims con deprecación)
│   ├── mel
│   └── mtts
├── legacy/                     # ✅ código original sin modificar (historial)
│   ├── api.py args.py main.py process.py tts.py lrc.py utils.py
│   └── requirements.txt
├── docs/                       # documentación (Fase 0)
├── voices_es.py                # catálogo de voces ES (fuente de voices.py)
├── tmp/                        # artefactos de referencia (fuera de git)
└── story.txt / story.wav       # ejemplos originales
```

## Directorio de trabajo

```
~/.bildung/multi-tts/
```

Todo el proyecto vive aquí (es el workspace actual). Al empaquetar con
`pip install -e .`, el paquete queda importable desde cualquier parte de
Termux.

## Layout propuesto

```
~/.bildung/multi-tts/
├── pyproject.toml              # metadatos + entry points + deps
├── README.md                   # índice de la documentación
├── docs/
│   ├── API.md                  # servidor MultiTTS (ingeniería inversa)
│   ├── DIALOG_SYNTAX.md        # sintaxis del guion + escapado
│   ├── ENGINE.md               # diseño del motor de diálogos
│   ├── ARCHITECTURE.md         # este archivo
│   ├── ROADMAP.md              # mapa de ruta por fases
│   └── OPENAPI.md              # contrato REST futuro
├── src/
│   └── mtts/
│       ├── __init__.py         # versión + exports públicos
│       ├── api.py              # cliente HTTP de /forward, /voices, /log
│       ├── audio.py            # utilidades WAV (frames, silencio, concat,
│       │                       #   validate_wav, normalize_loudness)
│       ├── cache.py            # caché de chunks por hash (ADDITIONS.md §1)
│       ├── voices.py           # catálogo de voces (de /voices)
│       ├── lrc.py              # generación LRC
│       ├── dialog/
│       │   ├── __init__.py
│       │   ├── parser.py
│       │   ├── characters.py
│       │   ├── escape.py
│       │   └── engine.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py         # entry point `mtts`
│       │   └── dialog_cmd.py
│       └── server/             # (Fase 3) API REST + dashboard
│           ├── __init__.py
│           ├── app.py
│           └── routers/
├── tests/
│   ├── test_parser.py
│   ├── test_escape.py
│   ├── test_audio.py
│   └── test_characters.py
├── bin/                        # wrappers legacy (shims con deprecación)
│   ├── mel
│   └── mtts
├── voices_es.py                # catálogo de voces ES (fuente de voices.py)
├── tmp/                        # artefactos de referencia (fuera de git)
│   ├── burst_test.py           # prueba de ráfaga reproducible
│   ├── length_test.py          # prueba de longitud por llamada
│   └── apk/decompiled-apk-1.8.0.tar.gz  # decompilación consolidada
└── legacy/                     # código actual, sin tocar durante la migración
    ├── api.py tts.py process.py args.py main.py lrc.py utils.py
```

## Nombre del paquete y entry points

- **Paquete importable**: `mtts`.
- **Python mínimo**: `>=3.10` (`requires-python` en `pyproject.toml`).
  Nada del código actual necesita más; maximiza compatibilidad Termux/otros
  Androids. Las features usadas se verifican contra 3.10 en Fase 1. Ver
  `ADDITIONS.md` §6.
- **Entry points** (definidos en `pyproject.toml`):

```toml
[project.scripts]
mtts = "mtts.cli.main:main"          # CLI principal
mtts-server = "mtts.server.app:main" # API REST (Fase 3, futuro)
```

## Dependencias

| Fase    | Paquete            | Uso |
|---------|--------------------|-----|
| base    | `requests`         | cliente HTTP (ya presente) |
| audio   | stdlib `wave`      | leer/escribir WAV (sin dep extra) |
| opcional| `ffmpeg` (binario) | convertir WAV→MP3 si se pide MP3 |
| opcional| `mplayer` (binario)| reproducción (`--play`) |
| Fase 3  | `fastapi` + `uvicorn` | API REST con OpenAPI autogenerado |
| Fase 3  | `itsdangerous` o stdlib `secrets` | token Bearer si se expone a LAN |

> `numpy` ya está instalado, pero para el motor **no es necesario**: las
> utilidades WAV usan `wave` + `array`/`bytes` de stdlib.

## Principios de diseño

1. **Núcleo puro, sin I/O de UI**: `dialog/engine.py`, `audio.py`, `api.py`
   no saben si los llamó la CLI o la API. Reciben datos y devuelven datos.
2. **CLI y API son capas finas** sobre el núcleo. Así ambos se benefician de
   las mismas reglas (cast, escapado, LRC, pausas).
3. **Documentación es código de primer orden**: cada pieza de conocimiento
   del servidor queda en `docs/` para que escalar no dependa de memoria.
4. **Sin estado global**: el cast y los defaults son parámetros, no variables
   de módulo.

## Flujo compartido CLI/API

```
           ┌─────────────── CLI (argparse) ───────────────┐
           │                                              │
 guion ──▶ │   mtts.dialog.engine.render(script, cast,   │ ──▶ WAV / LRC
           │              options={lrc, play, out_format})│
           │                                              │
           └──────────────────────────────────────────────┘
           ┌─────────────── API (FastAPI) ────────────────┐
           │  POST /dialog  → engine.render(...)          │ ──▶ binario/JSON
           │  GET  /voices  → mtts.api.get_voices()       │
           └──────────────────────────────────────────────┘
```

## Cómo escalar (puntos de extensión)

- **Nuevas directivas** en el guion → añadir un caso en `parser.py`.
- **Nuevo motor de voz** (otro servidor TTS) → implementar la misma interfaz
  de `api.py` (`synthesize(text, voice, params) -> bytes`).
- **Nuevo formato de salida** (MP3, OGG) → añadir un conversor en `audio.py`
  (usa `ffmpeg`).
- **Nuevo endpoint** → añadir un router en `server/routers/`.

## Migración (plan de bajo riesgo)

1. Crear `legacy/` y mover ahí el código actual **sin modificarlo**.
2. Crear `src/mtts/` con el código reestructurado (imports y firma limpios).
3. `pip install -e .` y verificar que `mtts` replica el comportamiento actual
   (listar voces, convertir archivo, directorio, LRC, blacklist).
4. Reescribir `bin/mel` y `bin/mtts` para que llamen al nuevo `mtts`.
5. Retirar `legacy/` cuando todo esté cubierto por tests.
