# Añadidos propuestos al plan

> **Fecha:** 2026-08-19
> Propuestas del agente tras revisar el plan completo (`docs/`) a la luz de
> las pruebas de `docs/BURST_TEST.md`. Son **extensiones**, no cambios de
> arquitectura: el plan base queda como está.

## 1. Caché de chunks por hash (prioridad alta — Fase 2)

**Qué:** guardar cada WAV sintetizado en disco, indexado por
`hash(text, voice, speed, pitch, volume)` — p. ej.
`~/.cache/mtts/<sha256>.wav` — y consultar la caché antes de llamar a
`/forward`.

**Por qué:** no es por throughput del servidor (probado sobrado: 10.9×
tiempo real, ver `BURST_TEST.md`), es por **productividad**: en Fase 4/5
re-renderizarás el mismo guion muchas veces editando una línea; sin caché
cada render re-sintetiza las 100 líneas, con caché solo la línea cambiada.
Es barato: stdlib (`hashlib`, `os`) y unas decenas de líneas.

**Detalles:**
- Hash sobre los 5 parámetros exactos que van al query string (text ya
  escapado, voice, speed, pitch, volume).
- `--no-cache` en CLI y campo `cache: true/false` en API para forzar
  re-síntesis.
- Limpieza por tamaño máximo (`mtts cache clear` / umbral configurable);
  los WAV de texto corto pesan decenas de KB, no es crítico.
- **Invalidación gratuita tras drift de APK:** si el formato de salida
  cambia (ver `RISKS.md`), la caché antigua es basura — incluir la versión
  del contrato (p. ej. "apk-1.8.0") en el hash o en el prefijo de
  directorio la invalida automáticamente.

## 2. Normalización de loudness por chunk (opcional — Fase 2)

**Qué:** escalar cada chunk al mismo RMS objetivo antes de concatenar.

**Por qué:** voces de motores distintos (microsoft, vocalizer, …) tienen
niveles distintos; en un diálogo los saltos de volumen entre personajes se
oyen mal. Ya existe evidencia en `docs/API.md` de que `volume=100` hace
clipping y de que el RMS varía con el volumen — el cálculo es trivial
(sumatorio de cuadrados sobre frames 16-bit con `audio.py`).

**Detalles:**
- Off por defecto (`--normalize` opt-in) para que el audio sea
  bit-exact con lo que el servidor devuelve, salvo que se pida.
- RMS objetivo configurable; escalar con saturación (clamp) a 16-bit.
- Documentar que altera el audio respecto del original (por eso es opt-in).

## 3. Progreso y estimaciones (Fase 2/3)

**Qué:**
- CLI: barra de progreso o línea de estado `n/N chunks · 12.3 s / ~40 s
  (ETA)` en `mtts dialog`.
- API: incluir en la respuesta JSON el array `chunks` con
  `(personaje, texto, duración, params)` — ya está en `docs/OPENAPI.md`;
  añadir explícitamente el equivalente en CLI.

**Por qué:** renders de 30–40 s con la pantalla muerta se sienten rotos
aunque funcionen. La ETA es fiable: el throughput es estable (~10–11×
tiempo real, medido).

## 4. Entrega de audio por URL en la API (Fase 3)

**Qué:** en `POST /dialog` con `lrc: true`, devolver JSON con
`audio_url` (ej. `GET /audio/{id}` temporal) + contenido LRC, en vez de
base64 embebido.

**Por qué:** un WAV de 10 min ≈ 28 MB; en base64 = 37 MB dentro de un
JSON. El dashboard (Fase 4) consume por URL de todos modos (elemento
`<audio src>`), y dos endpoints separados permiten servir el audio con
`Content-Type` correcto y streaming/range requests.

**Detalles:** `id` aleatorio, TTL configurable (p. ej. 1 h), purga al
expirar; opcional `?inline=true` para quien quiera el binario directo.

## 5. Bind y auth del servicio local (Fase 3)

**Qué:** default `--bind 127.0.0.1` con flag para exponer; token simple
opcional (`Authorization: Bearer`) para el dashboard.

**Por qué:** el servidor 8774 de la APK ya binda `0.0.0.0` sin auth (es su
comportamiento original, no lo cambiamos), pero nuestra capa de
orquestación no necesita heredar esa exposición. En red local (wifi)
cualquiera podría golpear un dashboard sin auth. Loopback por defecto es
el default prudente y no cuesta nada.

## 6. Target Python ≥ 3.10 (Fase 1)

**Qué:** fijar `requires-python = ">=3.10"` en `pyproject.toml`.

**Por qué:** el README dice 3.12 y el entorno tiene 3.14, pero nada del
código actual necesita más de 3.10 (`match` está en 3.10 si hiciera falta).
Bajar el piso maximiza compatibilidad (Termux, otros Androids) sin coste.
Las features usadas deben verificarse contra 3.10 en Fase 1.

## 7. `GET /health` con síntesis canary (Fase 3)

**Qué:** el healthcheck no solo comprueba alcance de 8774: ejecuta una
síntesis corta ("hola", voz offline fija) y valida la cabecera WAV
(canales, sample rate, bits, duración > 0).

**Por qué:** es la mitigación principal del único riesgo abierto — el
drift por versión de la APK puede cambiar el formato de salida sin cambiar
status codes, y un ping simple no lo detectaría. Detalle completo en
`docs/RISKS.md` §Mitigaciones.

## Resumen de integración con el roadmap

| Añadido | Fase | Coste | Retorno |
|---|---|---|---|
| 1. Caché de chunks | 2 | Bajo | Alto (re-renders) |
| 2. Normalización loudness | 2 | Bajo | Medio (calidad de diálogo) |
| 3. Progreso n/N + ETA | 2/3 | Bajo | Medio (UX) |
| 4. Audio por URL + TTL | 3 | Bajo | Medio (dashboard) |
| 5. Loopback + token | 3 | Trivial | Medio (seguridad) |
| 6. Python ≥ 3.10 | 1 | Trivial | Medio (compat) |
| 7. Canary en `/health` | 3 | Bajo | **Alto (mitiga RISKS.md)** |
