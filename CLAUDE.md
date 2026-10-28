# mentoria-agentes-claude

Mini agente de desarrollo con Claude, hecho para enseñar. Prioriza que el código
sea **legible y didáctico** por encima de abstracciones o features extra.

## Estructura
- `agente/bucle.py` — el bucle del agente (llamada a la API, tool_use → tool_result).
- `agente/herramientas.py` — esquemas JSON + implementaciones de las herramientas.
- `workspace/` — proyecto objetivo con bugs a propósito. **No lo arregles tú**: es el ejercicio para el agente.
- `tests/` — tests offline del agente (cliente falso, no llaman a la API).

## Comandos
- Tests del agente: `.venv/bin/python -m pytest -q`
- Ejecutar el agente: `.venv/bin/python -m agente "Haz que pasen los tests"`
- Restaurar el ejercicio: `git restore workspace/`

## Convenciones
- Nombres y comentarios en español.
- Cada herramienta nueva necesita: esquema en `ESQUEMAS`, método en `Herramientas` y un test en `tests/test_herramientas.py`.
- Las herramientas nunca deben salir de `workspace/` (usa `_resolver`).
