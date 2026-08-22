# Motor de diálogos — Diseño e implementación

Convierte un guion (ver `docs/DIALOG_SYNTAX.md`) en un único archivo de audio,
haciendo las llamadas necesarias a `GET /forward` y concatenando el resultado.

## Por qué hace falta un motor

El servidor MultiTTS solo acepta **una voz + una velocidad + un tono +
un volumen por petición** (`?voice&speed&pitch&volume`). No se pueden cambiar
esos parámetros *dentro* de un mismo `text` (las etiquetas `[[speed]]`,
`[[pitch]]`, `[[volume]]` inline **no funcionan**, verificado en `docs/API.md`).

Por tanto, para un diálogo con varios personajes y matices, el motor debe:

1. **Parsear** el guion en una lista de *items*.
2. **Trocear** en *chunks* (un chunk = un tramo hablado con parámetros fijos).
3. **Sintetizar** cada chunk con su propia llamada a `/forward`
   (con **caché** y **validación** de respuesta, ver abajo).
4. **Inyectar silencio** para las pausas (localmente, sin llamada).
5. **Concatenar** los frames PCM en un WAV final (con **normalización**
   opcional de loudness).
6. Opcionalmente, generar **LRC** y/o **reproducir**.

> El diseño es **serial y sin delay forzado**: la evidencia de
> `docs/BURST_TEST.md` (33/33 llamadas, ~10.9× tiempo real) confirma que no
> hacen falta colas ni rate limiting del lado del cliente.

## Modelo de datos interno

El parser produce una lista de items. Cada item es uno de:

```python
Say(personaje: str, text: str, params: dict)   # tramo hablado
Pause(ms: int)                                  # silencio
Control(kind: str, value: float)                # [vel N] [pitch N] [vol N]
```

- `params` ya viene resuelto (defaults globales < cast < override línea).
- El texto de un `Say` ya viene **escapado** (ver abajo).

## Pipeline

```
script (str)
   │
   ▼
parse_script() ──▶ list[Say|Pause|Control]
   │
   ▼
resolve_cast() ──▶ cada Say con voice/speed/pitch/volume finales
   │
   ▼
escape_text() ──▶ neutralizar [[...]] salvo [[PAUSE:ms]]
   │
   ▼
synthesize() ──▶ [caché?] → 1 GET /forward por Say ──▶ bytes WAV ──▶ [validar]
   │
   ▼
render() ──▶ inyectar silencio PCM para Pause ──▶ [normalizar?] ──▶ concat ──▶ WAV
   │
   ├─▶ (opcional) build_lrc()  → timestamps por línea
   └─▶ (opcional) play()       → mplayer
```

## Módulos propuestos

```
mtts/
  dialog/
    parser.py        # parse_script() → items
    characters.py    # carga/valida cast (JSON + inline)
    engine.py        # orquestador: parse → synth → render
    escape.py        # escape_text() y validación de [[PAUSE:ms]]
  audio.py           # read_wav_frames(), make_silence(), concat_wav(),
                     # write_wav(), normalize_loudness(), validate_wav()
  cache.py           # caché de chunks por hash (ADDITIONS.md §1)
  voices.py          # catálogo de voces (de /voices; ver voices_es.py)
  api.py             # cliente HTTP del servidor MultiTTS (reutilizado)
```

## Resolución de parámetros (orden de prioridad)

```
1. defaults globales        (los que arrancan la sesión, o [vel]/[pitch]/[vol])
2. cast del personaje       (voice + speed + pitch + volume + pause_after)
3. override de línea        (nombre (speed=20): texto)
```

`voice` no tiene default global (siempre viene del cast o de la línea).

- **Merge por campo, no por personaje:** cuando un personaje está en el cast
  JSON *y* tiene definición inline, gana el JSON campo a campo. Un JSON que
  define solo `speed` no borra el `pitch` inline. Ver OPEN_QUESTIONS #5.
- **Voz por defecto:** `default_voice` acepta un `string` (global) o un
  `map{locale: voz}` (por idioma). Si no se encuentra voz para el locale del
  guion, cae al global. Personaje ausente del cast → esta voz, **con warning**
  (nombre + línea). El silencio aquí produce audios con todos los personajes
  con la misma voz sin explicación. Ver OPEN_QUESTIONS #6.

## Síntesis por chunk

Cada `Say` produce **una** llamada:

```
GET /forward?text=<texto escapado>&voice=<id>&speed=<n>&pitch=<n>&volume=<n>
```

- `speed`, `pitch`, `volume` se envían **siempre** (evita el bug de
  `speed` vacío → 400 documentado en `docs/API.md`).
- Se guarda la duración real del WAV devuelto (para el LRC y la ETA).

### Caché de chunks (por hash)

Antes de llamar a `/forward`, se consulta la caché:

- **Clave:** `hash(text, voice, speed, pitch, volume)` con SHA-256, en
  `~/.cache/mtts/<sha256>.wav`.
- **Incluye la versión del contrato** (`"apk-1.8.0"`) en el hash o en el
  prefijo de directorio: si el formato de salida cambia tras una
  actualización de la APK, la caché antigua se invalida automáticamente.
- `--no-cache` en CLI / campo `cache: false` en API fuerza re-síntesis.
- Limpieza por tamaño máximo (`mtts cache clear` / umbral configurable).
- **Justificación:** productividad en re-renders (editar una línea re-sintetiza
  solo esa línea), no throughput del servidor. Detalle en `ADDITIONS.md` §1.

### Validación de cada respuesta

El wrapper de síntesis trata como **error reintentable** (no como chunk
válido):

- cuerpo vacío o sin cabecera `RIFF/WAVE`;
- formato distinto de **1 canal / 24 000 Hz / 16-bit**;
- duración decodificada = 0.

Esto convierte el drift de formato de la APK en un error claro con contexto
("chunk 37 de 100: esperaba 24000 Hz, llegó 44100") en vez de audio corrupto.
Barato de implementar sobre `wave` de stdlib. Ver `RISKS.md` §Mitigaciones.

### Longitud de chunk

Sin límite duro en v1. A partir de **~1 000 caracteres**, emitir **warning**
informativo (no bloquear): el problema no es el fallo sino la latencia sin
feedback y la granularidad del LRC. Evidencia: `tmp/length_test.py`. Ver
OPEN_QUESTIONS #10.

## Silencio (pausas)

- `Pause(ms)` se renderiza como **silencio PCM** (frames en cero) de
  `ms / 1000 * 24000` frames. No requiere llamada al servidor.
- `pause_after` del personaje = silencio automático tras cada `Say` de ese
  personaje.
- `[[PAUSE:ms]]` **dentro** del texto se deja pasar al motor (es nativo y
  más fiel para pausas dramáticas), no se convierte en silencio local.

## Escapado

En `escape_text()`:

1. `[[PAUSE:<int>]]` (case-insensitive) → se conserva tal cual.
   - Con decimales o no numérico → **warning + truncar a entero** (no
     rechazar: los guiones generados por IA producen `[[PAUSE:0.5s]]` con
     naturalidad). Ver OPEN_QUESTIONS #8.
2. Cualquier otro `[[...]]` → `[[` se reemplaza por `[ [` y `]]` por `] ]`.
3. El resto del texto se deja intacto (corchetes simples, `@`, `:`, etc. no
   interfieren con el motor).

Detalle y tabla completa en `docs/API.md` (sección "Escapado") y
`docs/DIALOG_SYNTAX.md`.

## Concatenación WAV

- Todos los WAV del servidor son **24 kHz, mono, 16-bit PCM** (mismo formato,
  verificado en 33/33 llamadas — `BURST_TEST.md`), así que se concatenan
  **solo los frames de datos** (sin repetir cabecera).
- `audio.concat_wav(frames_list) → bytes` escribe una sola cabecera WAV y
  luego todos los frames.
- Si un chunk falla (voz inválida / 500 / formato inválido), se reintenta
  (lógica ya existente en `api.py`) y, si sigue fallando, se **registra y
  salta** sin romper el resto.

### Normalización de loudness (opcional, opt-in)

- `--normalize` (CLI) / `normalize: true` (API) escala cada chunk al mismo
  RMS objetivo antes de concatenar.
- **Off por defecto**: el audio por defecto es bit-exact con lo que el
  servidor devuelve.
- RMS objetivo configurable; escalado con saturación (clamp) a 16-bit.
- Justificación: voces de motores distintos tienen niveles distintos y los
  saltos de volumen entre personajes se oyen mal. Ver `ADDITIONS.md` §2.

## LRC (opcional)

- Por cada `Say` se registra `(timestamp_inicio, texto_limpio)`.
- El texto del LRC se limpia de etiquetas `[[...]]` y acotaciones.
- `timestamp_inicio` = suma de duraciones acumuladas (chunks + silencios).
- Formato idéntico al actual `lrc.py`.

## Reproducción (opcional)

- Al terminar, si se pide `--play`, se lanza `mplayer <archivo>`.
- En la API, `play` no aplica: el audio se entrega por **URL temporal**
  (`GET /audio/{id}` con TTL ~1 h), no como binario embebido. Ver
  `ADDITIONS.md` §4 y `OPENAPI.md`.

## Progreso y estimaciones

- CLI: línea de estado `n/N chunks · 12.3 s / ~40 s (ETA)` en `mtts dialog`.
- API: array `chunks` en la respuesta con `(personaje, texto, duración,
  params)` — la duración medida por chunk alimenta la ETA del dashboard.
- La ETA es fiable: throughput estable ~10–11× tiempo real (medido).

## Errores y logging

- Voz desconocida → error claro con el nombre del personaje y la línea.
- Personaje fuera del cast → **warning** con nombre y línea (cae al default).
- `[[PAUSE:...]]` con decimales o no numérico → warning, se trunca/escapa.
- Chunk largo (~1 000+ caracteres) → warning informativo.
- Respuesta WAV inválida (formato/duración) → error reintentable con contexto
  de chunk.

## Tests mínimos

- Parser: cast, diálogos, overrides, pausas (ms y s), acotaciones, controles.
- Escape: `[[PAUSE:1000]]` se conserva; `[[foo]]` se escapa; `[[PAUSE:0.5s]]`
  → warning + truncado; texto normal intacto.
- Resolución de parámetros: prioridad global < cast < línea; merge por campo.
- Audio: `make_silence(ms)` produce el nº correcto de frames; `concat_wav`
  produce un WAV válido (lo abre `wave`); `validate_wav()` detecta formato
  incorrecto; `normalize_loudness()` ajusta RMS con clamp.
- Caché: mismo chunk → misma clave; `--no-cache` fuerza re-síntesis; cambio
  de cualquier parámetro → clave distinta.
