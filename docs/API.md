# MultiTTS — Servidor local de reenvío TTS (puerto 8774)

Documentación de ingeniería inversa de la APK **multi-tts 1.8.0** (clase
`A6.d` / `org.nobody.multitts.service.ForwardService`), verificada contra el
servidor en vivo en `http://127.0.0.1:8774`.

> **Fecha de última verificación:** 2026-08-17
> Toda la sección de "etiquetas nativas" fue contrastada empíricamente con
> la voz `microsoft_es-MX-DaliaNeural-MiAndroidAccesible`.

---

## Resumen

- Clase servidor: `A6.d` extiende `e5.i` (NanoHTTPD).
- **Bind**: `0.0.0.0:8774` (escucha en todas las interfaces; sin auth).
- Las rutas y parámetros están **ofuscados con XOR** (`a6.AbstractC0220g.f(data, key)`,
  clave cíclica). Desofuscados a continuación.

## Endpoints

| Método | Ruta       | Content-Type      | HTTP | Descripción |
|--------|-----------|-------------------|------|-------------|
| GET    | `/forward`| `audio/x-wav`     | 200  | Sintetiza texto a WAV |
| GET    | `/voices` | `application/json`| 200  | Catálogo completo de voces |
| GET    | `/legado` | `application/json`| 200  | Config para el lector **Legado** (metadata del forwarder) |
| GET    | `/log`    | `text/plain`      | 200  | Contenido del log del motor TTS |
| GET    | (otra)    | `text/html`       | 404  | `<html><body>Page Not Found.</body></html>` |

> Nota: **no existe** `/info`. La ruta que devuelve metadatos es `/legado`.

---

## `GET /forward`

Sintetiza texto y devuelve el audio en formato **WAV PCM** (mono,
24 000 Hz, 16-bit little-endian), `Transfer-Encoding: chunked` (sin
`Content-Length`).

### Parámetros de consulta

| Param    | Requerido | Tipo   | Rango  | Interno (código)                              | Semántica verificada |
|----------|-----------|--------|--------|-----------------------------------------------|----------------------|
| `text`   | sí*       | string | —      | `Normalizer.normalize(text, NFC)`             | Texto a sintetizar   |
| `voice`  | sí*       | string | —      | `i.g(voice, …)`; si vacío usa voz por defecto | ID de voz (ver `/voices`) |
| `volume` | no        | float  | 0–100  | se pasa directo al motor                      | Ganancia de amplitud (mayor = más fuerte) |
| `speed`  | no        | float  | 0–100  | `int(speed) * 6` (→ 0–600)                    | Velocidad: mayor = más rápido |
| `pitch`  | no        | float  | 0–100  | `int(pitch) * 2` (→ 0–200)                    | Tono de voz |

\* En la práctica `text` y `voice` deben ir poblados. Sin `voice` el
servidor responde 200 con cuerpo vacío; con voz inválida responde 500.

### Valores por defecto (si el parámetro está vacío)

| Param    | Default interno |
|----------|-----------------|
| `volume` | `50.0`          |
| `speed`  | 400 → `SC_BAD_REQUEST` si falta velocidad (**comportamiento especial**, ver nota) |
| `pitch`  | `C0940a.f15592Z.f15618b` (config compartida, default **100** → equivale a `pitch=50`) |

> El `speed` se multiplica por 6: `speed=50` → 300. Si `speed` está
> **vacío**, el código asigna `HttpStatus.SC_BAD_REQUEST` (400) a la
> variable (aunque en la práctica la petición puede no llegar a validarse
> como 400 en la red; se recomienda enviar siempre `speed`).

### Respuesta correcta

```
HTTP/1.1 200 OK
Content-Type: audio/x-wav
Transfer-Encoding: chunked
<bytes WAV: cabecera 44 bytes + PCM 16-bit>
```

### Respuesta de error (voz inválida, error del motor)

```
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{"success":false,"error":{"message":"Voz no encontrado:voz_invalida_xyz"}}
```

Estructura: `{ "success": bool, "error": { "message": string } }`.

---

## Etiquetas nativas dentro de `text` (VERIFICADO 2026-08-17)

El motor procesa un **mini-lenguaje de etiquetas** dentro del campo `text`.
Es la clave para pausas dramáticas y para controlar qué se habla y qué no.

### Regla de oro: `[[...]]` es un tag de control

Todo lo que va entre **doble corchete** `[[...]]` **NO se pronuncia**:
se interpreta como directiva y se elimina del audio. Solo las directivas
reconocidas producen un efecto (pausa); el resto se descarta en silencio.

| Entrada               | Duración  | Interpretación |
|-----------------------|-----------|----------------|
| `hola`                | 0.45 s    | control |
| `hola [[mundo]]`      | 0.45 s    | `[[mundo]]` se **traga** → solo suena "hola" |
| `hola [[MUNDO]]`      | 0.45 s    | igual (case-insensitive para la directiva) |
| `hola [[foo:1000]]`   | 0.45 s    | `[[foo:…]]` desconocido → se descarta |
| `hola [[mundo]] amigo`| 1.01 s    | suena "hola amigo" |

> ⚠️ **Implicación para diálogos generados por IA:** si el texto a sintetizar
> contiene `[[...]]` **literal** (ej. marcado de otra herramienta, notas de
> guion), el motor lo eliminará del audio sin pronunciarlo. Hay que
> **escaparlo** o **limpiarlo** antes de enviar (ver sección "Escapado").

### Pausa nativa: `[[PAUSE:ms]]`

Produce un silencio dentro del audio. Es **case-insensitive**
(`[[pause:500]]` ≡ `[[PAUSE:500]]`).

| Entrada                  | Duración   | Notas |
|--------------------------|------------|-------|
| `[[PAUSE:1500]]`         | 1.500 s    | silencio exacto |
| `[[PAUSE:1.5]]`          | 0.500 s    | ⚠️ NO soporta decimales: interpreta solo "1" (≈ 0.5s según motor) |
| `hola [[PAUSE:250]] mundo`| 1.236 s   | pausa de 250 ms entre palabras |
| `hola [[PAUSE:2000]]`    | 2.452 s    | 0.45s de "hola" + 2s de silencio |

> **Unidad:** milisegundos. **Solo enteros** (los decimales se truncan o dan
> comportamiento indefinido). Para pausas con precisión de ms, el engine de
> diálogos debe inyectar silencio PCM local en vez de depender de decimales.

### Pausa SSML: `<break/>`

El motor **también** acepta SSML `<break>` (útil si el texto ya viene en SSML).

| Entrada                         | Duración   | Notas |
|---------------------------------|------------|-------|
| `hola <break time="500ms"/> mundo` | 3.67 s  | pausa larga (incluye pausa natural del motor) |
| `hola <break time="2000ms"/> mundo`| 3.62 s  | |
| `hola <break time="2s"/> mundo`    | 3.21 s  | |
| `hola <break time="2"/> mundo`     | 4.07 s  | sin unidad → interpreta por defecto |
| `hola <break strength="strong"/> mundo` | 3.17 s | |
| `hola <break/> mundo`              | 1.93 s  | pausa corta |

> Nota: las duraciones de `<break>` incluyen la pausa natural del motor tras
> "hola", por eso son mayores que el silencio puro. Para silencios
> deterministas se prefiere `[[PAUSE:ms]]` o inyección de silencio PCM.

### Lo que NO funciona como tag inline (verificado)

| Intento              | Resultado |
|----------------------|-----------|
| `[[speed:N]]`        | ❌ errático. `[[speed:90]]` rompe la síntesis (0.013 s, audio vacío) |
| `[[RATE:N]]` / `[[rate N]]` | ❌ sin efecto (se traga el tag, no cambia velocidad) |
| `[[pitch:N]]`        | ❌ sin efecto fiable (`[[pitch:90]]` → 5.27 s vs 4.23 s control, inconsistente) |
| `[[volume:N]]`       | ❌ sin efecto |
| `[[SILENCE:...]]`, `[[slnc ...]]` | ❌ no reconocido (se traga el tag) |

> **Conclusión de diseño:** velocidad, tono y volumen se controlan **solo por
> query string** (`?speed=&pitch=&volume=`). Por tanto, un cambio de estos
> parámetros en mitad de un diálogo requiere **una llamada aparte** a
> `/forward`. Las pausas, en cambio, sí pueden ir inline con `[[PAUSE:ms]]`.

---

## Escapado de símbolos que interfieren

Como `[[...]]` es una directiva del motor, cualquier `[[` **literal** en el
texto debe neutralizarse. Técnicas verificadas:

| Técnica                              | Resultado | Veredicto |
|--------------------------------------|-----------|-----------|
| `hola [[mundo]]`                     | 0.45 s (se traga "mundo") | ❌ no sirve |
| `hola \[\[mundo\]\]` (backslash)     | 5.23 s    | ⚠️ NO recomendado: el motor deletrea/incluye los backslashes |
| `hola [ [mundo] ]` (espacio)         | 1.00 s    | ✅ funciona: suena "hola [mundo]" (corchete simple, no doble) |
| `hola ［［mundo］］` (fullwidth)       | 0.71 s    | ✅ funciona: los paréntesis fullwidth se hablan o ignoran sin tragar |
| `hola 【【mundo】】` (CJK brackets)    | 0.71 s    | ✅ funciona (ídem) |

### Estrategia recomendada para el engine de diálogos

1. **`[` y `]` simples son seguros**: el motor solo interpreta `[[` como tag.
   Un corchete simple se pronuncia con normalidad.
2. **Para escribir `[[` literal**: romper el doble corchete con un espacio
   (`[ [`), o usar caracteres de ancho completo (`［［`), o —más limpio—
   **limpiar/escapar en el parser antes de enviar** (el engine reemplaza
   `[[` literal por `[ [`, salvo el patrón `[[PAUSE:ms]]` que es la única
   directiva que se permite llegar al motor).
3. **Regla del parser de diálogos**: solo `[[PAUSE:<int>]]` se trata como
   directiva; cualquier otro `[[...]]` se considera texto literal y se
   escapa (`[[` → `[ [`) antes de la llamada.

### Símbolos que NO interfieren (se hablan normal)

`#`, `@`, `:`, `=`, `[ ]`, `( )`, `\` (backslash suelto) se pronuncian sin
efectos especiales en el motor. La sintaxis del guion de diálogos
(`@personaje`, `personaje: texto`, `[pausa N]`, `#comentario`) **no choca**
con el motor porque se resuelve en el parser, **antes** de enviar solo el
texto limpio a `/forward`.

---

## `GET /voices`

Devuelve el catálogo completo de voces (107 voces).

```json
{
  "success": true,
  "data": {
    "count": 107,
    "catalog": {
      "samsung":   [ { "id","name","gender","locale","type" }, … ],
      "vocalizer": [ { "id","name","gender","locale","desc","type" }, … ],
      "filmora":   [ { "id","name","gender","locale","desc","type" }, … ],
      "google":    [ { "id","name","gender","locale","type" }, … ],
      "microsoft": [ { "id","name","gender","locale","desc","type" }, … ],
      "cereproc":  [ { "id","name","gender","locale","desc","type" }, … ],
      "acapela":   [ { "id","name","gender","locale","desc","type" }, … ]
    }
  }
}
```

Campos por voz:
- `id`: identificador a pasar en `?voice=…` (ej. `microsoft_es-MX-DaliaNeural-MiAndroidAccesible`).
- `name`: nombre legible.
- `gender`: `male` / `female`.
- `locale`: idioma-región (ej. `es-MX`).
- `desc`: descripción/estilo (solo algunos motores).
- `type`: `offline` (local) / `online` (requiere red).

### Distribución por motor

| Motor      | Voces | Tipo    |
|------------|-------|---------|
| filmora    | 60    | online  |
| vocalizer  | 12    | offline |
| samsung    | 9     | offline |
| microsoft  | 9     | offline |
| google     | 8     | offline |
| acapela    | 7     | offline |
| cereproc   | 2     | offline |

---

## `GET /legado`

Metadata para el lector **Legado** (plantilla de reenvío). Respuesta real:

```json
{
  "concurrentRate": "1500",
  "contentType": "audio/x-wav",
  "header": "",
  "id": 260672396,
  "lastUpdateTime": 1786927711612,
  "name": "MultiTTS•转发器",
  "url": "http://localhost:8774/forward?volume=50&speed={{speakSpeed*2}}&text={{java.encodeURI(speakText)}}"
}
```

`id` = `hashCode()` de la cadena `"MultiTTS Forwarder"`. La `url` muestra la
plantilla de llamada que usa Legado (`speakSpeed` es 0–50 en esa app, por eso
aparece `*2` para casar con el rango 0–100 del parámetro `speed`).

---

## `GET /log`

Devuelve `text/plain` con el contenido del archivo de log del motor TTS
(útil para depurar errores de síntesis, p.ej. `JSONException` del motor).

---

## Parámetros de audio verificados (empírico, voz Dalia es-MX)

| Caso                    | Resultado |
|-------------------------|-----------|
| `text="Hola mundo"`     | WAV mono 24 kHz/16-bit, 0.74 s |
| `speed=5`  (frase larga)| 2.87 s |
| `speed=50`              | 1.32 s |
| `speed=100`             | 0.81 s  (mayor velocidad ⇒ menor duración) |
| `volume=1`              | RMS ≈ 5578, peak 28991 |
| `volume=100`            | RMS ≈ 11042, peak 32768 (recorte/clipping) |

- `volume` controla la **ganancia** (0–100, mayor = más alto). Con valores
  altos hay saturación (clipping).
- `speed` controla la **velocidad de habla** (mayor = más rápido).

---

## Voces en español (`es-*`) para diálogos

IDs listos para usar (formato `motor_id`):

**Microsoft (offline)**
- `microsoft_es-MX-DaliaNeural-MiAndroidAccesible` — Dalia, female, es-MX
- `microsoft_es-MX-JorgeNeural-MiAndroidAccesible` — Jorge, male, es-MX
- `microsoft_es-MX-Sabina-Apollo` — Sabina, female, es-MX
- `microsoft_es-MX-Raul-Apollo` — Raúl, male, es-MX
- `microsoft_es-ES-ElviraNeural-MiAndroidAccesible` — Elvira, female, es-ES
- `microsoft_es-ES-AlvaroNeural-MiAndroidAccesible` — Alvaro, male, es-ES
- `microsoft_es-ES-Helena-Apollo` — Helena, female, es-ES
- `microsoft_es-ES-Laura-Apollo` — Laura, female, es-ES
- `microsoft_es-ES-Pablo-Apollo` — Pablo, male, es-ES

**Vocalizer (offline)**
- `vocalizer_spa-mex-paulina-high-MiAndroidAccesible` — Paulina, female, es-MX
- `vocalizer_spa-mex-juan-high-MiAndroidAccesible` — Juan, male, es-MX
- `vocalizer_spa-mex-angelica-high-MiAndroidAccesible` — Angélica, female, es-MX
- `vocalizer_spa-esp-monica-high-MiAndroidAccesible` — Mónica, female, es-ES
- `vocalizer_spa-esp-marisol-high-MiAndroidAccesible` — Marisol, female, es-ES
- `vocalizer_spa-esp-jorge-high-MiAndroidAccesible` — Jorge, male, es-ES
- `vocalizer_spa-arg-isabela-high-MiAndroidAccesible` — Isabela, female, es-AR
- `vocalizer_spa-arg-diego-high-MiAndroidAccesible` — Diego, male, es-AR
- `vocalizer_spa-col-ximena-high-MiAndroidAccesible` — Ximena, female, es-CO
- `vocalizer_spa-col-soledad-high-MiAndroidAccesible` — Soledad, female, es-CO
- `vocalizer_spa-col-carlos-high-MiAndroidAccesible` — Carlos, male, es-CO
- `vocalizer_spa-chl-francisca-high-MiAndroidAccesible` — Francisca, female, es-CL

**Acapela (offline)**
- `acapela_spa-MEX-Emilio-MiAndroidAccesible` — Emilio, male, es-MX
- `acapela_spa-MEX-Rodrigo-MiAndroidAccesible` — Rodrigo, male, es-MX
- `acapela_spa-MEX-Rosa-MiAndroidAccesible` — Rosa, female, es-MX
- `acapela_spa-MEX-Valeria-MiAndroidAccesible` — Valeria, female, es-MX
- `acapela_spa-ESP-Antonio-MiAndroidAccesible` — Antonio, male, spa-ESP
- `acapela_spa-ESP-Inés-MiAndroidAccesible` — Inés, female, es-ES
- `acapela_spa-ESP-María-MiAndroidAccesible` — María, female, es-ES

**Cereproc (offline)**
- `cereproc_Ana` — Ana, female, es-ES
- `cereproc_Sara` — Sara, female, es-ES

**Samsung (offline)**
- `samsung_es_mx_f00` / `_l01` — female, es-MX
- `samsung_es_mx_g01` / `_m00` — male, es-MX
- `samsung_es_es_g01` — male, es-ES
- `samsung_es_es_l01` — female, es-ES
- `samsung_es_us_f00` / `_l01` — female, es-US
- `samsung_es_us_g01` — male, es-US

**Google (offline)**
- `google_es-es-x-ana` — female, es-ES
- `google_es-es-x-eea` — female, es-ES
- `google_es-es-x-eeb` — male, es-ES
- `google_es-es-x-eec` — female, es-ES
- `google_es-es-x-eed` — male, es-ES
- `google_es-es-x-eee` — female, es-ES
- `google_es-es-x-eef` — male, es-ES
- `google_es-es-x-nhg` — female, es-ES

---

## Ejemplos con `curl`

```bash
# Listar voces
curl -s http://127.0.0.1:8774/voices

# Sintetizar (guardar WAV)
curl -s "http://127.0.0.1:8774/forward?text=Hola%20mundo&voice=microsoft_es-MX-DaliaNeural-MiAndroidAccesible&volume=45&speed=40&pitch=27" -o salida.wav

# Con pausa nativa
curl -s "http://127.0.0.1:8774/forward?text=Hola%20%5B%5BPAUSE:1000%5D%5D%20mundo&voice=microsoft_es-MX-DaliaNeural-MiAndroidAccesible&volume=45&speed=40&pitch=27" -o salida.wav

# Metadatos Legado
curl -s http://127.0.0.1:8774/legado

# Log del motor
curl -s http://127.0.0.1:8774/log
```

## Notas de implementación del servidor

- El handler `A6.d.e(C0429c)` hace `switch (path.hashCode())` sobre rutas
  desofuscadas en tiempo de ejecución.
- En `/forward`, tras sintetizar, **reescribe la cabecera WAV**: bytes 4–7
  (longitud RIFF) y 40–43 (longitud de datos) a partir de
  `byteArray.length - 44`.
- El texto se normaliza a **NFC** antes de pasar al motor.
- Tras cada síntesis, el estado pasa a `msg_idle`/`msg_no_running_task`
  (se nota en el log: `forward: data len=…`).
- El motor interpreta `[[...]]` como tag de control (lo elimina del audio) y
  reconoce `[[PAUSE:ms]]` (case-insensitive, solo enteros) y `<break/>` SSML.
