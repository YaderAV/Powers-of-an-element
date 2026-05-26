"""
naive.py
========

Método ingenuo: a^b mod n por multiplicación iterada.

Realiza b multiplicaciones modulares. Su complejidad es O(b), lo que lo
vuelve inviable para exponentes grandes — se incluye únicamente como
*baseline* didáctico para contrastar con los métodos sublineales en b.
"""

from .core import OpCounter


def naive_modexp(a: int, b: int, n: int, counter: OpCounter | None = None) -> int:
    """
    Calcula a^b mod n multiplicando b veces.

    Parameters
    ----------
    a : int
        Base.
    b : int
        Exponente no negativo.
    n : int
        Módulo positivo.
    counter : OpCounter, optional
        Si se provee, registra las operaciones realizadas.

    Returns
    -------
    int
        Valor de a^b mod n.
    """
    if n == 1:
        return 0
    if b == 0:
        return 1

    a = a % n
    result = 1
    for _ in range(b):
        if counter is not None:
            result = counter.mul(result, a, n)
        else:
            result = (result * a) % n
    return result
