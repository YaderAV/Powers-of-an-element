# Potencias de un Elemento módulo *n*

Proyecto final del curso **Algoritmos y Complejidad** — Universidad del Norte, 2026.
Capítulo de referencia: **31.6** de Cormen, *Introduction to Algorithms*, 4ª ed.
Integrantes: Enrique Peinado, Eliud Quiroz, Yader Vega

Implementación y comparación experimental de cinco algoritmos para calcular
$a^b \bmod n$:

| Método                                       | Multiplicaciones (promedio) | Cuadrados | Memoria      |
|----------------------------------------------|-----------------------------|-----------|--------------|
| Ingenuo                                      | $b$                         | 0         | $O(1)$       |
| Binario L→R (Cormen)                         | $\beta/2$                   | $\beta$   | $O(1)$       |
| Binario R→L (ej. 31.6-2)                     | $\beta/2$                   | $\beta$   | $O(1)$       |
| Ventana fija $k$-aria                        | $\beta/k + 2^k - 2$         | $\beta$   | $O(2^k)$     |
| Ventana deslizante                           | $\beta/(k+1) + 2^{k-1}$     | $\beta$   | $O(2^{k-1})$ |

donde $\beta = \lfloor\log_2 b\rfloor + 1$ es el número de bits del exponente.

## Estructura del repositorio

```
modexp/
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py          # API pública del paquete
│   ├── core.py              # Clase OpCounter (instrumentación)
│   ├── naive.py             # Algoritmo 1: multiplicación iterada
│   ├── binary_lr.py         # Algoritmo 2: cuadrados repetidos L→R (Cormen)
│   ├── binary_rl.py         # Algoritmo 3: cuadrados repetidos R→L
│   ├── kary.py              # Algoritmo 4: ventana fija k-aria
│   └── sliding.py           # Algoritmo 5: ventana deslizante
├── tests/
│   └── test_correctness.py  # Suite pytest (177 tests)
├── experiments/
│   ├── run_experiments.py   # Genera 4 CSVs con resultados
│   ├── plot_results.py      # Genera figuras a partir de los CSVs
│   └── HARDWARE.md          # Guía de configuración del entorno experimental
├── results/                 # CSVs, figuras y system_info.txt (gitignored)
└── demo.py                  # Demostración interactiva
```

## Requisitos

- Python 3.11 o superior (uso de sintaxis `int | None`).
- `pytest` para correr los tests.
- Opcionalmente `matplotlib`, `pandas` y `numpy` para la fase experimental.

Instalación:

```bash
pip install -r requirements.txt
```

## Uso rápido

```python
from src import binary_lr_modexp, sliding_window_modexp, OpCounter

# Cálculo simple
print(binary_lr_modexp(7, 560, 561))  # 1 (Cormen Fig 31.4)

# Con contador de operaciones
c = OpCounter()
sliding_window_modexp(7, 560, 561, k=4, counter=c)
print(c.snapshot())  # {'multiplications': 8, 'squarings': 10, 'total': 18}
```

## Ejecutar los tests

Desde la raíz del proyecto:

```bash
python -m pytest tests/ -v
```

Resultado esperado: **177 tests pasados**. Los tests verifican:

- Casos borde ($b=0$, $b=1$, $a=0$, $n=1$, ejemplo de Cormen).
- Comparación contra `pow(a, b, n)` para exponentes de 8 a 1024 bits.
- Conteo exacto de operaciones contra los valores predichos por la teoría.
- Consistencia cruzada: todos los algoritmos dan el mismo resultado.

## Ejecutar la demostración

```bash
python demo.py
```

Muestra:
1. El ejemplo $7^{560} \bmod 561$ de Cormen con los conteos de cada algoritmo.
2. Tabla de escalabilidad para exponentes de 64 a 2048 bits.
3. Efecto del parámetro $k$ en los métodos de ventana.
4. Comparación de tiempo contra `pow()` nativo de CPython.

## Batería de experimentos

Para regenerar todos los datos y figuras del informe:

```bash
# Genera los CSVs en results/
python experiments/run_experiments.py            # ~25-35 min en hardware típico
python experiments/run_experiments.py --quick    # ~1 min, muestras reducidas

# Genera las gráficas (PNG y PDF) en results/figures/
python experiments/plot_results.py
```

Cinco experimentos se ejecutan en orden:

1. **scaling** — operaciones vs. tamaño del exponente β ∈ {8, 16, ..., 4096}.
2. **window_size** — operaciones vs. k para β fijo (2048 bits).
3. **timing** — tiempo de ejecución vs. β, incluyendo `pow()` como referencia.
4. **hamming** — efecto del peso de Hamming H(b) sobre el conteo.
5. **special_exponents** — Compara el conteo de operaciones para exponentes con estructura especial vs. exponentes aleatorios del mismo tamaño en bits.

Cada experimento se puede correr aisladamente con `--experiment <nombre>`.
Todos los archivos producidos quedan en `results/` y el sistema captura
automáticamente la info de hardware en `results/system_info.txt`.


## Reproducibilidad

Todas las pruebas usan `random.seed(2026)`. La misma semilla produce
exactamente los mismos casos de prueba en cualquier máquina con la
misma versión de Python. El demo también es determinista.

## Referencias

1. Cormen, Leiserson, Rivest y Stein (2022). *Introduction to Algorithms*, 4ª ed., MIT Press. Capítulo 31, §31.6.
2. Menezes, van Oorschot y Vanstone (1996). *Handbook of Applied Cryptography*, CRC Press. Capítulo 14, §14.6.
3. Knuth (1997). *The Art of Computer Programming, Vol. 2*. Addison-Wesley. §4.6.3.

## Licencia

Uso académico — Universidad del Norte, 2026.
