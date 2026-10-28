---
name: agregar-herramienta
description: Añade una herramienta nueva al mini agente (esquema + implementación + test). Úsala cuando el usuario pida que el agente pueda hacer algo nuevo, p. ej. "que el agente pueda buscar texto".
---

# Añadir una herramienta al agente

Sigue estos pasos en orden y no te saltes el test:

1. **Esquema** en `ESQUEMAS` (`agente/herramientas.py`):
   - `name` en snake_case y en español.
   - `description` que diga *cuándo* usarla y *qué devuelve*, no solo qué hace.
   - `strict: True`, `additionalProperties: False` y todos los campos en `required`.
2. **Implementación**: un método en la clase `Herramientas` con el mismo nombre.
   - Toda ruta pasa por `self._resolver(...)`.
   - Errores esperables → `raise ErrorHerramienta("mensaje útil para el modelo")`.
   - Limita el tamaño de la salida con `MAX_CARACTERES`.
   - Si tiene efectos (escribe, borra, llama a la red), pide aprobación con `self.aprobar`.
3. **Test** en `tests/test_herramientas.py`: caso feliz + un caso de error.
4. Ejecuta `.venv/bin/python -m pytest -q` y muestra el resultado.
5. Resume en 3 líneas qué se añadió y cómo probarla con el agente.
