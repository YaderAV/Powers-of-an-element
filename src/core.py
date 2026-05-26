"""
core.py
=======

Utilidades base para los algoritmos de exponenciación modular.

Define la clase OpCounter, que registra el número de multiplicaciones y
cuadrados modulares ejecutados por cada algoritmo. La separación entre
ambos tipos de operación es importante porque varios análisis teóricos
(Cormen §31.6, HAC §14.6) los reportan por separado.
"""

from dataclasses import dataclass


@dataclass
class OpCounter:
    """
    Contador de operaciones modulares.

    Convenciones:
      - `mul(x, y, n)` debe usarse cuando x e y son operandos *distintos*.
      - `sqr(x, n)` debe usarse para cuadrados (x * x mod n).

    Esto refleja la distinción estándar en la literatura de exponenciación
    modular: los cuadrados son más baratos en algunas implementaciones
    (p. ej., con representación de Montgomery o GMP) y se cuentan aparte.
    """

    multiplications: int = 0
    squarings: int = 0

    @property
    def total(self) -> int:
        """Total de operaciones modulares (multiplicaciones + cuadrados)."""
        return self.multiplications + self.squarings

    def mul(self, x: int, y: int, n: int) -> int:
        """Multiplicación modular (x * y) mod n. Cuenta como una multiplicación."""
        self.multiplications += 1
        return (x * y) % n

    def sqr(self, x: int, n: int) -> int:
        """Cuadrado modular (x * x) mod n. Cuenta como un cuadrado."""
        self.squarings += 1
        return (x * x) % n

    def reset(self) -> None:
        """Reinicia los contadores a cero."""
        self.multiplications = 0
        self.squarings = 0

    def snapshot(self) -> dict:
        """Devuelve un diccionario con el estado actual del contador."""
        return {
            "multiplications": self.multiplications,
            "squarings": self.squarings,
            "total": self.total,
        }
