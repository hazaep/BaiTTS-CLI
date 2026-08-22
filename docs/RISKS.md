# Riesgo abierto: drift por versión de la APK

> **Fecha:** 2026-08-19
> **Estado:** único riesgo de caja negra que queda abierto tras las pruebas
> de `docs/BURST_TEST.md`.

## Descripción

No tenemos el código fuente de la APK **multi-tts 1.8.0** y una parte está
ofuscada (rutas y parámetros con XOR cíclico, clave `a6.AbstractC0220g.f`).
Todo el contrato documentado en `docs/API.md` proviene de la APK 1.8.0
decompilada y verificada en vivo contra el servidor:

| Elemento del contrato | Dónde se usa en el plan |
|---|---|
| Rutas desofuscadas (`/forward`, `/voices`, `/legado`, `/log`) | Cliente HTTP (`api.py`, futuro `mtts.api`) |
| Parámetros `?text&voice&speed&pitch&volume` y sus defaults/quirks | Cada llamada de síntesis del engine |
| Semántica de `[[PAUSE:ms]]` y tags que se tragan | `dialog/escape.py`, `docs/DIALOG_SYNTAX.md` |
| Salida WAV PCM mono 24 kHz 16-bit | `audio.concat_wav()` — **asume formato único** |
| Quirks (200 con cuerpo vacío sin `voice`; `speed` vacío → 400) | Validación del cliente |

**El riesgo:** si la app se actualiza (o cambia algo en el motor), cualquier
parte de ese contrato puede romperse **silenciosamente**. El caso más dañino
no es un 404 evidente, sino un **cambio de formato de salida** (p. ej. de
24 kHz mono a 44.1 kHz estéreo, o a MP3): el endpoint seguiría respondiendo
200, `concat_wav()` concatenaría frames de dos formatos distintos y el WAV
resultante sería **basura audible** (ruido, velocidad incorrecta) sin que
ningún HTTP status lo delate.

## Impacto si materializa

- Motor de diálogos roto (concatenación inválida o audio corrupto).
- Latencias/quirks documentados desactualizados (`docs/API.md` pierde valor
  de referencia).
- Diagnóstico difícil: los fallos de formato no arrojan errores HTTP.

## Mitigaciones

1. **Pin de versión (ya en el plan, Fase 0):** no actualizar la APK que
   expone el servidor sin re-ejecutar la verificación. Mantener el APK
   `multi-tts_1.8.0.apk` y los artefactos de decompilación como referencia
   de regresión.
2. **Síntesis canary en `GET /health` (Fase 3):** no conformarse con
   "¿8774 responde?". El healthcheck debe:
   1. Llamar a `/forward` con un texto fijo ("hola") y voz offline conocida.
   2. Parsear la respuesta con el módulo `wave` (o `audio.py`).
   3. Validar: cabecera `RIFF/WAVE`, **1 canal, 24 000 Hz, 16-bit**,
      duración > 0.
   4. Devolver `ok` solo si todo lo anterior se cumple; si no,
      reportar qué falló (alcance, status, formato).

   Esto detecta drift de formato —el fallo más silencioso— en el primer
   healthcheck tras una actualización.
3. **Validación de cada respuesta en el engine (Fase 2):** el wrapper de
   síntesis debe tratar como **error reintenable** (no como chunk válido):
   cuerpo vacío, cabecera WAV inválida, o formato distinto de
   mono/24 kHz/16-bit. Barato de implementar sobre `wave` de la stdlib y
   convierte el drift en un error claro con contexto ("chunk 37 de 100:
   esperaba 24000 Hz, llegó 44100") en vez de audio corrupto.
4. **Test de ráfaga como test de regresión:** `tmp/burst_test.py` (ver
   `docs/BURST_TEST.md`) sirve tal cual para re-validar tras cualquier
   actualización de la APK: 20 llamadas, validar formato de cada una.
   Ejecutarlo debería ser parte del protocolo post-actualización.
5. **Re-descompilación solo bajo demanda:** el pendiente de Fase 0
   (`jadx --show-bad-code` para documentar el `switch (path.hashCode())`
   exacto) **no es prerrequisito de nada** — las rutas ya están
   desofuscadas y verificadas en vivo. Activarlo únicamente si el servidor
   cambia de comportamiento y hay que re-mapear rutas.

## Señales tempranas de que el contrato cambió

- `/forward` empieza a devolver cuerpos vacíos o 500 con voces antes válidas.
- Las duraciones de audio reportadas por el engine se desvían >10 % de lo
  esperado para un texto conocido.
- `/voices` cambia de tamaño/estructura (hoy: 107 voces).
- El WAV canary del healthcheck no valida formato.
