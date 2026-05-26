"""
Paquete `src` — Implementaciones de exponenciación modular.

Algoritmos disponibles:
  - naive_modexp:           multiplicación iterada O(b).
  - binary_lr_modexp:       cuadrados repetidos L→R (Cormen §31.6).
  - binary_rl_modexp:       cuadrados repetidos R→L (Cormen ej. 31.6-2).
  - kary_modexp:            ventana fija de k bits.
  - sliding_window_modexp:  ventana deslizante de hasta k bits.

Utilidad:
  - OpCounter:              instrumentación del número de operaciones.
"""

from .core import OpCounter
from .naive import naive_modexp
from .binary_lr import binary_lr_modexp
from .binary_rl import binary_rl_modexp
from .kary import kary_modexp
from .sliding import sliding_window_modexp

__all__ = [
    "OpCounter",
    "naive_modexp",
    "binary_lr_modexp",
    "binary_rl_modexp",
    "kary_modexp",
    "sliding_window_modexp",
]

# Diccionario útil para iterar sobre todos los algoritmos en experimentos.
ALGORITHMS = {
    "naive": naive_modexp,
    "binary_lr": binary_lr_modexp,
    "binary_rl": binary_rl_modexp,
    "kary": kary_modexp,
    "sliding": sliding_window_modexp,
}
