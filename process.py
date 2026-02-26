import os
import glob
import sys
from api import get_voices, text_to_speech
from tts import convert_text_to_audio_file
from utils import load_blacklist_patterns, apply_blacklist, convert_file_to_utf8

def handle_list_voices(api_url):
    """
    Manejar la rama --list, obtener y mostrar la lista de voces con formato
    """
    try:
        data = get_voices(api_url)
        if not data.get("success") or 'data' not in data or 'catalog' not in data['data']:
            raise ValueError("El formato de la lista de voces devuelta por la API es incorrecto")

        all_voices = []
        for key in data['data']['catalog']:
            all_voices.extend(data['data']['catalog'][key])
        
        if not all_voices:
            print("No se encontraron voces disponibles.")
            return

        print("\nLista de voces disponibles:")
        separator = "=" * 50
        for voice in all_voices:
            print(separator)
            print(f"ID: {voice.get('id', 'N/A')},")
            print(f"Nombre: {voice.get('name', 'N/A')},")
            print(f"Género: {voice.get('gender', 'N/A')},")
            print(f"Idioma: {voice.get('locale', 'N/A')},")
            print(f"Tipo: {voice.get('type', 'N/A')}")
        print(separator)

    except Exception as e:
        raise RuntimeError(f"Fallo al obtener la lista de voces: {e}")


def process_file(api_url, file_path, output_dir, voice_params, lrc_max_len, blacklist_source):
    """
    Procesar un único archivo de texto
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo de entrada no existe: {file_path}")

    print(f"\n--- Comenzando procesamiento del archivo: {os.path.basename(file_path)} ---")
    
    os.makedirs(output_dir, exist_ok=True)
    
    lines = []
    # --- Nuevo: Lógica de lectura de archivo con reintentos y conversión ---
    while True:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            break # Lectura exitosa, salir del bucle
        except UnicodeDecodeError:
            print(f"\nAdvertencia: El archivo '{os.path.basename(file_path)}' no está codificado en UTF-8.")
            prompt = "¿Intentar convertirlo a codificación UTF-8 y reintentar? (esto sobrescribirá el archivo original) [y/n]: "
            user_choice = input(prompt).lower()
            
            if user_choice in ['y', 'yes']:
                print("Intentando convertir...")
                if convert_file_to_utf8(file_path):
                    print("Conversión exitosa, reintentando lectura...")
                    continue # Volver al inicio del bucle para intentar leer nuevamente
                else:
                    raise ValueError(f"Fallo en la conversión del archivo {os.path.basename(file_path)}, tarea terminada.")
            else:
                raise ValueError(f"Operación cancelada por el usuario, archivo {os.path.basename(file_path)} no procesado.")
        
    # Cargar lista negra
    blacklist_patterns = load_blacklist_patterns(blacklist_source)

    # Preprocesar líneas de texto
    processed_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line: # Ignorar líneas vacías
            blacklisted_line = apply_blacklist(stripped_line, blacklist_patterns)
            processed_lines.append(blacklisted_line)
    
    if not processed_lines:
        print(f"El archivo {os.path.basename(file_path)} está vacío o solo contiene líneas en blanco, se omitió.")
        return
        
    # Agregar marcador de silencio a la última línea del documento
    processed_lines[-1] = processed_lines[-1] + "[[PAUSE:1000]]"
    
    # Configurar nombre de archivo de salida
    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_wav_path = os.path.join(output_dir, f"{base_filename}.wav")
    output_lrc_path = os.path.join(output_dir, f"{base_filename}.lrc") if lrc_max_len is not None else None

    # Llamar a la función principal de conversión TTS
    convert_text_to_audio_file(
        api_url=api_url,
        lines=processed_lines,
        voice_params=voice_params,
        output_wav_path=output_wav_path,
        output_lrc_path=output_lrc_path,
        lrc_max_len=lrc_max_len
    )
    print(f"--- Procesamiento del archivo completado: {os.path.basename(file_path)} ---")


def process_directory(api_url, input_dir, output_dir, voice_params, lrc_max_len, blacklist_source):
    """
    Procesar todos los archivos .txt en un directorio especificado
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"El directorio de entrada no existe: {input_dir}")

    txt_files = sorted(glob.glob(os.path.join(input_dir, '*.txt')))
    
    if not txt_files:
        print(f"No se encontraron archivos .txt en el directorio {input_dir}.")
        return
    
    # --- Nuevo: Verificación previa de codificación para procesamiento por lotes ---
    print("Realizando verificación previa de codificación de archivos...")
    files_to_convert = []
    for file_path in txt_files:
        try:
            # Solo intentar abrir, no leer contenido, para verificar codificación rápidamente
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1) 
        except UnicodeDecodeError:
            files_to_convert.append(file_path)
    
    if files_to_convert:
        print("\nAdvertencia: Se detectó que los siguientes archivos no están en codificación UTF-8:")
        for f in files_to_convert:
            print(f" - {os.path.basename(f)}")
        
        prompt = "\n¿Intentar convertir todos los archivos anteriores a codificación UTF-8 para continuar? (esto sobrescribirá los archivos originales) [y/n]: "
        user_choice = input(prompt).lower()
        
        if user_choice in ['y', 'yes']:
            print("Convirtiendo archivos por lotes...")
            success_count = 0
            for file_path in files_to_convert:
                if convert_file_to_utf8(file_path):
                    success_count += 1
            if success_count != len(files_to_convert):
                raise ValueError("Fallo en la conversión de algunos archivos, tarea terminada. Por favor revisa los logs anteriores.")
            print("Conversión de todos los archivos completada, continuando con la tarea.")
        else:
            raise ValueError("Operación cancelada por el usuario, tarea por lotes no ejecutada.")

    # --- Finalizada la verificación previa, comenzar procesamiento formal ---
    print(f"\nProcesando {len(txt_files)} archivos en el directorio '{input_dir}'...")

    for file_path in txt_files:
        try:
            process_file(api_url, file_path, output_dir, voice_params, lrc_max_len, blacklist_source)
        except Exception as e:
            print(f"Error al procesar el archivo {os.path.basename(file_path)}: {e}", file=sys.stderr)
            # Elegir continuar procesando el siguiente archivo
            continue
            
    print("\nTodos los archivos han sido procesados.")
