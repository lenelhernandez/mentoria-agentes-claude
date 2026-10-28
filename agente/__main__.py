"""Uso: python -m agente "objetivo" [--workspace RUTA] [--auto]"""

import argparse
from pathlib import Path

from .bucle import ejecutar_agente


def aprobar_en_terminal(ruta: str, contenido: str) -> bool:
    print(f"\n--- El agente quiere escribir {ruta} ---")
    print(contenido if len(contenido) < 2000 else contenido[:2000] + "\n[...]")
    return input("¿Aprobar? [s/N] ").strip().lower() in {"s", "si", "sí", "y", "yes"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini agente de desarrollo con Claude")
    parser.add_argument("objetivo", help='Qué quieres que haga, p. ej. "Haz que pasen los tests"')
    parser.add_argument("--workspace", type=Path, default=Path("workspace"))
    parser.add_argument("--auto", action="store_true", help="Aprueba escrituras sin preguntar")
    parser.add_argument("--max-turnos", type=int, default=20)
    args = parser.parse_args()

    aprobar = (lambda ruta, contenido: True) if args.auto else aprobar_en_terminal
    resultado = ejecutar_agente(args.objetivo, args.workspace, aprobar=aprobar, max_turnos=args.max_turnos)
    print("\n=== Resultado ===\n" + resultado)


if __name__ == "__main__":
    main()
