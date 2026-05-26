"""
kary.py
=======

Exponenciación modular por método de ventana fija (k-aria).

Se precomputa una tabla con todas las potencias a^j mod n para
j = 0, 1, ..., 2^k − 1. Luego se procesa el exponente en bloques de k
bits, de izquierda a derecha. En cada bloque se hacen k cuadrados
seguidos de una multiplicación por T[w].

Costo (multiplicaciones modulares):
    - Precomputación: 2^k − 2.
    - Núcleo del bucle: β cuadrados + ⌈β/k⌉ − 1 multiplicaciones.
    - Total: β + ⌈β/k⌉ + 2^k − 2 operaciones, aprox.

El tamaño óptimo de ventana minimiza el total y se aproxima por
    k_opt ≈ log₂ β − log₂ log₂ β.

Para β = 1024 da k ≈ 7; para β = 2048 da k ≈ 8.

Referencia: Menezes, van Oorschot y Vanstone, *Handbook of Applied
Cryptography*, Algoritmo 14.82 (fixed-window exponentiation).
"""

from .core import OpCounter


def kary_modexp(
    a: int,
    b: int,
    n: int,
    k: int = 4,
    counter: OpCounter | None = None,
) -> int:
    """
    Calcula a^b mod n por el método k-ario (ventana fija).

    Parameters
    ----------
    a : int
        Base.
    b : int
        Exponente no negativo.
    n : int
        Módulo positivo.
    k : int, default 4
        Tamaño de la ventana en bits. Debe ser ≥ 1.
    counter : OpCounter, optional
        Contador de operaciones.
    """
    if k < 1:
        raise ValueError("El tamaño de ventana k debe ser ≥ 1")
    if n == 1:
        return 0
    if b == 0:
        return 1

    a = a % n
    size = 1 << k  # 2^k

    # ---- Precomputación: T[j] = a^j mod n para j = 0, ..., 2^k - 1 ----
    table = [1] * size
    if size > 1:
        table[1] = a
    for j in range(2, size):
        if counter is not None:
            table[j] = counter.mul(table[j - 1], a, n)
        else:
            table[j] = (table[j - 1] * a) % n

    # ---- División del exponente en ventanas de k bits ----
    bits = bin(b)[2:]
    # Padding por la izquierda para que la longitud sea múltiplo de k
    pad = (-len(bits)) % k
    bits = "0" * pad + bits
    windows = [int(bits[i : i + k], 2) for i in range(0, len(bits), k)]

    # ---- Bucle principal ----
    # Inicializamos con la primera ventana (puede valer 0 si b tenía leading zeros;
    # con b > 0 no ocurre porque bin(b)[2:] empieza en '1').
    result = table[windows[0]]
    for w in windows[1:]:
        # k cuadrados consecutivos
        for _ in range(k):
            if counter is not None:
                result = counter.sqr(result, n)
            else:
                result = (result * result) % n
        # Multiplicación por T[w]. En la versión estricta del libro se
        # multiplica incluso cuando w == 0 (resultado·1). Esta variante
        # incluye esa multiplicación "desperdiciada" para reflejar
        # fielmente el algoritmo; la versión skip-zero es una
        # optimización que tiende hacia ventana deslizante.
        if counter is not None:
            result = counter.mul(result, table[w], n)
        else:
            result = (result * table[w]) % n
    return result
