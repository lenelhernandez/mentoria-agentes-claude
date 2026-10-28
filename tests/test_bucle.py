"""Prueba el bucle sin llamar a la API: un cliente falso devuelve respuestas guionadas."""

from types import SimpleNamespace as NS

from agente.bucle import ejecutar_agente


class ClienteFalso:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.peticiones = []
        self.beta = NS(messages=NS(create=self._create))

    def _create(self, **kwargs):
        self.peticiones.append(kwargs)
        return self.respuestas.pop(0)


def respuesta(stop_reason, *bloques):
    return NS(stop_reason=stop_reason, content=list(bloques), usage=NS(input_tokens=10, output_tokens=5))


def test_ejecuta_herramienta_y_devuelve_resultado(tmp_path):
    (tmp_path / "hola.txt").write_text("hola mundo")
    cliente = ClienteFalso([
        respuesta("tool_use", NS(type="tool_use", id="t1", name="leer_archivo", input={"ruta": "hola.txt"})),
        respuesta("end_turn", NS(type="text", text="El archivo dice hola mundo.")),
    ])

    final = ejecutar_agente("¿Qué dice hola.txt?", tmp_path, client=cliente, log=lambda _: None)

    assert final == "El archivo dice hola mundo."
    # mensajes: [objetivo, assistant(tool_use), user(tool_result), ...]
    resultado = cliente.peticiones[1]["messages"][2]["content"][0]
    assert resultado == {"type": "tool_result", "tool_use_id": "t1", "content": "hola mundo", "is_error": False}


def test_errores_de_herramienta_vuelven_como_is_error(tmp_path):
    cliente = ClienteFalso([
        respuesta("tool_use", NS(type="tool_use", id="t1", name="leer_archivo", input={"ruta": "no-existe"})),
        respuesta("end_turn", NS(type="text", text="No existe.")),
    ])

    ejecutar_agente("lee", tmp_path, client=cliente, log=lambda _: None)

    assert cliente.peticiones[1]["messages"][2]["content"][0]["is_error"] is True


def test_respeta_max_turnos(tmp_path):
    bucle_infinito = respuesta("tool_use", NS(type="tool_use", id="t", name="listar_archivos", input={"ruta": "."}))
    cliente = ClienteFalso([bucle_infinito] * 3)

    final = ejecutar_agente("x", tmp_path, client=cliente, max_turnos=3, log=lambda _: None)

    assert "límite" in final
