"""
binary_rl.py
============

Exponenciación modular por cuadrados repetidos, recorriendo los bits del
exponente de derecha a izquierda (LSB → MSB).

Resuelve el ejercicio 31.6-2 de Cormen: «Give a modular exponentiation
algorithm that examines the bits of b from right to left instead of left
to right».

Invariante de bucle: en cada iteración,
  - `base` contiene a^(2^i) mod n, donde i es el índice del bit a procesar.
  - `result` acumula el producto de las potencias correspondientes a los
    bits ya vistos del exponente.

Conteo asintótico idéntico a la versión L→R: β cuadrados y H(b)
multiplicaciones. La diferencia es estructural — cada iteración hace
ambas operaciones de forma independiente, lo cual se presta mejor al
paralelismo a nivel de instrucción.
"""

from .core import OpCounter


def binary_rl_modexp(a: int, b: int, n: int, counter: OpCounter | None = None) -> int:
    """
    Calcula a^b mod n por cuadrados repetidos, recorriendo bits R→L.
    """
    if n == 1:
        return 0
    if b == 0:
        return 1

    a = a % n
    result = 1
    base = a

    while b > 0:
        if b & 1:
            if counter is not None:
                result = counter.mul(result, base, n)
            else:
                result = (result * base) % n
        b >>= 1
        # Sólo elevamos al cuadrado si todavía quedan bits por procesar
        # (evita un cuadrado desperdiciado tras el bit más significativo).
        if b > 0:
            if counter is not None:
                base = counter.sqr(base, n)
            else:
                base = (base * base) % n
    return result
