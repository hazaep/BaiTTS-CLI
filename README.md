# BaiTTS-CLI

Una herramienta de línea de comandos basada en la API de **MultiTTS** para consumirla y convertir documentos de texto (`.txt`) en audiolibros (`.wav`), con la opción de generar archivos de letra sincronizados en formato LRC.

## Características

- ✅ Conversión de un archivo de texto a voz
- ✅ Procesamiento por lotes de carpetas con archivos de texto
- ✅ Generación de archivos LRC (con número máximo de caracteres por línea personalizable)
- ✅ Ajuste de parámetros de voz (volumen, velocidad, tono)
- ✅ Lista negra para filtrar contenido específico
- ✅ Consulta de la lista de voces disponibles en la API

## Requisitos de instalación

- Python 3.12.11
- Dependencias: `requests 2.32.4`

## Uso

### Sintaxis básica

```bash
python main.py --api <URL_API> [opciones]
```

### Parámetros

**Parámetro obligatorio:**
- `--api` — URL de la API a utilizar

**Modo de operación (elige uno):**
- `-l, --list` — Muestra la lista de voces disponibles
- `-f, --file` — Especifica un archivo de texto a convertir
- `-d, --dir` — Especifica una carpeta para procesamiento por lotes

**Opciones de salida:**
- `-o, --out` — Carpeta de salida (por defecto: directorio actual)

**Parámetros de voz:**
- `--voice` — ID de la voz a utilizar (usa `-l` para ver las disponibles)
- `--volume` — Volumen (0–100)
- `--speed` — Velocidad (0–100)
- `--pitch` — Tono (0–100)

**Generación de letras:**
- `-s, --sub` — Genera un archivo LRC para el archivo procesado
  - `-s` sin argumento: máximo 15 caracteres por línea (valor por defecto)
  - `-s <número>`: número máximo de caracteres por línea (10–100)

**Filtrado de contenido:**
- `-b, --blacklist` — Palabras o expresiones a excluir del procesamiento. Acepta expresiones regulares, puede ser una cadena de texto, archivo o URL. Separa múltiples valores con `|`. Si es un archivo, cada línea se trata como un valor independiente.

## Ejemplos

**1. Consultar las voces disponibles:**
```bash
python main.py --api http://127.0.0.1:8774 -l
```

**2. Convertir un archivo:**
```bash
python main.py --api http://127.0.0.1:8774 -f ./input.txt --voice voice1 -o ./output
```

**3. Procesar una carpeta y generar letras:**
```bash
python main.py --api http://127.0.0.1:8774 -d ./texts --voice v2 -s 20 -o ./output
```

**4. Uso con parámetros avanzados:**
```bash
python main.py --api http://127.0.0.1:8774 -f story.txt \
               --voice v3 --volume 80 --speed 90 --pitch 75 \
               -b "palabra1|palabra2" -s -o audio_output
```

## Notas importantes

1. **Parámetros mutuamente excluyentes:** `--list`, `--file` y `--dir` no pueden usarse al mismo tiempo. Con `--list` solo se puede usar `--api`.

2. **Rango de valores:** `--volume`, `--speed`, `--pitch` y `--sub` requieren soporte de la API. Si no se especifican, se usan los valores por defecto. Valores fuera de rango producirán un error.

3. **Lista negra:** Admite expresiones regulares. El contenido puede cargarse desde un archivo, URL o directamente como texto.

## Ayuda

```bash
python main.py --api <URL_API> -h
```

