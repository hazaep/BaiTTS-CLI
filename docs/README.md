# Documentación del proyecto MultiTTS

Conocimiento técnico del servidor MultiTTS (puerto 8774) y diseño del
proyecto de diálogos. Estos documentos son **consultables**: cada hallazgo
queda escrito para no depender de memoria.

## Índice

| Documento | Contenido |
|-----------|-----------|
| [API.md](API.md) | Servidor MultiTTS: endpoints, parámetros, **etiquetas nativas** (`[[PAUSE]]`, `<break/>`) y **escapado**. |
| [DIALOG_SYNTAX.md](DIALOG_SYNTAX.md) | Sintaxis del guion de diálogos (cast, pausas, overrides, acotaciones, escapado). |
| [ENGINE.md](ENGINE.md) | Diseño del motor de diálogos (pipeline, módulos, resolución de parámetros). |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Estructura del paquete instalable (`pip install -e`), layout, entry points. |
| [ROADMAP.md](ROADMAP.md) | Mapa de ruta por fases (refactor → engine → API → dashboard → IA). |
| [OPENAPI.md](OPENAPI.md) | Contrato REST futuro (Fase 3). |
| [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) | **Decisiones del proyecto** (estado consolidado: 14 resueltas, 8 pendientes de confirmación). |
| [AGENT_OPEN_QUESTIONS.md](AGENT_OPEN_QUESTIONS.md) | Razonamiento del agente para cada decisión (2026-08-19), con evidencia. |
| [BURST_TEST.md](BURST_TEST.md) | **Prueba de ráfaga + escala** (2026-08-19): 33/33 llamadas OK, ~10.9× tiempo real. |
| [RISKS.md](RISKS.md) | Riesgo abierto: drift por versión de la APK + mitigaciones (canary en `/health`). |
| [ADDITIONS.md](ADDITIONS.md) | Añadidos propuestos al plan (caché, normalización, progreso, URL de audio, …). |

## Hechos técnicos clave (resumen)

1. **Pausa nativa**: `[[PAUSE:ms]]` funciona dentro del texto (case-insensitive,
   solo enteros). También `<break time="..."/>` SSML.
2. **`[[...]]` es tag de control**: cualquier otro contenido entre dobles
   corchetes se **elimina** del audio (no se pronuncia).
3. **Velocidad/tono/volumen** solo por query string (`?speed&pitch&volume`),
   **no** por etiqueta inline. ⇒ un cambio de voz/params = una llamada aparte.
4. **Escapado**: para que `[[` literal suene, romperlo (`[ [`), usar ancho
   completo (`［［`), o escapar en el parser.
5. Formato de audio: **WAV 24 kHz mono 16-bit** en todas las respuestas
   (validado en 33/33 llamadas — `BURST_TEST.md`).
6. **Rendimiento**: ~10.9× tiempo real, sin throttle real pese a
   `concurrentRate: 1500` (ver `BURST_TEST.md`).
7. **Riesgo abierto**: drift por actualización de la APK — mitigar con
   canary en `/health` (ver `RISKS.md`).

Ver `docs/API.md` para el detalle empírico.

## Artefactos de referencia (fuera de git)

| Artefacto | Contenido |
|-----------|-----------|
| `../voices_es.py` | Catálogo de voces en español (de `/voices`), con helpers `get_voice()`, `voices_by_gender()`. Fuente de `src/mtts/voices.py`. |
| `../tmp/burst_test.py` | Prueba de ráfaga reproducible (`BURST_TEST.md`). |
| `../tmp/length_test.py` | Prueba de longitud por llamada única (resuelve OPEN_QUESTIONS #10). |
| `../tmp/apk/decompiled-apk-1.8.0.tar.gz` | Decompilación consolidada del APK 1.8.0 (regresión de `RISKS.md`). |
