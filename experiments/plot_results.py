"""
plot_results.py
===============

Genera las figuras del informe a partir de los CSVs producidos por
`run_experiments.py`. Las figuras se guardan en `results/figures/` en
formato PNG (para preview) y PDF (para incluir en LaTeX).

Uso:
    python experiments/plot_results.py
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import pandas as pd


RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True, parents=True)


# Esquema de colores y marcadores coherente entre todas las figuras
STYLES = {
    "naive":       {"color": "#d62728", "marker": "x", "label": "Ingenuo"},
    "binary_lr":   {"color": "#1f77b4", "marker": "o", "label": "Binario L→R"},
    "binary_rl":   {"color": "#ff7f0e", "marker": "s", "label": "Binario R→L"},
    "kary":        {"color": "#2ca02c", "marker": "^", "label": "k-aria fija"},
    "sliding":     {"color": "#9467bd", "marker": "D", "label": "Ventana deslizante"},
    "pow_builtin": {"color": "#7f7f7f", "marker": "*", "label": "pow() nativo (C)"},
}


def _save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / f"{name}.png", dpi=150, bbox_inches="tight")
    fig.savefig(FIGURES_DIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"    → {name}.png + {name}.pdf")


# ---------------------------------------------------------------------------
# Figura 1: Escalabilidad
# ---------------------------------------------------------------------------

def plot_scaling() -> None:
    csv_path = RESULTS_DIR / "scaling.csv"
    if not csv_path.exists():
        print(f"    (saltada: {csv_path} no existe)")
        return
    df = pd.read_csv(csv_path)
    agg = df.groupby(["bit_size", "algorithm", "k"], dropna=False).agg(
        mean_ops=("total_ops", "mean"),
        mean_mul=("multiplications", "mean"),
        mean_sqr=("squarings", "mean"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(9, 6))

    # Métodos sin parámetro k
    for algo in ["naive", "binary_lr", "binary_rl"]:
        sub = agg[(agg["algorithm"] == algo) & (agg["k"].isna() | (agg["k"] == ""))]
        if len(sub) == 0:
            continue
        st = STYLES[algo]
        ax.plot(sub["bit_size"], sub["mean_ops"],
                marker=st["marker"], color=st["color"], label=st["label"],
                markersize=8, linewidth=1.5)

    # Métodos con ventana (mostramos k=6 representativo)
    for algo in ["kary", "sliding"]:
        sub = agg[(agg["algorithm"] == algo) & (agg["k"] == 6)]
        if len(sub) == 0:
            continue
        st = STYLES[algo]
        ax.plot(sub["bit_size"], sub["mean_ops"],
                marker=st["marker"], color=st["color"], label=f"{st['label']} (k=6)",
                markersize=8, linewidth=1.5)

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=10)
    ax.set_xlabel(r"$\beta$ (bits del exponente)")
    ax.set_ylabel("Operaciones modulares (cuadrados + multiplicaciones)")
    ax.set_title("Figura 1. Escalabilidad: operaciones vs. tamaño del exponente")
    ax.legend(loc="best", framealpha=0.9)
    ax.grid(True, which="both", alpha=0.3)

    _save(fig, "fig1_scaling")


# ---------------------------------------------------------------------------
# Figura 2: Tamaño de ventana
# ---------------------------------------------------------------------------

def plot_window_size() -> None:
    csv_path = RESULTS_DIR / "window_size.csv"
    if not csv_path.exists():
        print(f"    (saltada: {csv_path} no existe)")
        return
    df = pd.read_csv(csv_path)
    bit_size = int(df["bit_size"].iloc[0])
    agg = df.groupby(["k", "algorithm"]).agg(
        mean_ops=("total_ops", "mean"),
        mean_mul=("multiplications", "mean"),
        mean_sqr=("squarings", "mean"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(9, 6))
    for algo in ["kary", "sliding"]:
        sub = agg[agg["algorithm"] == algo].sort_values("k")
        st = STYLES[algo]
        ax.plot(sub["k"], sub["mean_ops"],
                marker=st["marker"], color=st["color"], label=st["label"],
                markersize=9, linewidth=1.8)

    # Marca el k óptimo teórico
    k_opt = math.log2(bit_size) - math.log2(math.log2(bit_size))
    ax.axvline(k_opt, color="gray", linestyle="--", alpha=0.6,
               label=fr"$k_{{opt}}$ teórico ≈ {k_opt:.1f}")

    # Resalta los mínimos empíricos
    for algo in ["kary", "sliding"]:
        sub = agg[agg["algorithm"] == algo].sort_values("k")
        idx_min = sub["mean_ops"].idxmin()
        k_min = int(sub.loc[idx_min, "k"])
        ops_min = sub.loc[idx_min, "mean_ops"]
        ax.annotate(f"k={k_min}\n{ops_min:.0f} ops",
                    xy=(k_min, ops_min),
                    xytext=(10, -25), textcoords="offset points",
                    fontsize=9, color=STYLES[algo]["color"],
                    arrowprops=dict(arrowstyle="->", color=STYLES[algo]["color"]))

    ax.set_xlabel("k (tamaño de ventana en bits)")
    ax.set_ylabel("Operaciones modulares totales (promedio)")
    ax.set_title(fr"Figura 2. Efecto del tamaño de ventana ($\beta$ = {bit_size} bits)")
    ax.set_xticks(range(1, 11))
    ax.legend()
    ax.grid(True, alpha=0.3)

    _save(fig, "fig2_window_size")


# ---------------------------------------------------------------------------
# Figura 3: Tiempo de ejecución
# ---------------------------------------------------------------------------

def plot_timing() -> None:
    csv_path = RESULTS_DIR / "timing.csv"
    if not csv_path.exists():
        print(f"    (saltada: {csv_path} no existe)")
        return
    df = pd.read_csv(csv_path)
    agg = df.groupby(["bit_size", "algorithm", "k"], dropna=False).agg(
        median_time=("time_seconds", "median"),
    ).reset_index()
    agg["time_ms"] = agg["median_time"] * 1000

    fig, ax = plt.subplots(figsize=(9, 6))

    for algo in ["pow_builtin", "binary_lr", "binary_rl"]:
        sub = agg[(agg["algorithm"] == algo) & (agg["k"].isna() | (agg["k"] == ""))]
        if len(sub) == 0:
            continue
        st = STYLES[algo]
        ax.plot(sub["bit_size"], sub["time_ms"],
                marker=st["marker"], color=st["color"], label=st["label"],
                markersize=8, linewidth=1.5)

    for algo in ["kary", "sliding"]:
        sub = agg[(agg["algorithm"] == algo) & (agg["k"] == 6)]
        if len(sub) == 0:
            continue
        st = STYLES[algo]
        ax.plot(sub["bit_size"], sub["time_ms"],
                marker=st["marker"], color=st["color"], label=f"{st['label']} (k=6)",
                markersize=8, linewidth=1.5)

    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=10)
    ax.set_xlabel(r"$\beta$ (bits del exponente)")
    ax.set_ylabel("Tiempo de ejecución (ms, mediana)")
    ax.set_title("Figura 3. Tiempo de ejecución vs. tamaño del exponente")
    ax.legend(loc="best")
    ax.grid(True, which="both", alpha=0.3)

    _save(fig, "fig3_timing")


# ---------------------------------------------------------------------------
# Figura 4: Peso de Hamming
# ---------------------------------------------------------------------------

def plot_hamming() -> None:
    csv_path = RESULTS_DIR / "hamming.csv"
    if not csv_path.exists():
        print(f"    (saltada: {csv_path} no existe)")
        return
    df = pd.read_csv(csv_path)
    bit_size = int(df["bit_size"].iloc[0])
    agg = df.groupby(["hamming_weight", "algorithm", "k"], dropna=False).agg(
        mean_ops=("total_ops", "mean"),
        mean_mul=("multiplications", "mean"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(9, 6))

    for algo in ["binary_lr", "binary_rl"]:
        sub = agg[(agg["algorithm"] == algo) & (agg["k"].isna() | (agg["k"] == ""))]
        st = STYLES[algo]
        ax.plot(sub["hamming_weight"], sub["mean_ops"],
                marker=st["marker"], color=st["color"], label=st["label"],
                markersize=8, linewidth=1.5)

    for algo in ["kary", "sliding"]:
        sub = agg[(agg["algorithm"] == algo) & (agg["k"] == 6)]
        st = STYLES[algo]
        ax.plot(sub["hamming_weight"], sub["mean_ops"],
                marker=st["marker"], color=st["color"], label=f"{st['label']} (k=6)",
                markersize=8, linewidth=1.5)

    ax.set_xlabel(fr"H(b) — peso de Hamming del exponente ($\beta$ = {bit_size})")
    ax.set_ylabel("Operaciones modulares (promedio)")
    ax.set_title("Figura 4. Sensibilidad al peso de Hamming del exponente")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    _save(fig, "fig4_hamming")


# ---------------------------------------------------------------------------
# Tabla resumen
# ---------------------------------------------------------------------------

def print_summary_tables() -> None:
    """Genera tablas en formato markdown que se pueden pegar en el informe."""
    out = []

    scaling_csv = RESULTS_DIR / "scaling.csv"
    if scaling_csv.exists():
        df = pd.read_csv(scaling_csv)
        # Promedios por algoritmo a tamaños representativos
        out.append("\n## Tabla 1. Operaciones promedio vs. β (selección)\n")
        sizes_of_interest = [64, 256, 1024, 2048, 4096]
        algos_of_interest = [
            ("binary_lr", None), ("binary_rl", None),
            ("kary", 6), ("sliding", 6),
        ]
        out.append("| β | " + " | ".join(
            f"{a}{' k='+str(k) if k else ''}" for a, k in algos_of_interest
        ) + " |")
        out.append("|---" * (1 + len(algos_of_interest)) + "|")
        for bs in sizes_of_interest:
            row = [f"{bs}"]
            for algo, k in algos_of_interest:
                if k is None:
                    sub = df[(df["bit_size"] == bs) & (df["algorithm"] == algo)]
                else:
                    sub = df[(df["bit_size"] == bs) & (df["algorithm"] == algo)
                             & (df["k"] == k)]
                if len(sub) > 0:
                    row.append(f"{sub['total_ops'].mean():.0f}")
                else:
                    row.append("—")
            out.append("| " + " | ".join(row) + " |")

    window_csv = RESULTS_DIR / "window_size.csv"
    if window_csv.exists():
        df = pd.read_csv(window_csv)
        bs = int(df["bit_size"].iloc[0])
        out.append(f"\n## Tabla 2. k óptimo empírico (β = {bs})\n")
        out.append("| k | kary | sliding |")
        out.append("|---|------|---------|")
        for k in range(1, 11):
            kary_mean = df[(df["algorithm"] == "kary") & (df["k"] == k)]["total_ops"].mean()
            sli_mean  = df[(df["algorithm"] == "sliding") & (df["k"] == k)]["total_ops"].mean()
            out.append(f"| {k} | {kary_mean:.0f} | {sli_mean:.0f} |")

    text = "\n".join(out)
    (RESULTS_DIR / "summary_tables.md").write_text(text, encoding="utf-8")
    print("    → summary_tables.md")
    print(text)


def main() -> None:
    print("Generando gráficas...")
    plot_scaling()
    plot_window_size()
    plot_timing()
    plot_hamming()
    print("\nTablas resumen:")
    print_summary_tables()
    print(f"\nTodas las figuras en: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
