# Mentoría: agentes con Claude — proyecto práctico

Un **mini agente de desarrollo** en ~150 líneas de Python, para ver por dentro lo
que hacen herramientas como Claude Code: el bucle, las herramientas, los permisos,
el contexto y la verificación.

Acompaña a la **parte 2** de la mentoría: las presentaciones están en [`docs/`](docs/) (ábrelas en el navegador; flechas para avanzar, `F` para pantalla completa).

```
agente/
  bucle.py          ← el bucle: llamada a la API → tool_use → tool_result → repetir
  herramientas.py   ← esquemas JSON + implementación confinada al workspace
  __main__.py       ← CLI con aprobación humana de escrituras
workspace/          ← proyecto con 3 bugs a propósito (el "ticket" del agente)
  AGENTE.md         ← instrucciones del proyecto (como CLAUDE.md)
tests/              ← tests del agente, sin llamar a la API (cliente falso)
.claude/            ← configuración para practicar Claude Code
  settings.json     ← permisos + hook
  hooks/            ← hook que protege los tests del workspace
  skills/           ← skill "agregar-herramienta"
  agents/           ← subagente "revisor"
CLAUDE.md           ← contexto del repo para Claude Code
```

## Puesta en marcha

```bash
python3 -m venv .venv
.venv/bin/pip install "anthropic>=2.3" pytest
export ANTHROPIC_API_KEY=sk-ant-...   # nunca lo subas al repo
.venv/bin/python -m pytest -q         # tests del agente (no gastan tokens)
```

Variables opcionales:

| Variable | Por defecto | Para qué |
|---|---|---|
| `CLAUDE_MODEL` | `claude-opus-5-5` | Prueba `claude-sonnet-5-5` o `claude-haiku-5-5` y compara |
| `CLAUDE_EFFORT` | `medium` | `low` · `medium` · `high` · `xhigh` · `max` |

## Ejercicios

### 1. Ver el bucle en acción (15 min)

```bash
.venv/bin/python -m agente "Haz que pasen los tests del workspace"
```

Observa la traza `[herramienta] …`. Preguntas para comentar:
- ¿Ejecutó los tests **antes** de editar? ¿Por qué importa?
- ¿Cuántos turnos y tokens usó? Repite con `CLAUDE_EFFORT=low` y con otro modelo.
- Rechaza (`N`) una escritura: ¿qué hace el agente con ese error?

Para repetir el ejercicio: `git restore workspace/`.

### 2. Leer el código (15 min)

En `agente/bucle.py`, ubica:
- Dónde se decide si el agente **sigue o termina** (`stop_reason`).
- Por qué todos los `tool_result` van en **un solo** mensaje.
- Cómo entra `AGENTE.md` al contexto. Cámbialo (p. ej. "responde siempre en inglés") y vuelve a correr.

### 3. Añadir una herramienta (20 min)

Añade `buscar_texto(patron)` que devuelva `archivo:línea: texto` de las coincidencias.
Hazlo a mano **o** pídeselo a Claude Code usando la skill del repo:

```
/agregar-herramienta buscar_texto: busca un patrón en los archivos del workspace
```

Luego compara: ¿el agente usa la herramienta nueva por sí solo? ¿Qué cambia si la
`description` es vaga?

### 4. Guardarraíles (15 min)

- Intenta que el agente lea `../pyproject.toml`. ¿Qué lo impide? (`_resolver`)
- En Claude Code, pide: *"cambia el test de cupones para que pase"*. El hook
  `.claude/hooks/proteger_archivos.py` lo bloquea. Léelo: es un script de 20 líneas.
- Discute: ¿qué otra acción merecería aprobación humana o un hook?

### 5. Claude Code como compañero (20 min)

Abre Claude Code en la raíz del repo (`claude`) y prueba:
1. *"Explícame cómo funciona este repo"* → fíjate que usa `CLAUDE.md`.
2. Activa **plan mode** (Shift+Tab) y pide *"añade soporte de cupones de monto fijo"*. Revisa el plan antes de aceptar.
3. Pide *"usa el subagente revisor para revisar mis cambios"*.

### Extra

- **Tool Runner**: reescribe el bucle con `client.beta.messages.tool_runner(...)` y `@beta_tool`. ¿Qué ganas y qué pierdes de visibilidad?
- **Evals**: crea 3 workspaces con bugs distintos y un script que mida cuántos resuelve cada modelo/effort y con cuántos tokens.
- **MCP**: expón `herramientas.py` como servidor MCP para usarlo desde Claude Code.

## Seguridad

- La API key va en variables de entorno, nunca en el código ni en el repo.
- El agente solo ve `workspace/`; las escrituras piden confirmación salvo con `--auto`.
- `ejecutar_tests` corre código Python del workspace: úsalo solo con código en el que confíes.
