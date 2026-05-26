"""
binary_lr.py
============

Exponenciación modular por cuadrados repetidos, recorriendo los bits del
exponente de izquierda a derecha (MSB → LSB).

Implementación fiel al pseudocódigo MODULAR-EXPONENTIATION presentado en
Cormen, Leiserson, Rivest y Stein, *Introduction to Algorithms*, 4ª ed.,
sección 31.6, página 957.

Invariante de bucle (Cormen): justo antes de cada iteración,
  1. c es el prefijo ⟨b_k, b_{k-1}, ..., b_{i+1}⟩ de la representación
     binaria de b.
  2. d = a^c mod n.

Análisis: β + H(b) operaciones, donde β = ⌊log₂ b⌋ + 1 y H(b) es el peso
de Hamming (número de unos) de b. En promedio, ≈ 1.5·β multiplicaciones
modulares.
"""

from .core import OpCounter


def binary_lr_modexp(a: int, b: int, n: int, counter: OpCounter | None = None) -> int:
    """
    Calcula a^b mod n por cuadrados repetidos, recorriendo bits L→R.

    Sigue el pseudocódigo MODULAR-EXPONENTIATION de Cormen §31.6.
    """
    if n == 1:
        return 0
    if b == 0:
        return 1

    a = a % n
    d = 1
    # bin(b)[2:] entrega los bits desde el MSB. Para b > 0, comienza con '1'.
    for bit in bin(b)[2:]:
        # Línea 6 del pseudocódigo de Cormen: d ← (d · d) mod n
        if counter is not None:
            d = counter.sqr(d, n)
        else:
            d = (d * d) % n
        # Líneas 7-9: si el bit es 1, multiplicar por a.
        if bit == "1":
            if counter is not None:
                d = counter.mul(d, a, n)
            else:
                d = (d * a) % n
    return d
