"""Herramientas del agente.

Cada herramienta tiene dos partes:
  1. Un *esquema* (JSON Schema) que Claude lee para saber qué puede pedir.
  2. Una *función* Python que ejecutamos nosotros cuando Claude la pide.

Claude nunca ejecuta nada por sí mismo: solo devuelve un bloque `tool_use`
diciendo "quiero llamar a X con estos argumentos". Nuestro código decide
si lo ejecuta, cómo, y qué resultado le devuelve.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable


class ErrorHerramienta(Exception):
    """Error que se devuelve a Claude como `tool_result` con `is_error: true`."""


# ---------------------------------------------------------------------------
# Esquemas: lo que Claude ve. La descripción es parte del prompt, escríbela
# pensando en cuándo usarla y qué devuelve, no solo en qué hace.
# ---------------------------------------------------------------------------

ESQUEMAS = [
    {
        "name": "listar_archivos",
        "description": (
            "Lista archivos y carpetas dentro del workspace. Úsala primero para "
            "orientarte. Devuelve una ruta por línea; las carpetas terminan en '/'."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "ruta": {
                    "type": "string",
                    "description": "Carpeta relativa al workspace. Usa '.' para la raíz.",
                }
            },
            "required": ["ruta"],
            "additionalProperties": False,
        },
    },
    {
        "name": "leer_archivo",
        "description": "Lee un archivo de texto del workspace y devuelve su contenido completo.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Ruta relativa al workspace."}
            },
            "required": ["ruta"],
            "additionalProperties": False,
        },
    },
    {
        "name": "escribir_archivo",
        "description": (
            "Sobrescribe un archivo del workspace con el contenido indicado. "
            "Requiere aprobación humana: si el usuario la rechaza recibirás un error, "
            "no insistas con el mismo cambio."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Ruta relativa al workspace."},
                "contenido": {"type": "string", "description": "Contenido completo del archivo."},
            },
            "required": ["ruta", "contenido"],
            "additionalProperties": False,
        },
    },
    {
        "name": "ejecutar_tests",
        "description": (
            "Ejecuta la suite de tests del workspace con pytest y devuelve la salida. "
            "Úsala para reproducir fallos y para verificar tus cambios antes de terminar."
        ),
        "strict": True,
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


# ---------------------------------------------------------------------------
# Implementaciones
# ---------------------------------------------------------------------------

MAX_CARACTERES = 20_000  # Evita llenar la ventana de contexto con un archivo enorme.


class Herramientas:
    """Ejecuta herramientas confinadas a una carpeta (el "sandbox" del agente)."""

    def __init__(self, workspace: Path, aprobar: Callable[[str, str], bool]):
        self.raiz = workspace.resolve()
        self.aprobar = aprobar

    def _resolver(self, ruta: str) -> Path:
        # Principio de permisos mínimos: nada fuera del workspace.
        destino = (self.raiz / ruta).resolve()
        if not destino.is_relative_to(self.raiz):
            raise ErrorHerramienta(f"Ruta fuera del workspace: {ruta}")
        return destino

    def ejecutar(self, nombre: str, entrada: dict) -> str:
        metodo = getattr(self, nombre, None)
        if nombre.startswith("_") or metodo is None:
            raise ErrorHerramienta(f"Herramienta desconocida: {nombre}")
        return metodo(**entrada)

    def listar_archivos(self, ruta: str) -> str:
        carpeta = self._resolver(ruta)
        if not carpeta.is_dir():
            raise ErrorHerramienta(f"No es una carpeta: {ruta}")
        lineas = []
        for p in sorted(carpeta.rglob("*")):
            if any(parte.startswith(".") or parte == "__pycache__" for parte in p.relative_to(self.raiz).parts):
                continue
            rel = p.relative_to(self.raiz).as_posix()
            lineas.append(rel + "/" if p.is_dir() else rel)
        return "\n".join(lineas) or "(vacío)"

    def leer_archivo(self, ruta: str) -> str:
        archivo = self._resolver(ruta)
        if not archivo.is_file():
            raise ErrorHerramienta(f"No existe el archivo: {ruta}")
        texto = archivo.read_text(encoding="utf-8")
        if len(texto) > MAX_CARACTERES:
            texto = texto[:MAX_CARACTERES] + "\n[... truncado ...]"
        return texto

    def escribir_archivo(self, ruta: str, contenido: str) -> str:
        archivo = self._resolver(ruta)
        # Humano en el bucle: las acciones con efectos se aprueban.
        if not self.aprobar(ruta, contenido):
            raise ErrorHerramienta("El usuario rechazó el cambio.")
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(contenido, encoding="utf-8")
        return f"Escrito {ruta} ({len(contenido)} caracteres)."

    def ejecutar_tests(self) -> str:
        try:
            proceso = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"],
                cwd=self.raiz,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            raise ErrorHerramienta("Los tests tardaron más de 60 s.")
        salida = (proceso.stdout + proceso.stderr)[-MAX_CARACTERES:]
        return f"exit code: {proceso.returncode}\n{salida}"
