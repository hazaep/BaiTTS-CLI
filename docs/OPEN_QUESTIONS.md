# Decisiones del proyecto — estado consolidado

> **Fecha:** 2026-08-20 (confirmaciones humanas integradas)
> Este archivo es la **fuente única de verdad** sobre el estado de las
> decisiones. El razonamiento completo de cada una está en
> [`AGENT_OPEN_QUESTIONS.md`](AGENT_OPEN_QUESTIONS.md), informado por la
> evidencia de [`BURST_TEST.md`](BURST_TEST.md).
>
> **Leyenda:** `[x]` = resuelta (evidencia empírica o consenso técnico);
> `[ ]` = recomendación firme del agente, **pendiente de tu confirmación**.

## Estado


| #   | Decisión                                    | Estado | Resolución                                                                                                                                                                                                  |
| --- | ------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Delimitador de personaje `personaje: texto` | \[x\]  | Confirmado. Formato natural de guion.                                                                                                                                                                       |
| 2   | Nombres de personaje con espacios           | \[x\]  | Sí, hasta el `:` o el `(` de override.                                                                                                                                                                      |
| 3   | Override por línea vs acotación             | \[x\]  | Confirmado. Desambiguar por **posición + clave conocida** (clave ∈ `{speed,pitch,volume,pause_after}` y valor numérico). Ver `DIALOG_SYNTAX.md`.                                                            |
| 4   | Cast JSON separado                          | \[x\]  | Sí (`cast` en API, `-c cast.json` en CLI).                                                                                                                                                                  |
| 5   | Fusión inline + JSON                        | \[x\]  | Gana el JSON. Merge **por campo**, no por personaje.                                                                                                                                                        |
| 6   | Voz por defecto                             | \[x\]  | Confirmado. `default_voice` acepta `string` (global) o `map{locale: voz}` (por idioma) con fallback al global. + **warning** cuando un personaje cae al default.                                            |
| 7   | Escapado canónico `[ [`                     | \[x\]  | Confirmado (vs. fullwidth `［［`).                                                                                                                                                                            |
| 8   | `[[PAUSE:ms]]` con decimales                | \[x\]  | Confirmado. Warning + truncar a entero (no rechazar).                                                                                                                                                       |
| 9   | Chunk por línea (1 línea = 1 llamada)       | \[x\]  | **Resuelto por evidencia** (`BURST_TEST.md`: 33/33, \~10.9× tiempo real).                                                                                                                                   |
| 10  | Límite de longitud por chunk                | \[x\]  | Confirmado. Sin límite duro; **warning informativo a partir de \~1 000 caracteres**.                                                                                                                        |
| 11  | LRC por línea de diálogo                    | \[x\]  | Confirmado (subdivisión por frase = mejora posterior).                                                                                                                                                      |
| 12  | MP3 ahora                                   | \[x\]  | No. WAV en Fase 2; MP3 vía `ffmpeg` a demanda.                                                                                                                                                              |
| 13  | Reproducción CLI/API                        | \[x\]  | Confirmado. CLI `--play` (mplayer). API: **URL temporal** (no binario embebido).                                                                                                                            |
| 14  | Framework API                               | \[x\]  | FastAPI + uvicorn.                                                                                                                                                                                          |
| 15  | Puerto + bind                               | \[x\]  | Confirmado. Puerto `8100`, **bind default `127.0.0.1`** (flag `--bind` para exponer).                                                                                                                       |
| 16  | Entrega de audio + LRC                      | \[x\]  | **URL temporal** (`GET /audio/{id}`, TTL \~1 h) + LRC. Base64 descartado.                                                                                                                                   |
| 17  | Auth                                        | \[x\]  | Confirmado. Sin auth en loopback; token `Bearer` solo si se expone a la LAN.                                                                                                                                |
| 18  | Nombre del paquete                          | \[x\]  | `mtts`.                                                                                                                                                                                                     |
| 19  | Python mínimo                               | \[x\]  | `>=3.10`.                                                                                                                                                                                                   |
| 20  | Wrappers `bin/mel` y `bin/mtts`             | \[x\]  | Confirmado. Mantener como shims delgados + aviso de deprecación; remover en Fase 4.                                                                                                                         |
| 21  | Fase 1 antes que Fase 2                     | \[x\]  | Confirmado (refactor primero, tests de regresión protegen el engine).                                                                                                                                       |
| 22  | Dashboard (Fase 4)                          | \[x\]  | "Más adelante", diseñando Fase 2/3 pensando en él.                                                                                                                                                          |
| 23  | Backend como config de primera clase        | \[x\]  | `backend_url` por env (`MTTS_BACKEND_URL`) + archivo de config (TOML), default `http://127.0.0.1:8774`. Flag `--backend` solo para dev. Ver `DISTRIBUTED.md` §1.                                            |
| 24  | Bind vs auth desacoplados                   | \[x\]  | `127.0.0.1` → sin token; `0.0.0.0`/LAN → token `Bearer` obligatorio. El criterio es la **dirección de bind**, no "estoy en localhost". Ver `DISTRIBUTED.md` §2.                                             |
| 25  | Cola y límite de concurrencia               | \[x\]  | Cola global serial delante de `/forward`; `max_concurrent` configurable (default 3). El límite probablemente sobra (&lt;10 clientes, \~10.9× real), se deja como knob. Ver `DISTRIBUTED.md` §3.             |
| 26  | Estados de salud degradados                 | \[x\]  | `/health` con 3 estados: `ok` / `backend_unreachable` / `backend_reachable_but_drift`. El server debe arrancar aunque el backend esté caído. Ver `DISTRIBUTED.md` §4.                                       |
| 27  | Voces preconfiguradas vs catálogo           | \[x\]  | Separar catálogo del backend (`/voices`, se reenvía) de **presets** locales (nombre → `{voice,speed,pitch,volume,pause_after}`) en config. Consultar preset devuelve sus defaults. Ver `DISTRIBUTED.md` §5. |
| 28  | Sintaxis: presets + overrides delta         | \[x\]  | `@preset(nombre)` en cast; overrides delta `+n`/`-n` (relativo) vs `n` (absoluto) sobre `speed`/`pitch`/`volume`/`pause_after`. `speed`/`pitch`/`volume` clamp 0–100; `pause_after` suma/resta ms sin cota. Ver `DISTRIBUTED.md` §6. |


## Resumen

- **Resueltas:** las 28 decisiones (2026-08-29).
- **Ajustes confirmados por el humano:** puerto `8100`, flag `--bind` (no `--host`),
flag `--backend` (no `--api`), `default_voice` multilocale (string | map | fallback).

## Añadidos derivados de la revisión

La revisión del agente añadió **siete extensiones** al plan (no cambios de
arquitectura). Están detalladas en [`ADDITIONS.md`](ADDITIONS.md) y ya
integradas en `ROADMAP.md`, `ENGINE.md` y `OPENAPI.md`:

1. Caché de chunks por hash (Fase 2).
2. Normalización de loudness opcional (Fase 2).
3. Progreso `n/N` + ETA (Fase 2/3).
4. Entrega de audio por URL + TTL (Fase 3).
5. Bind loopback + token (Fase 3).
6. Target Python `>=3.10` (Fase 1).
7. `GET /health` con síntesis canary (Fase 3) — mitiga el riesgo de
 drift de la APK (`RISKS.md`).

## Despliegue distribuido (post-roadmap)

Las decisiones #23–28 preparan el despliegue **Docker (rpi4b) + nodo Android**.
Detalle completo en [`DISTRIBUTED.md`](DISTRIBUTED.md): config de backend por
env+archivo (#23), bind vs auth desacoplados (#24), cola serial (#25), estados
de salud degradados (#26), voces preconfiguradas vs catálogo (#27) y sintaxis
de presets + overrides delta (#28). El desarrollo de la imagen es **bloqueante
en el rpi4b** (target `arm64v8`).