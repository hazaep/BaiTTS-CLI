# -*- coding: utf-8 -*-
"""
Catálogo de voces del servidor MultiTTS (puerto 8774).

Generado desde /voices y filtrado a voces en español (locale que empieza
por "es" o "spa"). Incluye metadatos útiles para asignar voces a personajes
de un diálogo (género, motor, tipo online/offline).

Estructura por motor:
    motor -> list[dict(id, name, gender, locale, type, desc)]
"""

VOICES_ES = {
    "microsoft": [
        {"id": "microsoft_es-ES-Helena-Apollo", "name": "Helena", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "es-ES,Helena @MiAndroidAccesible"},
        {"id": "microsoft_es-ES-Laura-Apollo", "name": "Laura", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "es-ES,Laura @MiAndroidAccesible"},
        {"id": "microsoft_es-ES-Pablo-Apollo", "name": "Pablo", "gender": "male", "locale": "es-ES", "type": "offline", "desc": "es-ES,Pablo @MiAndroidAccesible"},
        {"id": "microsoft_es-MX-Raul-Apollo", "name": "Raúl", "gender": "male", "locale": "es-MX", "type": "offline", "desc": "es-MX,Raul @MiAndroidAccesible"},
        {"id": "microsoft_es-MX-Sabina-Apollo", "name": "Sabina", "gender": "female", "locale": "es-MX", "type": "offline", "desc": "es-MX,Sabina @MiAndroidAccesible"},
        {"id": "microsoft_es-MX-JorgeNeural-MiAndroidAccesible", "name": "Jorge", "gender": "male", "locale": "es-MX", "type": "offline", "desc": "es-MX,Jorge @MiAndroidAccesible"},
        {"id": "microsoft_es-ES-ElviraNeural-MiAndroidAccesible", "name": "Elvira", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "es-ES,Elvira @MiAndroidAccesible"},
        {"id": "microsoft_es-ES-AlvaroNeural-MiAndroidAccesible", "name": "Alvaro", "gender": "male", "locale": "es-ES", "type": "offline", "desc": "es-ES,Alvaro @MiAndroidAccesible"},
        {"id": "microsoft_es-MX-DaliaNeural-MiAndroidAccesible", "name": "Dalia", "gender": "female", "locale": "es-MX", "type": "offline", "desc": "es-MX, Dalia @MiAndroidAccesible"},
    ],
    "vocalizer": [
        {"id": "vocalizer_spa-col-ximena-high-MiAndroidAccesible", "name": "Ximena", "gender": "female", "locale": "es-CO", "type": "offline", "desc": "es-CO, Ximena high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-col-soledad-high-MiAndroidAccesible", "name": "Soledad", "gender": "female", "locale": "es-CO", "type": "offline", "desc": "es-CO, Soledad high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-mex-paulina-high-MiAndroidAccesible", "name": "Paulina", "gender": "female", "locale": "es-MX", "type": "offline", "desc": "es-MX, Paulina high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-esp-monica-high-MiAndroidAccesible", "name": "Mónica", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "es-ES, Mónica high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-esp-marisol-high-MiAndroidAccesible", "name": "Marisol", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "es-ES, Marisol high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-mex-juan-high-MiAndroidAccesible", "name": "Juan", "gender": "male", "locale": "es-MX", "type": "offline", "desc": "es-MX, Juan high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-esp-jorge-high-MiAndroidAccesible", "name": "Jorge", "gender": "male", "locale": "es-ES", "type": "offline", "desc": "es-ES, Jorge high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-arg-isabela-high-MiAndroidAccesible", "name": "Isabela", "gender": "female", "locale": "es-AR", "type": "offline", "desc": "es-AR, Isabela high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-chl-francisca-high-MiAndroidAccesible", "name": "Francisca", "gender": "female", "locale": "es-CL", "type": "offline", "desc": "es-CL, Francisca high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-arg-diego-high-MiAndroidAccesible", "name": "Diego", "gender": "male", "locale": "es-AR", "type": "offline", "desc": "es-AR, Diego high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-col-carlos-high-MiAndroidAccesible", "name": "Carlos", "gender": "male", "locale": "es-CO", "type": "offline", "desc": "es-CO, Carlos high @MiAndroidAccesible"},
        {"id": "vocalizer_spa-mex-angelica-high-MiAndroidAccesible", "name": "Angélica", "gender": "female", "locale": "es-MX", "type": "offline", "desc": "es-MX, Angélica high @MiAndroidAccesible"},
    ],
    "acapela": [
        {"id": "acapela_spa-ESP-Antonio-MiAndroidAccesible", "name": "Antonio", "gender": "male", "locale": "spa-ESP", "type": "offline", "desc": "spa-ESP-Antonio @MiAndroidAccesible"},
        {"id": "acapela_spa-MEX-Emilio-MiAndroidAccesible", "name": "Emilio", "gender": "male", "locale": "es-MX", "type": "offline", "desc": "spa-MEX-Emilio @MiAndroidAccesible"},
        {"id": "acapela_spa-ESP-Inés-MiAndroidAccesible", "name": "Inés", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "spa-ESP-Inés @MiAndroidAccesible"},
        {"id": "acapela_spa-ESP-María-MiAndroidAccesible", "name": "María", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "spa-ESP-María @MiAndroidAccesible"},
        {"id": "acapela_spa-MEX-Rodrigo-MiAndroidAccesible", "name": "Rodrigo", "gender": "male", "locale": "es-MX", "type": "offline", "desc": "spa-MEX-Rodrigo @MiAndroidAccesible"},
        {"id": "acapela_spa-MEX-Rosa-MiAndroidAccesible", "name": "Rosa", "gender": "female", "locale": "es-MX", "type": "offline", "desc": "spa-MEX-Rosa @MiAndroidAccesible"},
        {"id": "acapela_spa-MEX-Valeria-MiAndroidAccesible", "name": "Valeria", "gender": "female", "locale": "es-MX", "type": "offline", "desc": "spa-MEX-Valeria @MiAndroidAccesible"},
    ],
    "cereproc": [
        {"id": "cereproc_Ana", "name": "Ana", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "Ana @MiAndroidAccesible"},
        {"id": "cereproc_Sara", "name": "Sara", "gender": "female", "locale": "es-ES", "type": "offline", "desc": "Sara @MiAndroidAccesible"},
    ],
    "samsung": [
        {"id": "samsung_es_es_g01", "name": "1", "gender": "male", "locale": "es-ES", "type": "offline"},
        {"id": "samsung_es_es_l01", "name": "2", "gender": "female", "locale": "es-ES", "type": "offline"},
        {"id": "samsung_es_mx_f00", "name": "3", "gender": "female", "locale": "es-MX", "type": "offline"},
        {"id": "samsung_es_mx_g01", "name": "4", "gender": "male", "locale": "es-MX", "type": "offline"},
        {"id": "samsung_es_mx_l01", "name": "5", "gender": "female", "locale": "es-MX", "type": "offline"},
        {"id": "samsung_es_mx_m00", "name": "6", "gender": "male", "locale": "es-MX", "type": "offline"},
        {"id": "samsung_es_us_f00", "name": "7", "gender": "female", "locale": "es-US", "type": "offline"},
        {"id": "samsung_es_us_g01", "name": "8", "gender": "male", "locale": "es-US", "type": "offline"},
        {"id": "samsung_es_us_l01", "name": "9", "gender": "female", "locale": "es-US", "type": "offline"},
    ],
    "google": [
        {"id": "google_es-es-x-ana", "name": "1", "gender": "female", "locale": "es-ES", "type": "offline"},
        {"id": "google_es-es-x-eea", "name": "2", "gender": "female", "locale": "es-ES", "type": "offline"},
        {"id": "google_es-es-x-eeb", "name": "3", "gender": "male", "locale": "es-ES", "type": "offline"},
        {"id": "google_es-es-x-eec", "name": "4", "gender": "female", "locale": "es-ES", "type": "offline"},
        {"id": "google_es-es-x-eed", "name": "5", "gender": "male", "locale": "es-ES", "type": "offline"},
        {"id": "google_es-es-x-eee", "name": "6", "gender": "female", "locale": "es-ES", "type": "offline"},
        {"id": "google_es-es-x-eef", "name": "7", "gender": "male", "locale": "es-ES", "type": "offline"},
        {"id": "google_es-es-x-nhg", "name": "8", "gender": "female", "locale": "es-ES", "type": "offline"},
    ],
}

# Índice plano: id -> dict(..., motor=...)
VOICES_FLAT = {
    v["id"]: {**v, "motor": motor}
    for motor, voices in VOICES_ES.items()
    for v in voices
}


def voices_by_gender(gender=None):
    """Devuelve lista de voces filtrada por género ('male'/'female'/None)."""
    out = []
    for vid, meta in VOICES_FLAT.items():
        if gender is None or meta["gender"] == gender:
            out.append((vid, meta))
    return out


def get_voice(voice_id):
    """Devuelve el dict de una voz por su id, o None."""
    return VOICES_FLAT.get(voice_id)
