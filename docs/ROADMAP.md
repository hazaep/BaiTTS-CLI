# Mapa de ruta (roadmap)

Orden sugerido de fases. Cada fase entrega algo **usable** por sí solo.
Las decisiones de diseño están en [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) y
las extensiones propuestas por la revisión en [`ADDITIONS.md`](ADDITIONS.md).

## Fase 0 — Consolidar conocimiento técnico ✅

**Entregables:**
- [x] `docs/API.md` — endpoints y parámetros del servidor MultiTTS.
- [x] Sección de **etiquetas nativas** (`[[PAUSE:ms]]`, `<break/>`, tags
      que se tragan) verificada empíricamente.
- [x] Sección de **escapado** de símbolos que interfieren.
- [x] `docs/DIALOG_SYNTAX.md` — sintaxis del guion.
- [x] `docs/ENGINE.md` — diseño del motor de diálogos.
- [x] `docs/ARCHITECTURE.md` — estructura del paquete.
- [x] `docs/ROADMAP.md` — este archivo.
- [x] `docs/OPENAPI.md` — contrato REST futuro.
- [x] `docs/OPEN_QUESTIONS.md` — decisiones consolidadas (con respuestas).
- [x] `docs/BURST_TEST.md` — prueba de ráfaga + escala (33/33, ~10.9× real).
- [x] `docs/RISKS.md` — riesgo de drift de la APK + mitigaciones.
- [x] `docs/ADDITIONS.md` — extensiones propuestas al plan.
- [x] `tmp/burst_test.py` + `tmp/burst_test_output.txt` — evidencia reproducible.
- [x] `tmp/length_test.py` — prueba de longitud por llamada (OPEN_QUESTIONS #10).
- [x] Artefactos de decompilación del APK consolidados en
      `tmp/apk/decompiled-apk-1.8.0.tar.gz` (fuera de git).

**Pendiente (opcional, no bloquea nada):** re-descompilar con `--show-bad-code`
para documentar el `switch (path.hashCode())` exacto. Solo es necesario si el
servidor cambia de comportamiento (ver `RISKS.md` §Mitigaciones, punto 5).

## Fase 1 — Refactor a paquete instalable

**Objetivo:** mantener el 100 % de la funcionalidad actual, pero en un paquete
instalable y testeable.

- [ ] `pyproject.toml` (paquete `mtts`, `requires-python = ">=3.10"`,
      entry points `mtts` y `mtts-server`).
- [ ] Migrar `api.py`, `tts.py`, `process.py`, `lrc.py`, `utils.py` a
      `src/mtts/` con firma limpia.
- [ ] `pip install -e .` funcional en Termux.
- [ ] CLI `mtts` compatible con los flags actuales (`--backend -l -f -d -o
      --voice --volume --speed --pitch -s -b`).
- [ ] Tests de regresión (listar voces, convertir archivo, LRC, blacklist).
- [ ] Verificar features contra Python 3.10 (piso de compatibilidad).
- [ ] Wrappers `bin/mel` y `bin/mtts` reescritos como shims delgados con
      aviso de deprecación (remover en Fase 4). Ver OPEN_QUESTIONS #20.

## Fase 2 — Motor de diálogos (engine)

**Objetivo:** interpretar el guion y construir audio multi-personaje.

- [ ] `dialog/parser.py` — parsear cast, diálogos, overrides, pausas,
      acotaciones, controles globales.
- [ ] `dialog/escape.py` — escapado `[[...]]` (conservar solo `[[PAUSE:ms]]`).
- [ ] `dialog/characters.py` — cast inline (`@`) + JSON (merge por campo).
- [ ] `dialog/engine.py` — pipeline synth + silencio + concat.
- [ ] `audio.py` — `make_silence`, `concat_wav`, lectura de frames.
- [ ] **Caché de chunks por hash** (`~/.cache/mtts/<sha256>.wav`, incluye
      versión del contrato "apk-1.8.0" en el hash). Ver `ADDITIONS.md` §1.
- [ ] **Validación de cada respuesta WAV** (cuerpo vacío, cabecera inválida
      o formato distinto de mono/24 kHz/16-bit → error reintentable).
      Ver `RISKS.md` §Mitigaciones, punto 3.
- [ ] **Normalización de loudness opcional** (`--normalize`, off por defecto).
      Ver `ADDITIONS.md` §2.
- [ ] Warning de voz default (personaje fuera del cast) y de chunk largo
      (~1 000+ caracteres). Ver OPEN_QUESTIONS #6 y #10.
- [ ] CLI: subcomando `mtts dialog` (`-f`, `-c`, `-o`, `--lrc`, `--play`,
      `--format wav|mp3`, `--no-cache`, `--normalize`).
- [ ] **Progreso `n/N` + ETA** en `mtts dialog`. Ver `ADDITIONS.md` §3.
- [ ] LRC por línea de diálogo (opcional).
- [ ] Reproducción opcional (`mplayer`).
- [ ] Tests de parser, escapado, resolución de parámetros y audio.

## Fase 3 — API REST local (OpenAPI)

**Objetivo:** exponer el núcleo como servicio HTTP con OpenAPI autogenerado,
pensando ya en el dashboard.

- [ ] `server/app.py` (FastAPI + uvicorn) con bind default `127.0.0.1`
      (flag `--bind` para exponer). Ver `ADDITIONS.md` §5.
- [ ] `GET /health` — **canary**: alcance + síntesis corta + validación de
      cabecera WAV (1 ch / 24 kHz / 16-bit / duración > 0). Ver `RISKS.md`.
- [ ] `GET /voices` — reenvío del catálogo.
- [ ] `POST /tts` — síntesis simple (texto + params).
- [ ] `POST /dialog` — guion + cast → audio (con `lrc: true/false`).
- [ ] `GET /audio/{id}` — entrega de audio por URL temporal (TTL ~1 h).
      Ver `ADDITIONS.md` §4 y `OPENAPI.md`.
- [ ] OpenAPI en `/docs` y `/openapi.json` (gratis con FastAPI).
- [ ] Token `Bearer` opcional solo si se expone a la LAN. Ver OPEN_QUESTIONS #17.
- [ ] Respuesta `POST /dialog` con `lrc:true`: JSON con `audio_url` + `lrc` +
      array `chunks` (incluye duración/params por chunk, para la ETA).

## Fase 4 — Dashboard sencillo (localhost)

**Objetivo:** interfaz web mínima sobre la API de Fase 3.

- [ ] Editor de guion con resaltado básico.
- [ ] Selector de voces por motor/género/idioma (consumiendo `GET /voices`).
- [ ] Gestión de cast (crear/editar personajes).
- [ ] Preview y generación de audio (botón → `POST /dialog`).
- [ ] Reproductor embebido (consumiendo `audio_url`) + descarga.
- [ ] Visualización de timeline/LRC (a partir del array `chunks`).
- [ ] Remover los wrappers legacy `bin/mel` y `bin/mtts` (fin de deprecación).

## Fase 5 — Escalado e integración con IA

**Objetivo:** flujo de trabajo productivo con guiones generados por IA.

- [ ] Plantillas/presets de personajes reutilizables.
- [ ] Pipeline "prompt → guion (IA) → motor → audio".
- [ ] Validación y saneado automático de guiones IA (escapado, límites de
      longitud, voces existentes).
- [ ] Exportación multi-formato (WAV, MP3, LRC, JSON de chunks).

---

## Notas de decisión (consolidadas)

- Framework API: **FastAPI** (OpenAPI automático).
- Formato de salida nativo: **WAV** (lo que devuelve el servidor). MP3 es
  conversión vía `ffmpeg` (opcional).
- Bind default **`127.0.0.1`**; exponer a LAN es opt-in con token.
- El servidor MultiTTS (8774) es la **fuente de síntesis**; nuestra API es una
  capa de orquestación local.
- Rendimiento validado: **~10.9× tiempo real**, motor serial sin delay forzado
  (`BURST_TEST.md`).
