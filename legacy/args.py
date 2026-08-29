import argparse
import sys

def parse_and_validate_args():
    """
    Analizar y validar los argumentos de línea de comandos
    """
    parser = argparse.ArgumentParser(description="Herramienta CLI de texto a voz", add_help=False)

    # Parámetro help personalizado
    parser.add_argument(
        '-h', '--help', action='help', default=argparse.SUPPRESS,
        help='Mostrar este mensaje de ayuda y salir'
    )

    # Parámetros de API y generales
    parser.add_argument('--api', type=str, required=True, help='Especificar la URL de la API a llamar (obligatorio)')

    # Parámetros de ramas de funcionalidad
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--list', action='store_true', help='Obtener y mostrar la lista de voces soportadas')
    group.add_argument('-f', '--file', type=str, help='Especificar un único archivo de texto a convertir')
    group.add_argument('-d', '--dir', type=str, help='Especificar una carpeta para procesamiento por lotes')

    # Parámetros adicionales para las ramas file y dir
    parser.add_argument('-o', '--out', type=str, default='.', help='Especificar carpeta de salida (por defecto: directorio actual)')
    parser.add_argument('--voice', type=str, help='Especificar el ID de la voz a utilizar')
    parser.add_argument('--volume', type=int, choices=range(0, 101), metavar="[0-100]", help='Especificar volumen (0-100)')
    parser.add_argument('--speed', type=int, choices=range(0, 101), metavar="[0-100]", help='Especificar velocidad de habla (0-100)')
    parser.add_argument('--pitch', type=int, choices=range(0, 101), metavar="[0-100]", help='Especificar tono (0-100)')
    
    # --- Optimización 2: Modificar parámetro --sub ---
    parser.add_argument(
        '-s', '--sub',
        nargs='?',
        type=int,
        const=15,  # Si se usa -s sin número, usar este valor por defecto
        default=None, # Si no se usa -s, el valor será None
        choices=range(10, 101),
        metavar="[10-100]",
        help='Generar archivo de subtítulos LRC para los archivos procesados. Opcionalmente proporciona el número máximo de caracteres por frase (10-100); si no se proporciona un número, el valor por defecto es 15.'
    )
    
    parser.add_argument('-b', '--blacklist', type=str, help='Especificar palabras/caracteres en lista negra que no se procesarán (soporta regex, puede ser archivo, URL o cadena)')

    args = parser.parse_args()

    # --- Validación de parámetros ---
    # Rama help: manejada por defecto por argparse, sin verificación adicional

    # Verificación para la rama list
    if args.list:
        allowed_args = ['api', 'list']
        for arg, value in vars(args).items():
            # Verificar si args.sub tiene su valor por defecto None
            if arg == 'sub' and value is None:
                continue
            if arg not in allowed_args and value is not None and value is not False and value != '.':
                 parser.error("Al usar el parámetro --list, solo se permite proporcionar el parámetro --api")

    # Verificación para las ramas file o dir
    if args.file or args.dir:
        allowed_args = ['api', 'file', 'dir', 'out', 'voice', 'volume', 'speed', 'pitch', 'sub', 'blacklist']
        for arg, value in vars(args).items():
             if arg not in allowed_args and value is not None and value is not False and value != '.':
                parser.error(f"Al usar --file o --dir, no se permite usar el parámetro --{arg}")
    
    # Verificar si se especificó alguna operación
    if not args.list and not args.file and not args.dir:
        # Si hay otros parámetros además de --api, se considera un error
        other_args_present = any(
            val is not None and val is not False
            for key, val in vars(args).items() if key not in ['api', 'out'] # 'out' tiene valor por defecto, excluirlo
        )
        if other_args_present:
             parser.error("Combinación de parámetros no válida (usa -h para obtener ayuda)")

    return args
