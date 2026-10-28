import pytest

from agente.herramientas import ErrorHerramienta, Herramientas


@pytest.fixture
def ws(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    return tmp_path


def test_leer_archivo(ws):
    assert Herramientas(ws, lambda r, c: True).leer_archivo("a.py") == "x = 1\n"


def test_no_sale_del_workspace(ws):
    with pytest.raises(ErrorHerramienta):
        Herramientas(ws, lambda r, c: True).leer_archivo("../../etc/passwd")


def test_escritura_rechazada_no_toca_el_archivo(ws):
    h = Herramientas(ws, lambda r, c: False)
    with pytest.raises(ErrorHerramienta):
        h.escribir_archivo("a.py", "roto")
    assert (ws / "a.py").read_text() == "x = 1\n"


def test_herramienta_desconocida(ws):
    with pytest.raises(ErrorHerramienta):
        Herramientas(ws, lambda r, c: True).ejecutar("_resolver", {"ruta": "."})
