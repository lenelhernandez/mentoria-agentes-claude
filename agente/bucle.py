"""El bucle del agente: objetivo -> acción -> observación -> repetir.

Esta es la versión "manual" del bucle, escrita a propósito para que se vea
cada paso. El SDK de Anthropic también trae un Tool Runner que hace este
mismo bucle por ti (ver README, ejercicio extra).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import anthropic

from .herramientas import ESQUEMAS, ErrorHerramienta, Herramientas

MODELO = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
# effort controla cuánto piensa el modelo (y cuántos tokens gasta).
# low | medium | high | xhigh | max
ESFUERZO = os.environ.get("CLAUDE_EFFORT", "medium")

# Si el modelo rechaza una petición por sus clasificadores de seguridad, la API
# la reintenta en otro modelo. Disponible en Opus 5.5, Fable 5.1 y Sonnet 5.5.
MODELOS_CON_FALLBACK = {"claude-opus-5-5", "claude-fable-5-1", "claude-sonnet-5-5"}

SISTEMA = """Eres un agente de desarrollo que trabaja dentro de un workspace Python.

Cómo trabajas:
- Antes de editar, explora: lista archivos y lee el código y los tests relevantes.
- Reproduce el problema ejecutando los tests antes de cambiar nada.
- Haz el cambio más pequeño que resuelva el objetivo. No cambies los tests para que pasen.
- Verifica ejecutando los tests después de cada cambio.
- Termina con un resumen corto: qué estaba mal, qué cambiaste y el resultado de los tests.
"""


def construir_sistema(workspace: Path) -> str:
    """Igual que CLAUDE.md en Claude Code: instrucciones del proyecto en el contexto."""
    instrucciones = workspace / "AGENTE.md"
    if instrucciones.is_file():
        return SISTEMA + "\n# Instrucciones del proyecto (AGENTE.md)\n\n" + instrucciones.read_text(encoding="utf-8")
    return SISTEMA


def ejecutar_agente(
    objetivo: str,
    workspace: Path,
    *,
    client: anthropic.Anthropic | None = None,
    aprobar: Callable[[str, str], bool] = lambda ruta, contenido: True,
    max_turnos: int = 20,
    log: Callable[[str], None] = print,
) -> str:
    client = client or anthropic.Anthropic()
    herramientas = Herramientas(workspace, aprobar)
    sistema = construir_sistema(workspace)
    extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"} if MODELO in MODELOS_CON_FALLBACK else {}

    # El "estado" del agente es simplemente la lista de mensajes.
    mensajes: list = [{"role": "user", "content": objetivo}]
    tokens_entrada = tokens_salida = 0

    for turno in range(1, max_turnos + 1):
        respuesta = client.beta.messages.create(
            model=MODELO,
            max_tokens=16000,
            system=sistema,
            tools=ESQUEMAS,
            messages=mensajes,
            output_config={"effort": ESFUERZO},
            **extra,
        )
        tokens_entrada += respuesta.usage.input_tokens
        tokens_salida += respuesta.usage.output_tokens

        # Devolvemos el contenido completo (incluidos bloques de thinking) sin tocarlo.
        mensajes.append({"role": "assistant", "content": respuesta.content})

        for bloque in respuesta.content:
            if bloque.type == "text" and bloque.text.strip():
                log(f"\n[claude] {bloque.text.strip()}")

        if respuesta.stop_reason == "refusal":
            return "El modelo rechazó la petición."
        if respuesta.stop_reason == "max_tokens":
            return "La respuesta se cortó por max_tokens."
        if respuesta.stop_reason != "tool_use":
            log(f"\n[fin] {turno} turnos · {tokens_entrada} tokens entrada · {tokens_salida} tokens salida")
            return "".join(b.text for b in respuesta.content if b.type == "text")

        # Ejecutamos TODAS las herramientas pedidas y devolvemos TODOS los
        # resultados en un único mensaje de usuario.
        resultados = []
        for bloque in respuesta.content:
            if bloque.type != "tool_use":
                continue
            log(f"[herramienta] {bloque.name}({_resumen(bloque.input)})")
            try:
                salida, es_error = herramientas.ejecutar(bloque.name, bloque.input), False
            except ErrorHerramienta as e:
                salida, es_error = str(e), True
            log(f"   -> {'ERROR: ' if es_error else ''}{_primera_linea(salida)}")
            resultados.append(
                {"type": "tool_result", "tool_use_id": bloque.id, "content": salida, "is_error": es_error}
            )
        mensajes.append({"role": "user", "content": resultados})

    return f"Se alcanzó el límite de {max_turnos} turnos sin terminar."


def _resumen(entrada: dict) -> str:
    corto = {k: (v[:40] + "…" if isinstance(v, str) and len(v) > 40 else v) for k, v in entrada.items()}
    return json.dumps(corto, ensure_ascii=False)


def _primera_linea(texto: str) -> str:
    linea = texto.strip().splitlines()[0] if texto.strip() else "(vacío)"
    return linea[:100]
