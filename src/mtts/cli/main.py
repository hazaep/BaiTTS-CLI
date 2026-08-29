"""Entry point de la CLI `mtts`."""

import sys

from ..process import handle_list_voices, process_file, process_directory
from .args import parse_and_validate_args


def main(argv=None):
    """
    Función principal de entrada del programa.
    :param argv: Lista de argumentos (None = usar sys.argv[1:])
    :return: Código de salida entero
    """
    args_list = list(sys.argv[1:]) if argv is None else list(argv)

    if not args_list:
        print("Error: No se especificó ninguna operación (usa -h para obtener ayuda)")
        return 1

    try:
        args = parse_and_validate_args(args_list)

        if args.list:
            handle_list_voices(args.backend)
        elif args.file:
            process_file(
                api_url=args.backend,
                file_path=args.file,
                output_dir=args.out,
                voice_params={
                    'voice': args.voice,
                    'volume': args.volume,
                    'speed': args.speed,
                    'pitch': args.pitch
                },
                lrc_max_len=args.sub,
                blacklist_source=args.blacklist
            )
        elif args.dir:
            process_directory(
                api_url=args.backend,
                input_dir=args.dir,
                output_dir=args.out,
                voice_params={
                    'voice': args.voice,
                    'volume': args.volume,
                    'speed': args.speed,
                    'pitch': args.pitch
                },
                lrc_max_len=args.sub,
                blacklist_source=args.blacklist
            )
        else:
            print("Error: No se especificó ninguna operación (usa -h para obtener ayuda)")
            return 1

    except (ValueError, FileNotFoundError, ConnectionError) as e:
        print(f"Error en la ejecución del programa: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ocurrió un error desconocido: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
