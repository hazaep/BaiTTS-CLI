import requests
import time
from urllib.parse import urljoin, urlencode

MAX_RETRIES = 3
RETRY_DELAY = 2  # segundos

def get_request_with_retry(url, params=None):
    """
    Realiza una solicitud GET con lógica de reintentos
    :param url: URL completa de la solicitud
    :param params: Parámetros de consulta para la URL
    :return: Objeto Response en caso de éxito
    :raises: ConnectionError si falla después de 3 intentos
    """
    last_error_message = ""
    
    # --- Optimización 2 START ---
    # Para mostrar claramente la URL completa de la solicitud en los logs
    full_url = url
    if params:
        full_url += "?" + urlencode(params)
    # --- Optimización 2 END ---

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()  # Lanza HTTPError si el código de estado es 4xx o 5xx
            return response
        # --- Optimización 2 START ---
        # Capturar errores HTTP específicos para obtener el código de estado
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            request_url = e.response.url
            last_error_message = f"La API devolvió un código de estado de error {status_code} (URL: {request_url})"
            print(f"Advertencia: Solicitud fallida (intento {attempt + 1}/{MAX_RETRIES}): {last_error_message}")
        # Capturar otros errores relacionados con solicitudes (timeout, problemas de DNS, etc.)
        except requests.exceptions.RequestException as e:
            last_error_message = f"Error de red al realizar la solicitud: {e}"
            print(f"Advertencia: Solicitud fallida (intento {attempt + 1}/{MAX_RETRIES}): {last_error_message}")
        # --- Optimización 2 END ---
            
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
        else:
            # --- Optimización 2 START ---
            # Incluir información de error más detallada en el mensaje final de excepción
            raise ConnectionError(f"La solicitud a la API falló completamente después de {MAX_RETRIES} intentos. Último error: {last_error_message}")
            # --- Optimización 2 END ---

def get_voices(api_url):
    """
    Obtener la lista de voces disponibles
    :param api_url: URL base de la API
    :return: Datos JSON con la lista de voces
    """
    voices_url = urljoin(api_url, "/voices")
    print(f"Obteniendo lista de voces desde {voices_url}...")
    response = get_request_with_retry(voices_url)
    return response.json()


def text_to_speech(api_url, text, voice_params):
    """
    Llamar al endpoint de texto a voz
    :param api_url: URL base de la API
    :param text: Texto a convertir
    :param voice_params: Parámetros relacionados con la voz (voice, volume, speed, pitch)
    :return: Datos binarios del audio en formato WAV
    """
    forward_url = urljoin(api_url, "/forward")
    
    # Filtrar parámetros con valor None
    params = {k: v for k, v in voice_params.items() if v is not None}
    params['text'] = text

    # Para mayor claridad en los logs, mostrar solo una parte del texto
    log_text = (text[:30] + '...') if len(text) > 30 else text
    print(f"Sintetizando texto: \"{log_text.strip()}\"")
    
    response = get_request_with_retry(forward_url, params=params)
    return response.content
