import re

def format_timestamp(milliseconds):
    """
    Convertir milisegundos a formato de timestamp LRC [mm:ss.xx]
    """
    total_seconds = milliseconds // 1000
    ms = (milliseconds % 1000) // 10
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"[{minutes:02}:{seconds:02}.{ms:02}]"

def generate_lrc_content(timestamps, texts):
    """
    Generar el contenido completo de un archivo LRC a partir de listas de timestamps y textos
    :param timestamps: Lista de timestamps en milisegundos (tiempo de inicio)
    :param texts: Lista de líneas de texto correspondientes
    :return: Cadena de texto con formato LRC
    """
    if len(timestamps) != len(texts):
        raise ValueError("La longitud de las listas de timestamps y textos no coincide")

    lrc_lines = []
    # Agregar algunos metadatos (opcional)
    lrc_lines.append("[ar:Generado por BaiTTS CLI]")
    lrc_lines.append("[al:Transcripción de Audio]")
    lrc_lines.append("[ti:Texto Convertido]")
    lrc_lines.append("")

    for ts, txt in zip(timestamps, texts):
        # --- Optimización 1 START ---
        # Usar expresión regular para eliminar todas las etiquetas en formato [[...]], haciendo las letras más limpias
        # Esto manejará tanto las etiquetas de lista negra como instrucciones como [[PAUSE:1000]]
        clean_text = re.sub(r'\[\[.*?\]\]', '', txt).strip()
        # --- Optimización 1 END ---

        if clean_text:
            lrc_line = f"{format_timestamp(ts)}{clean_text}"
            lrc_lines.append(lrc_line)
            
    return "\n".join(lrc_lines)
