#!/usr/bin/env python3

import sys
from args import parse_and_validate_args
from process import handle_list_voices, process_file, process_directory

def main():
    """
    Función principal de entrada del programa
    """
    if len(sys.argv) == 1:
        print("Error: No se especificó ninguna operación (usa -h para obtener ayuda)")
        sys.exit(1)
        
    try:
        args = parse_and_validate_args()

        if args.list:
            handle_list_voices(args.api)
        elif args.file:
            process_file(
                api_url=args.api,
                file_path=args.file,
                output_dir=args.out,
                voice_params={
                    'voice': args.voice,
                    'volume': args.volume,
                    'speed': args.speed,
                    'pitch': args.pitch
                },
                lrc_max_len=args.sub, # Pasar número máximo de caracteres para LRC o None
                blacklist_source=args.blacklist
            )
        elif args.dir:
            process_directory(
                api_url=args.api,
                input_dir=args.dir,
                output_dir=args.out,
                voice_params={
                    'voice': args.voice,
                    'volume': args.volume,
                    'speed': args.speed,
                    'pitch': args.pitch
                },
                lrc_max_len=args.sub, # Pasar número máximo de caracteres para LRC o None
                blacklist_source=args.blacklist
            )
        # Si no coincide con ninguna rama (manejado por argparse, esto es como respaldo)
        else:
             print("Error: No se especificó ninguna operación (usa -h para obtener ayuda)")


    except (ValueError, FileNotFoundError, ConnectionError) as e:
        print(f"Error en la ejecución del programa: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ocurrió un error desconocido: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
