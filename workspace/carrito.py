"""Carrito de compras de una tienda pequeña.

Tiene bugs a propósito: el objetivo del ejercicio es que el agente los encuentre
y los arregle haciendo pasar los tests.
"""

from dataclasses import dataclass, field


@dataclass
class Linea:
    producto: str
    precio_unitario: float
    cantidad: int = 1


@dataclass
class Carrito:
    lineas: list[Linea] = field(default_factory=list)
    cupon: str | None = None

    CUPONES = {"BIENVENIDA10": 0.10, "VIP25": 0.25}

    def agregar(self, producto: str, precio: float, cantidad: int = 1) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")
        for linea in self.lineas:
            if linea.producto == producto:
                linea.cantidad = cantidad
                return
        self.lineas.append(Linea(producto, precio, cantidad))

    def aplicar_cupon(self, codigo: str) -> None:
        if codigo not in self.CUPONES:
            raise ValueError(f"Cupón inválido: {codigo}")
        self.cupon = codigo

    def subtotal(self) -> float:
        return sum(linea.precio_unitario for linea in self.lineas)

    def total(self) -> float:
        descuento = self.CUPONES.get(self.cupon, 0)
        return round(self.subtotal() - descuento, 2)
