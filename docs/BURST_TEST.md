# Prueba de ráfaga y de escala contra el servidor MultiTTS (8774)

> **Fecha:** 2026-08-19
> **Entorno:** servidor en vivo `http://127.0.0.1:8774` (APK multi-tts 1.8.0,
> `ForwardService`), Termux / Android 15, cliente Python 3.14.
> **Voz:** `microsoft_es-MX-DaliaNeural-MiAndroidAccesible` (motor offline;
> no toca red).
> Script reproducible: `tmp/burst_test.py` · Salida completa: `tmp/burst_test_output.txt`.

**Objetivo:** validar empíricamente las dos suposiciones de rendimiento que
`docs/ENGINE.md` hacía sin evidencia:

1. ¿Aguanta el servidor ráfagas de llamadas consecutivas sin delay (errores
   500, cuerpos vacíos, timeouts)?
2. ¿Cuál es el throughput real para dimensionar el motor de diálogos?

---

## Metodología

- **Warm-up:** 1 llamada antes de medir (el handler pasa por estados
  `msg_idle` / `msg_no_running_task` tras cada síntesis; se descarta del
  conteo).
- **Ráfagas:** N llamadas consecutivas con delay configurable entre ellas.
- **Validación por llamada:** status HTTP, cabecera `RIFF/WAVE`, canales = 1,
  sample rate = 24 000 Hz, bits = 16, duración decodificada, latencia.
- **Post-condición:** revisión de `/log` para descartar errores nuevos.

---

## Resultado 1 — Ráfagas (33 llamadas, 33 válidas, 0 fallos)

### Ráfaga A — 20 llamadas cortas (1.2–2.3 s de audio), delay = 0 ms

| Métrica | Valor |
|---|---|
| OK / total | **20 / 20** |
| Latencia mín / media / máx | 180 / 211 / 260 ms |
| Audio total sintetizado | 35.6 s |

### Ráfaga B — 8 llamadas largas (6.9–8.2 s de audio), delay = 0 ms

| Métrica | Valor |
|---|---|
| OK / total | **8 / 8** |
| Latencia mín / media / máx | 618 / 679 / 735 ms |
| Audio total sintetizado | 60.2 s |

### Ráfaga C — 5 llamadas cortas, delay = 1500 ms (control)

| Métrica | Valor |
|---|---|
| OK / total | **5 / 5** |
| Latencia mín / media / máx | 147 / 190 / 235 ms |
| Audio total sintetizado | 7.7 s |

### Observaciones transversales

- **Cero 500s, cero cuerpos vacíos, cero timeouts, cero 200-vacíos** en las
  33 llamadas.
- **Formato WAV 100 % consistente:** las 33 respuestas fueron PCM mono,
  24 000 Hz, 16-bit — exactamente el formato que asume `concat_wav()` en
  `docs/ENGINE.md`.
- **`concurrentRate: 1500` (de `/legado`) es metadata inerte** del forwarder
  de Legado, no un throttle del endpoint: con delay 0 las llamadas salieron
  en ~200 ms (muy por debajo de 1500 ms) sin degradación acumulativa, y con
  delay 1500 ms la latencia incluso bajó (147 ms mín). No condiciona el
  diseño del motor.
- **`/log` sin errores nuevos:** solo entradas viejas del 2026-02-27 de la
  voz online `filmora` (`JSONException` de su provider). La voz offline no
  genera logs de error; el motor online (vulnerable) queda fuera del
  alcance de esta prueba y del caso de uso de diálogos.

---

## Resultado 2 — Escala real (prueba del usuario, 2026-08-19)

Síntesis de un texto largo con el pipeline existente sobre el mismo servidor:

| Métrica | Valor |
|---|---|
| Palabras / caracteres | 520 / 3 325 |
| Tiempo de proceso TTS | 20.70 s |
| Tiempo de reproducción del audio | 225.12 s |
| **Throughput** | **10.9 × tiempo real** |

Confirma a escala de escena completa (3.7 min de diálogo) lo que midieron
las ráfagas: un pipeline serial no se nota a escala de guion.

---

## Conclusiones para el plan

1. **El motor v1 puede ser estrictamente serial y sin delay forzado.** El
   diseño de `docs/ENGINE.md` (parse → chunks → síntesis serial → concat
   PCM) es directamente viable tal como está. No hacen falta colas,
   reintentos agresivos ni rate limiting del lado del cliente (más allá del
   reintento ya existente en `api.py` para fallos puntuales).
2. **Proyección de rendimiento:** ~10–11 × tiempo real ⇒ un diálogo de 100
   líneas (~4–5 min de audio) ≈ **30–40 s de render** sin caché. Sin
   presión para paralelizar.
3. **La caché de chunks (`docs/ADDITIONS.md` §1) se justifica por
   productividad** (re-renders al editar una línea), no por throughput del
   servidor.
4. El único riesgo de caja negra que queda abierto es el **drift por
   versión de la APK** — ver `docs/RISKS.md`.

---

## Contexto de riesgos cerrados con esta prueba

| Riesgo (pre-prueba) | Estado | Evidencia |
|---|---|---|
| El servidor es de tarea única y rebasa llamadas encadenadas | **Cerrado** | 33/33 con delay 0, latencias estables |
| `concurrentRate: 1500` es un throttle que obliga a serializar con delay | **Cerrado** | Latencias ~200 ms con delay 0; sin degradación |
| El rendimiento no alcanza para diálogos completos | **Cerrado** | 10.9 × tiempo real a escala de 520 palabras |
| El formato WAV podría variar entre llamadas y romper `concat_wav` | **Cerrado** | 33/33 respuestas mono/24 kHz/16-bit |
| Drift por actualización de la APK | **Abierto** | No testeable hoy — ver `docs/RISKS.md` |
