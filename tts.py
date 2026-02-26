import os
import wave
import tempfile
import shutil
import time
import io
from api import text_to_speech
from lrc import generate_lrc_content
from utils import split_text_for_lrc

def convert_text_to_audio_file(api_url, lines, voice_params, output_wav_path, output_lrc_path=None, lrc_max_len=None):
    """
    Convertir una lista de líneas de texto en un único archivo WAV, y opcionalmente generar un archivo LRC.
    - Si no se genera LRC, se llama a la API una vez por línea de texto para sintetizar audio.
    - Si se genera LRC, también se llama a la API una vez por línea para sintetizar audio, luego se asignan timestamps a las frases cortas divididas según la duración total del audio.
    """
    temp_dir = tempfile.mkdtemp(prefix="tts_cli_")
    print(f"Directorio temporal de caché creado: {temp_dir}")
    
    main_audio_paths = []
    
    try:
        if not output_lrc_path:
            # --- Rama de lógica 1: No generar LRC ---
            print("Modo: Solo sintetizar audio")
            for i, line in enumerate(lines):
                audio_data = text_to_speech(api_url, line, voice_params)
                chunk_path = os.path.join(temp_dir, f"main_audio_{i}.wav")
                with open(chunk_path, 'wb') as f:
                    f.write(audio_data)
                main_audio_paths.append(chunk_path)
        else:
            # --- Rama de lógica 2: Generar LRC ---
            print(f"Modo: Sintetizar audio y generar subtítulos LRC (máximo {lrc_max_len} caracteres por frase)")
            lrc_timestamps = []
            lrc_texts = []
            total_duration_ms = 0

            for i, line in enumerate(lines):
                # Paso 1: Sintetizar el audio completo de la línea única, para el archivo WAV final y cálculo de duración
                print(f"Sintetizando audio principal (línea {i+1}/{len(lines)})...")
                main_audio_data = text_to_speech(api_url, line, voice_params)
                main_chunk_path = os.path.join(temp_dir, f"main_audio_{i}.wav")
                with open(main_chunk_path, 'wb') as f:
                    f.write(main_audio_data)
                main_audio_paths.append(main_chunk_path)

                # Paso 2: Calcular la duración total de esta línea de audio completa
                line_duration_ms = 0
                try:
                    with wave.open(io.BytesIO(main_audio_data), 'rb') as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        line_duration_ms = int((frames / float(rate)) * 1000)
                except wave.Error:
                    print(f"Advertencia: No se pudo leer la duración de la línea de audio principal '{line[:20]}...', la línea de tiempo LRC para esta línea podría ser inexacta.")

                # Paso 3: Dividir el texto de esta línea en frases cortas para LRC
                lrc_chunks = split_text_for_lrc(line, lrc_max_len)
                
                print(f"Asignando timestamps a {len(lrc_chunks)} frases LRC para la línea {i+1}...")
                
                # Paso 4: Dividir la duración total equitativamente entre cada frase corta
                if lrc_chunks:
                    # Prevenir error de división por cero
                    duration_per_chunk = line_duration_ms / len(lrc_chunks) if len(lrc_chunks) > 0 else 0
                    for chunk_index, lrc_chunk in enumerate(lrc_chunks):
                        # Calcular el tiempo de inicio de la frase corta actual
                        chunk_start_time = total_duration_ms + int(chunk_index * duration_per_chunk)
                        
                        # Registrar datos para LRC
                        lrc_timestamps.append(chunk_start_time)
                        lrc_texts.append(lrc_chunk.strip())
                
                # Acumular duración total, preparándose para la siguiente línea
                total_duration_ms += line_duration_ms

            # Paso 5: Generar contenido del archivo LRC
            lrc_content = generate_lrc_content(lrc_timestamps, lrc_texts)
            with open(output_lrc_path, 'w', encoding='utf-8') as f:
                f.write(lrc_content)
            print(f"Archivo de letras LRC guardado: {output_lrc_path}")

        # --- Lógica común: Combinar archivos de audio principales ---
        if not main_audio_paths:
             print("Advertencia: No se generaron datos de audio, omitiendo síntesis de archivo.")
             return

        print(f"Combinando {len(main_audio_paths)} bloques de audio principales en {os.path.basename(output_wav_path)}...")
        combine_wav_files(main_audio_paths, output_wav_path)
        print(f"Archivo de audio guardado: {output_wav_path}")

    finally:
        print(f"Limpiando directorio temporal de caché: {temp_dir}")
        shutil.rmtree(temp_dir)


def combine_wav_files(input_files, output_file):
    """
    Combinar múltiples archivos WAV en uno solo.
    """
    if not input_files:
        return
        
    outfile = None
    try:
        # Usar el primer archivo WAV válido como plantilla de parámetros para el archivo de salida
        params = None
        for file_path in input_files:
            try:
                with wave.open(file_path, 'rb') as infile:
                    params = infile.getparams()
                    break
            except (wave.Error, EOFError):
                print(f"Advertencia: Fallo al leer parámetros del bloque de audio {os.path.basename(file_path)}, se omitió.")
                continue # Si el archivo está dañado, intentar con el siguiente
        
        if params is None:
            raise RuntimeError("Todos los bloques de audio son inválidos, no se puede combinar.")

        with wave.open(output_file, 'wb') as outfile:
            outfile.setparams(params)
            for file_path in input_files:
                try:
                    with wave.open(file_path, 'rb') as infile:
                        outfile.writeframes(infile.readframes(infile.getnframes()))
                except (wave.Error, EOFError):
                     print(f"Advertencia: Fallo al leer datos del bloque de audio {os.path.basename(file_path)}, se omitió.")
    except Exception as e:
        raise RuntimeError(f"Fallo al combinar archivos WAV: {e}")
