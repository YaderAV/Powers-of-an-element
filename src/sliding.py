"""
sliding.py
==========

Exponenciación modular por método de ventana deslizante.

Mejoras respecto a la ventana fija k-aria:
  1. Sólo se precomputan las **potencias impares** a^1, a^3, ..., a^(2^k − 1).
     La tabla ocupa la mitad: 2^(k−1) valores.
  2. Las ventanas tienen **tamaño variable** entre 1 y k bits, y se eligen
     de modo que siempre empiecen y terminen en 1 (valor impar).
  3. Los bits 0 entre ventanas son simplemente cuadrados (sin
     multiplicación por tabla).

Costo (multiplicaciones modulares):
  - Precomputación: 1 cuadrado + (2^(k−1) − 1) multiplicaciones.
  - Núcleo: β cuadrados + ≈ β/(k+1) multiplicaciones por entradas de tabla.
  - Total típico ≈ β + β/(k+1) + 2^(k−1).

Suele ahorrar 10–15 % de operaciones respecto a la k-aria fija a igual k,
y usa la mitad de memoria.

Referencia: Menezes, van Oorschot y Vanstone, *Handbook of Applied
Cryptography*, Algoritmo 14.85 (sliding-window exponentiation).
"""

from .core import OpCounter


def sliding_window_modexp(
    a: int,
    b: int,
    n: int,
    k: int = 4,
    counter: OpCounter | None = None,
) -> int:
    """
    Calcula a^b mod n por ventana deslizante de hasta k bits.
    """
    if k < 1:
        raise ValueError("El tamaño máximo de ventana k debe ser ≥ 1")
    if n == 1:
        return 0
    if b == 0:
        return 1

    a = a % n

    # ---- Precomputación de potencias impares ----
    # table[1] = a, table[3] = a^3, ..., table[2^k - 1].
    table = {1: a}
    if k > 1:
        if counter is not None:
            a_sq = counter.sqr(a, n)
        else:
            a_sq = (a * a) % n
        cur = a
        for idx in range(3, 1 << k, 2):
            if counter is not None:
                cur = counter.mul(cur, a_sq, n)
            else:
                cur = (cur * a_sq) % n
            table[idx] = cur

    # ---- Recorrido del exponente ----
    bits = bin(b)[2:]
    L = len(bits)

    # Localiza la primera ventana: la más larga (≤ k) que empiece en bits[0]='1'
    # y termine en un bit '1'. Inicializamos result con table[window_val]
    # para evitar cuadrados desperdiciados de 1.
    j_end = min(k, L)
    while bits[j_end - 1] == "0":
        j_end -= 1
    window_val = int(bits[0:j_end], 2)
    result = table[window_val]
    i = j_end

    while i < L:
        if bits[i] == "0":
            # Bit cero entre ventanas → un cuadrado
            if counter is not None:
                result = counter.sqr(result, n)
            else:
                result = (result * result) % n
            i += 1
        else:
            # Encontrar la ventana más larga ≤ k que empiece en i y termine en '1'
            j_end = min(i + k, L)
            while bits[j_end - 1] == "0":
                j_end -= 1
            window_val = int(bits[i:j_end], 2)
            window_len = j_end - i

            # Tantos cuadrados como bits tenga la ventana
            for _ in range(window_len):
                if counter is not None:
                    result = counter.sqr(result, n)
                else:
                    result = (result * result) % n
            # Una multiplicación por la entrada de la tabla
            if counter is not None:
                result = counter.mul(result, table[window_val], n)
            else:
                result = (result * table[window_val]) % n
            i = j_end

    return result
