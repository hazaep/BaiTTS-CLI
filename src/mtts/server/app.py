"""Placeholder de la API REST (Fase 3).

El entry point `mtts-server` existe para que el paquete sea estable desde la
Fase 1, pero la implementación real llega en la Fase 3 (ver docs/ROADMAP.md).
"""

import sys


def main(argv=None):
    print(
        "mtts-server aún no está implementado (Fase 3 del roadmap).\n"
        "Por ahora solo está disponible la CLI `mtts`.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
