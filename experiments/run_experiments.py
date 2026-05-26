"""
run_experiments.py
==================

Batería de experimentos para el proyecto de exponenciación modular.

Ejecutar todos los experimentos con muestras por defecto:

    python experiments/run_experiments.py

Modo rápido (muestras reducidas, ~1 min):

    python experiments/run_experiments.py --quick

Un solo experimento:

    python experiments/run_experiments.py --experiment scaling

Salida: archivos CSV en `results/` y `system_info.txt` con detalles del
hardware donde se corrió. Todo es determinista (semilla fija).
"""

import argparse
import csv
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path

# Permite ejecutar el script sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (
    OpCounter,
    binary_lr_modexp,
    binary_rl_modexp,
    kary_modexp,
    naive_modexp,
    sliding_window_modexp,
)


# ---------------------------------------------------------------------------
# Utilidades comunes
# ---------------------------------------------------------------------------

def random_case(bit_size: int, rng: random.Random) -> tuple[int, int, int]:
    """Genera una terna (a, b, n) con b y n de bit_size bits."""
    n = (rng.getrandbits(bit_size) | (1 << (bit_size - 1))) | 1  # impar, msb fijado
    a = rng.randrange(0, n)
    b = rng.getrandbits(bit_size) | (1 << (bit_size - 1))        # msb fijado
    return a, b, n


def time_call(fn, *args, repetitions: int = 5, warmup: int = 1, **kwargs) -> float:
    """Mide un call repetidamente, devuelve la mediana en segundos."""
    for _ in range(warmup):
        fn(*args, **kwargs)
    times = []
    for _ in range(repetitions):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"    → {path}  ({len(rows)} filas)")


# ---------------------------------------------------------------------------
# Experimento 1 — Escalabilidad
# ---------------------------------------------------------------------------

def experiment_scaling(
    output_path: Path,
    samples: int = 20,
    naive_max_bits: int = 22,
    seed: int = 2026,
) -> None:
    """
    Mide número de multiplicaciones y cuadrados vs. tamaño del exponente.

    El método ingenuo se incluye solo hasta `naive_max_bits` porque a
    partir de ahí se vuelve prohibitivamente lento.
    """
    rng = random.Random(seed)
    bit_sizes = [8, 16, 24, 32, 64, 128, 256, 512, 1024, 2048, 4096]

    rows = []
    for bs in bit_sizes:
        for sample_idx in range(samples):
            a, b, n = random_case(bs, rng)

            def record(algo_name, k_param, counter):
                rows.append({
                    "bit_size": bs,
                    "algorithm": algo_name,
                    "k": k_param if k_param is not None else "",
                    "sample": sample_idx,
                    "multiplications": counter.multiplications,
                    "squarings": counter.squarings,
                    "total_ops": counter.total,
                })

            # Naive solo para exponentes pequeños
            if bs <= naive_max_bits:
                c = OpCounter()
                naive_modexp(a, b, n, counter=c)
                record("naive", None, c)

            # Métodos binarios (siempre)
            for name, fn in [
                ("binary_lr", binary_lr_modexp),
                ("binary_rl", binary_rl_modexp),
            ]:
                c = OpCounter()
                fn(a, b, n, counter=c)
                record(name, None, c)

            # Métodos con ventana para varios k
            for k in [2, 4, 6, 8]:
                for name, fn in [
                    ("kary", kary_modexp),
                    ("sliding", sliding_window_modexp),
                ]:
                    c = OpCounter()
                    fn(a, b, n, k=k, counter=c)
                    record(name, k, c)

        if bs >= 1024:
            print(f"    bit_size={bs} terminado ({samples} muestras)")

    write_csv(
        output_path,
        ["bit_size", "algorithm", "k", "sample",
         "multiplications", "squarings", "total_ops"],
        rows,
    )


# ---------------------------------------------------------------------------
# Experimento 2 — Tamaño de ventana
# ---------------------------------------------------------------------------

def experiment_window_size(
    output_path: Path,
    bit_size: int = 2048,
    samples: int = 30,
    seed: int = 2026,
) -> None:
    """Para β fijo, explora el efecto del parámetro k."""
    rng = random.Random(seed)

    rows = []
    for sample_idx in range(samples):
        a, b, n = random_case(bit_size, rng)
        for k in range(1, 11):
            for name, fn in [
                ("kary", kary_modexp),
                ("sliding", sliding_window_modexp),
            ]:
                c = OpCounter()
                fn(a, b, n, k=k, counter=c)
                rows.append({
                    "bit_size": bit_size,
                    "algorithm": name,
                    "k": k,
                    "sample": sample_idx,
                    "multiplications": c.multiplications,
                    "squarings": c.squarings,
                    "total_ops": c.total,
                })

    write_csv(
        output_path,
        ["bit_size", "algorithm", "k", "sample",
         "multiplications", "squarings", "total_ops"],
        rows,
    )


# ---------------------------------------------------------------------------
# Experimento 3 — Tiempo de ejecución
# ---------------------------------------------------------------------------

def experiment_timing(
    output_path: Path,
    samples: int = 10,
    repetitions: int = 5,
    seed: int = 2026,
) -> None:
    """Mide tiempo en muro vs. tamaño del exponente."""
    rng = random.Random(seed)
    bit_sizes = [64, 128, 256, 512, 1024, 2048, 4096]

    rows = []
    for bs in bit_sizes:
        for sample_idx in range(samples):
            a, b, n = random_case(bs, rng)

            def record(algo_name, k_param, t):
                rows.append({
                    "bit_size": bs,
                    "algorithm": algo_name,
                    "k": k_param if k_param is not None else "",
                    "sample": sample_idx,
                    "time_seconds": t,
                })

            # pow() nativo de CPython como referencia
            t = time_call(pow, a, b, n, repetitions=repetitions)
            record("pow_builtin", None, t)

            # Métodos binarios
            for name, fn in [
                ("binary_lr", binary_lr_modexp),
                ("binary_rl", binary_rl_modexp),
            ]:
                t = time_call(fn, a, b, n, repetitions=repetitions)
                record(name, None, t)

            # Métodos con ventana en varios k
            for k in [4, 6, 8]:
                for name, fn in [
                    ("kary", kary_modexp),
                    ("sliding", sliding_window_modexp),
                ]:
                    t = time_call(fn, a, b, n, k=k, repetitions=repetitions)
                    record(name, k, t)

        print(f"    bit_size={bs} terminado")

    write_csv(
        output_path,
        ["bit_size", "algorithm", "k", "sample", "time_seconds"],
        rows,
    )


# ---------------------------------------------------------------------------
# Experimento 4 — Peso de Hamming
# ---------------------------------------------------------------------------

def gen_exponent_with_weight(weight: int, bit_size: int, rng: random.Random) -> int:
    """Genera un entero con bit_size bits que contiene exactamente `weight` unos."""
    if weight == 0:
        return 0
    if weight > bit_size:
        raise ValueError("weight no puede exceder bit_size")
    # Forzamos el MSB para garantizar exactamente bit_size bits
    other_positions = list(range(bit_size - 1))
    rng.shuffle(other_positions)
    chosen = other_positions[:weight - 1]
    b = (1 << (bit_size - 1))
    for p in chosen:
        b |= (1 << p)
    return b


def experiment_hamming(
    output_path: Path,
    bit_size: int = 1024,
    samples: int = 20,
    seed: int = 2026,
) -> None:
    """
    Mide cómo el peso de Hamming H(b) afecta el conteo de operaciones.

    Los métodos binarios deberían escalar lineal con H(b) en el conteo
    de multiplicaciones; los de ventana son más estables.
    """
    rng = random.Random(seed)
    weights = [1, 50, 100, 200, 400, 512, 700, 900, 1024]

    rows = []
    for w in weights:
        for sample_idx in range(samples):
            n = (rng.getrandbits(bit_size) | (1 << (bit_size - 1))) | 1
            a = rng.randrange(0, n)
            b = gen_exponent_with_weight(w, bit_size, rng)

            def record(algo_name, k_param, counter):
                rows.append({
                    "bit_size": bit_size,
                    "hamming_weight": w,
                    "algorithm": algo_name,
                    "k": k_param if k_param is not None else "",
                    "sample": sample_idx,
                    "multiplications": counter.multiplications,
                    "squarings": counter.squarings,
                    "total_ops": counter.total,
                })

            for name, fn in [
                ("binary_lr", binary_lr_modexp),
                ("binary_rl", binary_rl_modexp),
            ]:
                c = OpCounter()
                fn(a, b, n, counter=c)
                record(name, None, c)

            for k in [4, 6]:
                for name, fn in [
                    ("kary", kary_modexp),
                    ("sliding", sliding_window_modexp),
                ]:
                    c = OpCounter()
                    fn(a, b, n, k=k, counter=c)
                    record(name, k, c)

    write_csv(
        output_path,
        ["bit_size", "hamming_weight", "algorithm", "k", "sample",
         "multiplications", "squarings", "total_ops"],
        rows,
    )


# ---------------------------------------------------------------------------
# Captura de información del sistema
# ---------------------------------------------------------------------------

def capture_system_info(output_path: Path) -> None:
    """Guarda detalles del entorno para reproducibilidad."""
    lines = [
        f"Fecha:               {time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"Python:              {sys.version.split()[0]}",
        f"Plataforma:          {platform.platform()}",
        f"Arquitectura:        {platform.machine()}",
        f"Procesador:          {platform.processor() or 'desconocido'}",
        f"CPU lógicos:         {os.cpu_count()}",
    ]
    try:
        import psutil  # opcional
        freq = psutil.cpu_freq()
        if freq:
            lines.append(f"Frecuencia CPU:      {freq.current:.0f} MHz "
                         f"(min {freq.min:.0f} / max {freq.max:.0f})")
        mem = psutil.virtual_memory()
        lines.append(f"RAM total:           {mem.total / 1024**3:.1f} GiB")
    except ImportError:
        lines.append("Frecuencia CPU:      psutil no instalado (pip install psutil)")

    # En Linux, leer info adicional desde /proc
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    lines.append(f"Modelo de CPU:       {line.split(':',1)[1].strip()}")
                    break
    except FileNotFoundError:
        pass

    text = "\n".join(lines) + "\n"
    output_path.write_text(text)
    print(f"    → {output_path}")
    for line in lines:
        print(f"      {line}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment",
        choices=["scaling", "window", "timing", "hamming", "all"],
        default="all",
    )
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--quick", action="store_true",
                        help="Muestras reducidas y tamaños menores")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--results-dir", default=None)
    args = parser.parse_args()

    if args.results_dir:
        results_dir = Path(args.results_dir)
    else:
        results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True, parents=True)

    samples = 5 if args.quick else args.samples
    naive_max = 16 if args.quick else 22

    print("=" * 72)
    print("BATERÍA DE EXPERIMENTOS — Exponenciación modular")
    print("=" * 72)
    print(f"Semilla:                {args.seed}")
    print(f"Muestras por punto:     {samples}")
    print(f"Directorio de salida:   {results_dir}")
    if args.quick:
        print("MODO RÁPIDO activado.")
    print()

    print("[0/4] Información del sistema")
    capture_system_info(results_dir / "system_info.txt")
    print()

    if args.experiment in ("scaling", "all"):
        print("[1/4] Experimento de escalabilidad...")
        experiment_scaling(
            results_dir / "scaling.csv",
            samples=samples,
            seed=args.seed,
            naive_max_bits=naive_max,
        )
        print()

    if args.experiment in ("window", "all"):
        print("[2/4] Experimento de tamaño de ventana...")
        experiment_window_size(
            results_dir / "window_size.csv",
            bit_size=1024 if args.quick else 2048,
            samples=samples,
            seed=args.seed,
        )
        print()

    if args.experiment in ("timing", "all"):
        print("[3/4] Experimento de tiempo de ejecución...")
        experiment_timing(
            results_dir / "timing.csv",
            samples=max(3, samples // 2),
            repetitions=3 if args.quick else 5,
            seed=args.seed,
        )
        print()

    if args.experiment in ("hamming", "all"):
        print("[4/4] Experimento de peso de Hamming...")
        experiment_hamming(
            results_dir / "hamming.csv",
            bit_size=1024,
            samples=samples,
            seed=args.seed,
        )
        print()

    print("Listo. Para generar gráficas:")
    print("    python experiments/plot_results.py")


if __name__ == "__main__":
    main()
