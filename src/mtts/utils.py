"""Utilidades varias: codificación, lista negra y división de texto para LRC."""

import locale
import os
import re
import string

import requests


def convert_file_to_utf8(file_path):
    """
    Intentar leer el archivo con codificaciones comunes, luego guardar sobrescribiendo con codificación UTF-8.
    :param file_path: Ruta del archivo
    :return: True si la conversión fue exitosa, False si falló
    """
    encodings_to_try = [locale.getpreferredencoding(False), 'gbk', 'big5', 'utf16']

    content = None
    original_encoding = None

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            original_encoding = encoding
            print(f"Lectura exitosa del archivo con codificación '{encoding}': {os.path.basename(file_path)}")
            break
        except (UnicodeDecodeError, TypeError):
            continue

    if content is None:
        print(f"Error: No se pudo decodificar el archivo {os.path.basename(file_path)} con ninguna de las codificaciones alternativas ({', '.join(encodings_to_try)}).")
        return False

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"El archivo ha sido convertido exitosamente de '{original_encoding}' a UTF-8.")
        return True
    except Exception as e:
        print(f"Error: Fallo al escribir el archivo UTF-8: {e}")
        return False


def load_blacklist_patterns(source):
    """
    Cargar reglas de lista negra desde archivo, URL o cadena
    :param source: Origen (None, ruta de archivo, URL, o cadena con '|')
    :return: Lista de patrones de expresiones regulares
    """
    if not source:
        return []

    patterns = []
    try:
        if source.startswith(('http://', 'https://')):
            print(f"Cargando lista negra desde URL: {source}")
            response = requests.get(source)
            response.raise_for_status()
            lines = response.text.splitlines()
            patterns = [line.strip() for line in lines if line.strip()]
        elif os.path.exists(source):
            print(f"Cargando lista negra desde archivo local: {source}")
            with open(source, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                patterns = [line.strip() for line in lines if line.strip()]
        else:
            print("Tratando el parámetro de lista negra como expresión regular directa")
            # Asumir que es una cadena de expresión regular directa
            patterns = [source]
    except UnicodeDecodeError:
        print(f"Advertencia: El archivo de lista negra {source} no está en codificación UTF-8, por favor conviértelo y reintenta. No se usará la lista negra.")
        return []
    except Exception as e:
        print(f"Advertencia: Fallo al cargar la lista negra: {e}. No se usará la lista negra.")
        return []

    print(f"Se cargaron exitosamente {len(patterns)} reglas de lista negra.")
    return patterns


def apply_blacklist(text, patterns):
    """
    Envolver las partes del texto que coincidan con patrones de la lista negra con `[[...]]`
    :param text: Texto original
    :param patterns: Lista de patrones de expresiones regulares
    :return: Texto procesado
    """
    if not patterns:
        return text

    combined_pattern = "|".join(patterns)

    try:
        return re.sub(f"({combined_pattern})", r"[[\1]]", text)
    except re.error as e:
        print(f"Advertencia: Error en la expresión regular de la lista negra: {e}. Esta regla será ignorada.")
        processed_text = text
        for pattern in patterns:
            try:
                processed_text = re.sub(f"({pattern})", r"[[\1]]", processed_text)
            except re.error:
                continue
        return processed_text


def split_text_for_lrc(text, max_len):
    """
    Dividir texto largo en frases cortas para generar LRC, manteniendo la integridad de las etiquetas [[...]].
    Cada línea tendrá como máximo max_len caracteres que no sean signos de puntuación.
    """
    punctuation = string.punctuation + "，。！？；：、…—·《》""''"

    # Divide el texto capturando las etiquetas como separadores; texto normal y
    # etiquetas quedan alternados en la lista.
    segments = re.split(r'(\[\[.*?\]\])', text)
    segments = [s for s in segments if s]

    final_chunks = []
    current_chunk = ""
    char_count = 0

    for segment in segments:
        # Etiqueta: agregarla directamente, no cuenta para el conteo de caracteres
        if segment.startswith('[[') and segment.endswith(']]'):
            current_chunk += segment
            continue

        # Texto normal: procesar carácter por carácter
        for char in segment:
            current_chunk += char
            if char not in punctuation and not char.isspace():
                char_count += 1

            if char_count >= max_len:
                final_chunks.append(current_chunk.strip())
                current_chunk = ""
                char_count = 0

    if current_chunk.strip():
        final_chunks.append(current_chunk.strip())

    return final_chunks if final_chunks else [text]
