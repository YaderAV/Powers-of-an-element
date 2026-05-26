"""
test_correctness.py
===================

Suite de tests de correctitud para los algoritmos de exponenciación modular.
Cada algoritmo se compara contra `pow(a, b, n)` (implementado en C en CPython).

Ejecutar con:
    pytest tests/ -v

o desde la raíz del proyecto:
    python -m pytest tests/ -v
"""

import random
import sys
from pathlib import Path

# Permite ejecutar los tests sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import (
    ALGORITHMS,
    OpCounter,
    binary_lr_modexp,
    binary_rl_modexp,
    kary_modexp,
    naive_modexp,
    sliding_window_modexp,
)


# Semilla global para reproducibilidad
random.seed(2026)


# ---------------------------------------------------------------------------
# Algoritmos sin parámetro de ventana
# ---------------------------------------------------------------------------

NO_WINDOW = [naive_modexp, binary_lr_modexp, binary_rl_modexp]
WITH_WINDOW = [kary_modexp, sliding_window_modexp]


# ---------------------------------------------------------------------------
# Casos borde
# ---------------------------------------------------------------------------

EDGE_CASES = [
    # (a, b, n, expected)
    (0, 0, 7, 1),       # 0^0 = 1 por convención
    (1, 0, 7, 1),
    (5, 0, 7, 1),
    (5, 1, 7, 5),
    (0, 5, 7, 0),
    (1, 1000, 7, 1),
    (2, 10, 1, 0),      # cualquier cosa mod 1 = 0
    (7, 560, 561, 1),   # Figura 31.4 de Cormen (561 es un Carmichael)
]


@pytest.mark.parametrize("algo", NO_WINDOW)
@pytest.mark.parametrize("a,b,n,expected", EDGE_CASES)
def test_edge_cases_no_window(algo, a, b, n, expected):
    """Casos borde para algoritmos sin ventana."""
    # naive es O(b), saltamos el caso de b grande para él
    if algo is naive_modexp and b > 1000:
        pytest.skip("naive es demasiado lento para b grande")
    assert algo(a, b, n) == expected


@pytest.mark.parametrize("algo", WITH_WINDOW)
@pytest.mark.parametrize("k", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("a,b,n,expected", EDGE_CASES)
def test_edge_cases_with_window(algo, k, a, b, n, expected):
    """Casos borde para algoritmos con ventana."""
    assert algo(a, b, n, k=k) == expected


# ---------------------------------------------------------------------------
# Cormen Figura 31.4: verificación detallada
# ---------------------------------------------------------------------------

def test_cormen_figure_31_4():
    """
    Reproduce el ejemplo de Cormen §31.6, Fig 31.4:
        7^560 mod 561 = 1
    Verifica con todos los algoritmos.
    """
    expected = pow(7, 560, 561)
    assert expected == 1  # como confirma el libro

    assert naive_modexp(7, 560, 561) == 1
    assert binary_lr_modexp(7, 560, 561) == 1
    assert binary_rl_modexp(7, 560, 561) == 1
    for k in range(1, 7):
        assert kary_modexp(7, 560, 561, k=k) == 1
        assert sliding_window_modexp(7, 560, 561, k=k) == 1


# ---------------------------------------------------------------------------
# Pruebas aleatorias contra pow()
# ---------------------------------------------------------------------------

def random_test_case(bit_size: int) -> tuple[int, int, int]:
    """Genera (a, b, n) con b y n de bit_size bits."""
    n = random.getrandbits(bit_size) | (1 << (bit_size - 1)) | 1   # impar y de bit_size bits
    a = random.randrange(0, n)
    b = random.getrandbits(bit_size)
    return a, b, n


SMALL_SIZES = [8, 16, 32, 64]
LARGE_SIZES = [128, 256, 512, 1024]


@pytest.mark.parametrize("algo", [binary_lr_modexp, binary_rl_modexp])
@pytest.mark.parametrize("bit_size", SMALL_SIZES + LARGE_SIZES)
def test_random_binary_methods(algo, bit_size):
    """Tests aleatorios para métodos binarios contra pow()."""
    for _ in range(20):
        a, b, n = random_test_case(bit_size)
        assert algo(a, b, n) == pow(a, b, n), (
            f"Fallo en {algo.__name__}: a={a}, b={b}, n={n}"
        )


@pytest.mark.parametrize("algo", WITH_WINDOW)
@pytest.mark.parametrize("bit_size", SMALL_SIZES + LARGE_SIZES)
@pytest.mark.parametrize("k", [2, 4, 6])
def test_random_window_methods(algo, bit_size, k):
    """Tests aleatorios para métodos con ventana contra pow()."""
    for _ in range(10):
        a, b, n = random_test_case(bit_size)
        assert algo(a, b, n, k=k) == pow(a, b, n), (
            f"Fallo en {algo.__name__} con k={k}: a={a}, b={b}, n={n}"
        )


def test_naive_small():
    """Tests para el método ingenuo con exponentes pequeños."""
    for _ in range(50):
        a = random.randrange(0, 100)
        b = random.randrange(0, 200)
        n = random.randrange(1, 100)
        assert naive_modexp(a, b, n) == pow(a, b, n)


# ---------------------------------------------------------------------------
# Verificación de los contadores
# ---------------------------------------------------------------------------

def test_op_counter_basic():
    """Verifica que OpCounter registre correctamente las operaciones."""
    counter = OpCounter()
    assert counter.total == 0
    counter.mul(2, 3, 7)
    assert counter.multiplications == 1
    counter.sqr(4, 7)
    assert counter.squarings == 1
    assert counter.total == 2
    counter.reset()
    assert counter.total == 0


def test_binary_lr_op_count():
    """
    Cormen Figura 31.4: 7^560 mod 561.
    560 = 1000110000 (10 bits, 3 unos).
    El algoritmo realiza 10 cuadrados + 3 multiplicaciones.
    """
    counter = OpCounter()
    binary_lr_modexp(7, 560, 561, counter=counter)
    assert counter.squarings == 10
    assert counter.multiplications == 3


def test_binary_rl_op_count():
    """
    Para b=560 = 1000110000 (10 bits, 3 unos):
    R→L hace 9 cuadrados (uno menos: no se eleva tras el último bit)
    + 3 multiplicaciones.
    """
    counter = OpCounter()
    binary_rl_modexp(7, 560, 561, counter=counter)
    assert counter.squarings == 9
    assert counter.multiplications == 3


# ---------------------------------------------------------------------------
# Consistencia cruzada: todos los algoritmos dan el mismo resultado
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bit_size", [16, 32, 64, 128])
def test_cross_algorithm_consistency(bit_size):
    """Todos los algoritmos producen el mismo resultado para la misma entrada."""
    for _ in range(5):
        a, b, n = random_test_case(bit_size)
        expected = pow(a, b, n)
        results = {
            "binary_lr": binary_lr_modexp(a, b, n),
            "binary_rl": binary_rl_modexp(a, b, n),
            "kary_4": kary_modexp(a, b, n, k=4),
            "kary_6": kary_modexp(a, b, n, k=6),
            "sliding_4": sliding_window_modexp(a, b, n, k=4),
            "sliding_6": sliding_window_modexp(a, b, n, k=6),
        }
        for name, result in results.items():
            assert result == expected, (
                f"{name} discrepa: {result} vs {expected} "
                f"para a={a}, b={b}, n={n}"
            )


if __name__ == "__main__":
    # Permite correr el archivo directamente sin pytest
    pytest.main([__file__, "-v"])
