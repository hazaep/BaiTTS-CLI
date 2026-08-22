# Razonamiento del agente por decisión

> **Fecha:** 2026-08-19
> Razonamiento completo de cada decisión. El **estado consolidado** (qué está
> resuelto y qué falta confirmar) vive en `docs/OPEN_QUESTIONS.md`; este
> archivo es el respaldo argumental. Las respuestas están informadas por la
> evidencia de `docs/BURST_TEST.md` y cross-referencian `docs/ADDITIONS.md`
> y `docs/RISKS.md`.
>
> **Leyenda:** `[x]` = resuelto por evidencia empírica o consenso técnico;
> `[ ]` = recomendación firme del agente, pendiente de confirmación del humano.

## Sintaxis del guion

1. [x] **Delimitador de personaje**: mantener `personaje: texto`.
   → **Agente:** es el formato natural de guion (convención de
   subtítulos/screenplay), el que una IA generará sin instrucciones extra, y
   el más simple de parsear. `PERSONAJE>` no aporta nada y rompe la
   intuición "esto es un diálogo".
2. [x] **Nombres de personaje con espacios**: sí, permitidos hasta el `:`
   o el `(` de override.
   → **Agente:** coincide con cómo se escriben nombres reales de personajes
   ("voz en off", "señor López"). El parser ya necesita buscar el `:`
   terminador; el costo es cero.
3. [ ] **Override por línea vs acotaciones**: la regla `clave=valor` es
   correcta pero incompleta.
   → **Agente:** desambiguar por **posición + clave conocida**: paréntesis
   entre el nombre y el `:` es override **solo si** la clave ∈
   `{speed, pitch, volume, pause_after}` y el valor es numérico; cualquier
   otro paréntesis en esa posición —y todos los que van después del `:`—
   es texto hablado/acotación. Así `(velocidad=alta)` o `(raro=x)` nunca
   se interpretan como override silencioso. Con esa regla, confirmar que
   no colisiona.

## Cast y voces

4. [x] **Cast JSON separado**: sí (`cast` en API, `-c cast.json` en CLI).
   → **Agente:** imprescindible para Fase 5 (presets de personajes
   reutilizables). El cast inline queda para guiones autocontenidos.
5. [x] **Fusión inline + JSON**: gana el JSON.
   → **Agente:** de acuerdo. El JSON es la config "oficial" persistente; el
   inline es azúcar del guion. Documentar el comportamiento en
   `ENGINE.md`: merge por campo, no por personaje (un JSON que define solo
   `speed` no debe borrar el `pitch` inline).
6. [ ] **Voz por defecto**: configurable, default
   `microsoft_es-MX-DaliaNeural-MiAndroidAccesible`.
   → **Agente:** de acuerdo con la propuesta (es la voz verificada en todas
   las pruebas). Añadir: cuando un personaje del guion falta en el cast y
   cae al default, emitir **warning** con nombre y línea — el silencio aquí
   produce audios con todos los personajes con la misma voz sin explicación.

## Escapado

7. [x] **Escapado canónico `[ [`**: sí.
   → **Agente:** más semántico que `［［` (visible en el audio final si algo
   falla, reversible, ASCII puro). El parser ya lo propone así; confirmar.
8. [ ] **`[[PAUSE:ms]]` con decimales**: warning + truncar a entero.
   → **Agente:** de acuerdo. Rechazar rompería guiones generados por IA
   (que producen `[[PAUSE:0.5s]]` con naturalidad). El warning deja rastro
   en el log para depurar.

## Motor

9. [x] **Chunk por línea**: 1 línea = 1 llamada.
   → **Agente:** **resuelto por evidencia** (`docs/BURST_TEST.md`): el
   servidor aguanta ráfagas sin delay (33/33, latencia media 211 ms) y el
   throughput es ~10.9× tiempo real, así que no hay presión por optimizar
   con agrupación. La simplicidad de parser/LRC fiel gana. La agrupación
   queda como optimización futura medible (si algún día importa).
10. [ ] **Límite de longitud por chunk**: sin límite duro en v1, warning
        informativo.
    → **Agente:** la evidencia dice que textos largos funcionan (ráfaga B:
    ~300 caracteres en ~680 ms; prueba del usuario: 3 325 caracteres en
    una sesión de 20.7 s). El problema de un chunk enorme no es el fallo
    sino la latencia sin feedback y la granularidad del LRC. Propuesta:
    warning a partir de ~1 000 caracteres, sin bloquear.

## Salida

11. [x] **LRC por línea de diálogo**: sí, por línea.
    → **Agente:** la subdivisión por frase requiere estimar duraciones
    dentro del chunk (el servidor no da timestamps); por línea es exacto
    porque se mide cada WAV. Mejora posterior, como dice la propuesta.
12. [x] **MP3**: no ahora; WAV en Fase 2, MP3 vía `ffmpeg` a demanda.
    → **Agente:** de acuerdo. El formato nativo es WAV; añadir dependencia
    de encoding antes del dashboard no aporta nada.
13. [ ] **Reproducción**: `--play` en CLI (mplayer); en API, binario o URL.
    → **Agente:** en CLI sí. En API, entrega por **URL temporal**
    (`GET /audio/{id}` con TTL) en vez de binario embebido — ver
    `docs/ADDITIONS.md` §4. El streaming range-request es mejora
    posterior; el dashboard funciona con la URL sola.

## API REST (Fase 3)

14. [x] **Framework**: FastAPI + uvicorn.
    → **Agente:** confirmado. OpenAPI gratis alimenta directamente el
    dashboard (Fase 4) y el contrato ya está esbozado en `OPENAPI.md`.
15. [x] **Puerto**: 8100, con **bind default `127.0.0.1`**.
    → **Agente:** el puerto está bien. El matiz importante es el bind:
    8774 ya expone `0.0.0.0` sin auth (comportamiento original de la APK,
    no lo heredamos por defecto). Default loopback, flag `--bind` para
    exponer — ver `docs/ADDITIONS.md` §5.
16. [x] **Entrega de audio + LRC**: URL temporal + dos endpoints.
    → **Agente:** JSON con `audio_url` (`GET /audio/{id}`, TTL ~1 h) +
    LRC en la misma respuesta o endpoint propio. Base64 embebido
    descartado: un WAV de 10 min son ~28 MB → 37 MB de JSON. Ver
    `docs/ADDITIONS.md` §4.
17. [ ] **Auth**: sin auth en loopback; token simple (`Bearer`) si se expone.
    → **Agente:** en `127.0.0.1` el token es fricción sin beneficio. Si se
    expone a la LAN (flag), exigir token. Es un `if` en un middleware, no
    un subsistema.

## Empaquetado

18. [x] **Nombre del paquete**: `mtts`.
    → **Agente:** corto, sin colisiones, ya es el nombre de los entry
    points propuestos en el roadmap. `multitts-cli` es redundante.
19. [x] **Python mínimo**: `>=3.10`.
    → **Agente:** ver `docs/ADDITIONS.md` §6. Nada del código actual
    necesita más; maximiza compatibilidad Termux/otros Androids.
20. [ ] **Wrappers `bin/mel` y `bin/mtts`**: mantener como shims delgados
        con aviso de deprecación; remover cuando llegue el dashboard.
    → **Agente:** romperlos de golpe no aporta (nadie gana con el error),
    mantenerlos para siempre es deuda. Shim de 3 líneas sobre el nuevo
    `mtts` + warning, y fecha de remoción (p. ej. la versión de Fase 4).

## Roadmap / prioridades

21. [x] **Fase 1 antes que Fase 2**: confirmado.
    → **Agente:** construir el engine sobre `api.py` plano para luego
    migrarlo es pagar dos veces. El refactor primero deja tests de
    regresión que protegen el engine después.
22. [x] **Dashboard (Fase 4)**: "más adelante", pero diseñando Fase 2/3
        pensando en él.
    → **Agente:** el orden es correcto (CLI primero: es el usuario más
    barato de satisfacer y el que valida la sintaxis). Pero dos añadidos
    de `docs/ADDITIONS.md` se deciden *ahora* porque después son
    retrabajo: progreso n/N + ETA (§3) y entrega por URL (§4).

---

## Resumen

- **Resueltas:** las 22 decisiones (2026-08-20).
- **Ajustes confirmados por el humano:** puerto `8100`, flag `--bind` (no `--host`),
  flag `--backend` (no `--api`), `default_voice` multilocale (string | map | fallback).
