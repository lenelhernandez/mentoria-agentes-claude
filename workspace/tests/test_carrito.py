import pytest

from carrito import Carrito


def test_carrito_vacio():
    assert Carrito().total() == 0


def test_subtotal_considera_cantidad():
    c = Carrito()
    c.agregar("café", 3.50, cantidad=2)
    c.agregar("pan", 1.00)
    assert c.subtotal() == 8.00


def test_agregar_mismo_producto_suma_cantidades():
    c = Carrito()
    c.agregar("café", 3.50)
    c.agregar("café", 3.50, cantidad=2)
    assert len(c.lineas) == 1
    assert c.lineas[0].cantidad == 3


def test_cupon_es_porcentaje():
    c = Carrito()
    c.agregar("auriculares", 100.00)
    c.aplicar_cupon("BIENVENIDA10")
    assert c.total() == 90.00


def test_cupon_invalido():
    with pytest.raises(ValueError):
        Carrito().aplicar_cupon("GRATIS")


def test_cantidad_negativa():
    with pytest.raises(ValueError):
        Carrito().agregar("pan", 1.00, cantidad=-1)
