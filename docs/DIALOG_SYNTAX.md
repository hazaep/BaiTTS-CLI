# Sintaxis del guion de diálogos

Lenguaje de marcas simple para describir un diálogo que el **motor de
diálogos** interpreta y convierte en audio. Está pensado para ser escrito a
mano **o** generado por una IA, y para consumirse tanto desde CLI como desde
la API REST.

## Principios

1. **Legible y tolerante**: líneas en blanco y comentarios libres.
2. **Un personaje = una configuración default** (voz + velocidad + tono +
   volumen + pausas). Se define el *cast* una vez y se opera sobre él.
3. **`[ ]` = directiva de control** (línea propia, no se habla).
4. **`[[...]]` = etiqueta nativa del motor** (va dentro del texto hablado).
   Solo `[[PAUSE:ms]]` llega al motor; el resto se escapa.
5. **`( )` / `[ ]` sueltos en el texto** = acotación o texto literal, según
   posición (ver reglas del parser).

## Elementos

### 1. Comentario

Todo lo que empieza con `#` (línea propia) se ignora.

```
# esto es un comentario
```

### 2. Definición de personaje (cast)

```
@nombre = ID_VOZ (opciones)
```

- `ID_VOZ` = identificador real del catálogo de `/voices`
  (ej. `microsoft_es-MX-DaliaNeural-MiAndroidAccesible`).
- `(opciones)` = lista separada por comas, con `clave=valor`:
  `speed`, `pitch`, `volume`, `pause_after`.

```
@narrador = microsoft_es-MX-DaliaNeural-MiAndroidAccesible (speed=40 pitch=27 volume=45 pause_after=500)
@juan     = microsoft_es-MX-JorgeNeural-MiAndroidAccesible (speed=42 volume=48)
```

- `pause_after` (**por personaje**): silencio PCM local inyectado automáticamente
  tras **cada línea** hablada por ese personaje. No llama a `/forward`. Default `0`
  (sin pausa). Se suma a las pausas puntuales `[pausa N]` y a las pausas dramáticas
  intra-línea `[[PAUSE:ms]]`. Ver sección 5.

También se puede cargar un cast desde JSON (ver `docs/ENGINE.md`).

### 3. Diálogo

```
personaje: texto
```

Sintetiza `texto` con la configuración del personaje.

```
narrador: Era una noche oscura y tormentosa.
```

### 4. Override por línea

```
personaje (opciones): texto
```

Cambia parámetros **solo para esa línea** (se fusionan sobre la config del
personaje).

```
juan (speed=20 pitch=35): No deberías estar aquí.
```

**Regla de desambiguación (override vs acotación):** un paréntesis situado
**entre el nombre del personaje y el `:`** es override **solo si** la clave
está en `{speed, pitch, volume, pause_after}` y el valor es numérico.
Cualquier otro paréntesis en esa posición —y **todos** los que van después
del `:`— es texto hablado/acotación. Así `(velocidad=alta)` o `(raro=x)`
nunca se interpretan como override silencioso. Ver OPEN_QUESTIONS #3.

### 5. Pausa entre líneas (directiva)

```
[pausa N]
[pause N]
[pausa 1.5s]
```

Silencio de `N` milisegundos. Con sufijo `s` → segundos (decimales permitidos).

```
[pausa 800]
[pausa 1.5s]      # equivale a 1500 ms
```

### 6. Pausa dramática dentro del texto (etiqueta nativa)

Dentro de un diálogo, `[[PAUSE:ms]]` produce silencio **nativo** del motor.
Solo enteros.

```
juan: Vete... [[PAUSE:400]] antes de que sea tarde.
```

### 7. Acotación / dirección (no se habla)

- En una **línea propia** entre paréntesis: se ignora (acotación de escena).
- Entre `[ ]` con contenido **no numérico** en línea propia: se ignora.

```
(se escuchan truenos a lo lejos)
[juan mira por la ventana]
```

> ⚠️ Regla de desambiguación: `[pausa N]` y `[pause N]` son directivas de
> pausa; cualquier otro `[...]` en línea propia se trata como acotación.
>
> ⚠️ Para paréntesis **entre nombre y `:`**, ver la regla del override
> (sección 4): solo es override si la clave ∈ `{speed, pitch, volume,
> pause_after}` y el valor es numérico; en cualquier otro caso —y siempre
> después del `:`— es texto hablado o acotación, no override.

### 8. Control global (directiva)

Cambia los valores por defecto **desde ese punto en adelante** del guion.

```
[vel 35]      # speed por defecto
[pitch 30]    # pitch por defecto
[vol 50]      # volume por defecto
```

Afecta a todas las líneas posteriores (los overrides por línea siguen
teniendo prioridad).

---

## Escapado de símbolos que interfieren

El motor interpreta **cualquier** `[[...]]` como etiqueta de control y lo
**elimina del audio**. Si el texto real (ej. un diálogo generado por IA)
contiene `[[...]]` literal, hay que neutralizarlo antes de enviarlo a
`/forward`.

### Reglas del parser (obligatorias)

1. Solo el patrón `[[PAUSE:<entero>]]` (case-insensitive) se considera
   **directiva nativa** y se deja pasar al motor.
2. Cualquier otro `[[...]]` se considera **texto literal** y se escapa:
   - `[[` → `[ [`
   - `]]` → `] ]`
3. Los corchetes simples `[ ]`, paréntesis `( )`, `#`, `@`, `:`, `=` **no
   interfieren** con el motor y no necesitan escapado (se pronuncian normal).

### Tabla de escapado

| Quiero que suene...      | Escribo en el guion          | El parser envía al motor       |
|--------------------------|------------------------------|--------------------------------|
| `hola [mundo]`           | `hola [mundo]`               | `hola [mundo]` (sin cambios)   |
| `hola [[mundo]]` literal | `hola [[mundo]]`             | `hola [ [mundo] ]`             |
| pausa de 1 s             | `[[PAUSE:1000]]`             | `[[PAUSE:1000]]` (se respeta)  |
| `[[esto]] no es etiqueta`| `[[esto]] no es etiqueta`    | `[ [esto] ] no es etiqueta`    |

> Alternativa para quien escribe a mano: usar directamente corchetes
> separados `[ [` o caracteres de ancho completo `［［` en el guion. El parser
> los acepta y los deja pasar.

### Símbolos seguros (no se escapan)

`[`, `]`, `(`, `)`, `#`, `@`, `:`, `=`, `\` — el motor los pronuncia con
normalidad. La sintaxis del guion (`@personaje`, `personaje:`, `[pausa N]`,
`#comentario`) se resuelve **antes** en el parser y nunca llega al motor.

---

## Ejemplo completo

```text
# --------------------------------------------------
# Ejemplo: dos personajes + narrador
# --------------------------------------------------

@narrador = microsoft_es-MX-DaliaNeural-MiAndroidAccesible (speed=40 pitch=27 volume=45 pause_after=400)
@juan     = microsoft_es-MX-JorgeNeural-MiAndroidAccesible (speed=42 volume=48 pause_after=300)
@ana      = vocalizer_spa-mex-paulina-high-MiAndroidAccesible (speed=38 volume=50)

narrador: Era una noche oscura y tormentosa.
[pausa 800]
(se escuchan truenos)
ana: ¿Quién anda ahí? [[PAUSE:300]] ¿Eres tú, Juan?
juan (speed=20): Sí... soy yo. No deberías estar aquí.
ana: (temblando) ¿Por qué dices eso?
[pausa 1.2s]
narrador: Y así, sin más, la puerta se cerró.
```

---

## Coexistencia CLI / API

La misma sintaxis se usa en ambos casos:

- **CLI**: `mtts dialog -f guion.txt -c cast.json -o salida.wav --lrc --play`
- **API**: `POST /dialog` con el cuerpo `{ "script": "...", "cast": {...}, "lrc": true }`

Ver `docs/ENGINE.md` (implementación) y `docs/OPENAPI.md` (contrato REST).
