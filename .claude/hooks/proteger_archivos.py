"""Hook PreToolUse: impide que Claude Code edite archivos protegidos.

Claude Code envía por stdin un JSON con la herramienta y su entrada.
Salir con código 2 bloquea la acción y el texto de stderr se le muestra a Claude.
"""

import json
import sys

PROTEGIDOS = (".env", "workspace/tests/")

evento = json.load(sys.stdin)
ruta = evento.get("tool_input", {}).get("file_path", "")

for patron in PROTEGIDOS:
    if patron in ruta:
        print(f"Bloqueado por hook: '{ruta}' está protegido ({patron}). Los tests son la especificación.", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
