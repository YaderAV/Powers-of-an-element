"""Demostración interactiva de los algoritmos de exponenciación modular.
Muestra que todos producen el mismo resultado y compara el número de
operaciones (cuadrados y multiplicaciones) para distintos tamaños de
exponente.
"""

import random
import time

from src import (
    OpCounter,
    binary_lr_modexp,
    binary_rl_modexp,
    kary_modexp,
    naive_modexp,
    sliding_window_modexp,
)


random.seed(2026)


def run_with_count(fn, *args, **kwargs):
    """Ejecuta fn, devuelve (resultado, sqr, mul, tiempo_ms)."""
    counter = OpCounter()
    t0 = time.perf_counter()
    result = fn(*args, **kwargs, counter=counter)
    elapsed = (time.perf_counter() - t0) * 1000
    return result, counter.squarings, counter.multiplications, elapsed


def demo_cormen_example():
    """Ejemplo de Cormen Fig. 31.4: 7^560 mod 561 = 1."""
    print("=" * 70)
    print("EJEMPLO DE CORMEN (Figura 31.4): 7^560 mod 561")
    print("=" * 70)
    a, b, n = 7, 560, 561
    expected = pow(a, b, n)
    print(f"  Resultado esperado: {expected}\n")

    print(f"  {'Algoritmo':<22}{'sqr':>6}{'mul':>6}{'total':>8}  {'resultado':>10}")
    print(f"  {'-'*22}{'-'*6}{'-'*6}{'-'*8}  {'-'*10}")

    algos = [
        ("naive",        lambda: run_with_count(naive_modexp, a, b, n)),
        ("binary_lr",    lambda: run_with_count(binary_lr_modexp, a, b, n)),
        ("binary_rl",    lambda: run_with_count(binary_rl_modexp, a, b, n)),
        ("kary k=2",     lambda: run_with_count(kary_modexp, a, b, n, k=2)),
        ("kary k=4",     lambda: run_with_count(kary_modexp, a, b, n, k=4)),
        ("sliding k=2",  lambda: run_with_count(sliding_window_modexp, a, b, n, k=2)),
        ("sliding k=4",  lambda: run_with_count(sliding_window_modexp, a, b, n, k=4)),
    ]
    for name, fn in algos:
        r, sqr, mul, _ = fn()
        ok = "✓" if r == expected else "✗"
        print(f"  {name:<22}{sqr:>6}{mul:>6}{sqr+mul:>8}  {r:>10} {ok}")
    print()


def demo_scaling():
    """Compara los algoritmos a tamaños crecientes de exponente."""
    print("=" * 70)
    print("ESCALABILIDAD: número de operaciones vs. tamaño del exponente")
    print("=" * 70)
    print(f"  {'β (bits)':>10}  {'binary_lr':>12}  {'binary_rl':>12}  "
          f"{'kary k=4':>12}  {'kary k=6':>12}  {'sliding k=4':>14}  {'sliding k=6':>14}")
    print(f"  {'-'*10}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*14}  {'-'*14}")

    for bits in [64, 128, 256, 512, 1024, 2048]:
        # Generar una sola terna por tamaño para mantener equidad
        n = (random.getrandbits(bits) | (1 << (bits - 1))) | 1
        a = random.randrange(0, n)
        b = random.getrandbits(bits)

        results = {}
        for name, fn, args in [
            ("binary_lr",   binary_lr_modexp,       ()),
            ("binary_rl",   binary_rl_modexp,       ()),
            ("kary_4",      kary_modexp,            (4,)),
            ("kary_6",      kary_modexp,            (6,)),
            ("sliding_4",   sliding_window_modexp,  (4,)),
            ("sliding_6",   sliding_window_modexp,  (6,)),
        ]:
            counter = OpCounter()
            if args:
                fn(a, b, n, *args, counter=counter)
            else:
                fn(a, b, n, counter=counter)
            results[name] = counter.total

        print(f"  {bits:>10}  {results['binary_lr']:>12}  {results['binary_rl']:>12}  "
              f"{results['kary_4']:>12}  {results['kary_6']:>12}  "
              f"{results['sliding_4']:>14}  {results['sliding_6']:>14}")
    print()


def demo_window_sweep():
    """Para β fijo, explora el efecto del tamaño de ventana k."""
    print("=" * 70)
    print("EFECTO DE k (β = 1024 bits)")
    print("=" * 70)

    n = (random.getrandbits(1024) | (1 << 1023)) | 1
    a = random.randrange(0, n)
    b = random.getrandbits(1024)

    print(f"  {'k':>3}  {'kary (precomp)':>16}  {'kary (loop)':>14}  {'kary total':>12}  "
          f"{'sliding (precomp)':>20}  {'sliding (loop)':>16}  {'sliding total':>14}")
    print("  " + "-" * 100)

    for k in range(1, 11):
        # k-ary: el tamaño de tabla es 2^k, precomputación = 2^k - 2 muls
        precomp_kary = max(0, (1 << k) - 2)
        c1 = OpCounter()
        kary_modexp(a, b, n, k=k, counter=c1)
        loop_kary = c1.total - precomp_kary

        # sliding: precomputación = 1 sqr + (2^(k-1) - 1) mul = 2^(k-1) ops si k≥1
        precomp_sliding = (1 << (k - 1)) if k > 1 else 0
        c2 = OpCounter()
        sliding_window_modexp(a, b, n, k=k, counter=c2)
        loop_sliding = c2.total - precomp_sliding

        print(f"  {k:>3}  {precomp_kary:>16}  {loop_kary:>14}  {c1.total:>12}  "
              f"{precomp_sliding:>20}  {loop_sliding:>16}  {c2.total:>14}")
    print()


def demo_timing():
    """Compara tiempo de ejecución contra pow() nativo."""
    print("=" * 70)
    print("TIEMPO DE EJECUCIÓN (β = 1024 bits, 10 corridas, mediana en ms)")
    print("=" * 70)

    n = (random.getrandbits(1024) | (1 << 1023)) | 1
    a = random.randrange(0, n)
    b = random.getrandbits(1024)

    def time_it(fn, *args, **kwargs):
        times = []
        for _ in range(10):
            t0 = time.perf_counter()
            fn(*args, **kwargs)
            times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        return times[len(times) // 2]

    print(f"  {'algoritmo':<22} {'tiempo (ms)':>14}")
    print(f"  {'-'*22} {'-'*14}")
    print(f"  {'pow() de Python':<22} {time_it(pow, a, b, n):>14.3f}")
    print(f"  {'binary_lr':<22} {time_it(binary_lr_modexp, a, b, n):>14.3f}")
    print(f"  {'binary_rl':<22} {time_it(binary_rl_modexp, a, b, n):>14.3f}")
    print(f"  {'kary k=6':<22} {time_it(kary_modexp, a, b, n, k=6):>14.3f}")
    print(f"  {'sliding k=6':<22} {time_it(sliding_window_modexp, a, b, n, k=6):>14.3f}")
    print()
    print("  Nota: pow() está implementado en C; los algoritmos puros en")
    print("  Python serán órdenes de magnitud más lentos en tiempo absoluto,")
    print("  pero el conteo de multiplicaciones modulares sigue siendo el")
    print("  análisis de complejidad relevante.")
    print()


if __name__ == "__main__":
    demo_cormen_example()
    demo_scaling()
    demo_window_sweep()
    demo_timing()
