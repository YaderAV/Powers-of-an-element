# HARDWARE.md — Decisiones y configuración del entorno experimental

## 1. Qué importa medir y qué no

Para este proyecto hay **dos métricas independientes** que se reportan
por separado, porque dependen de cosas distintas:

|                   Métrica                | ¿Depende del hardware? | ¿Determinista? |
|------------------------------------------|------------------------|----------------|
| Número de multiplicaciones modulares     | No                     | Sí             |
| Número de cuadrados modulares            | No                     | Sí             |
| Tiempo de ejecución                      | **Sí**                 | No (varianza)  |

Los conteos de operaciones son **deterministas** para una semilla fija y
no dependen de la máquina. Pueden reproducirse en cualquier laptop sin
preocuparse por nada. Lo que requiere cuidado es el **tiempo de
ejecución**, que sí depende de CPU, frecuencia, caché y carga del sistema.

**Implicación práctica:** las figuras 1, 2 y 4 (sobre conteos) son
inmutables. La figura 3 (tiempo) hay que correrla en condiciones
controladas y reportar el hardware.

---

## 2. Recomendación de hardware

**Lo único que se debe evitar:**
- Correr mientras se reproducen videos, hay descargas activas, o el
  navegador tiene muchas pestañas. La carga concurrente distorsiona los
  tiempos.
- Correr con la batería: muchos laptops bajan la frecuencia del CPU para
  ahorrar energía. **Conectar a la corriente siempre.**
- Modos "ahorro de energía" del sistema operativo. Configurar en modo
  "alto rendimiento" / "performance" mientras corren los experimentos.

---

## 3. Configuración recomendada antes de correr `timing`

1. Panel de control → Opciones de energía → Alto rendimiento.
2. Conectar el equipo a corriente.
3. Cerrar Slack, navegador, Spotify, etc.

- Reiniciar la máquina antes de empezar (caches limpios).
- Cerrar aplicaciones en segundo plano.
- Dejar el equipo cerrado o ejecutar los experimentos cuando nadie lo
  esté usando — los procesos del usuario activo introducen ruido.

---

## 4. Hardware usado en este proyecto

Fecha de las corridas: 25/05/2026
Integrante responsable: Yader Vega
CPU: Intel Core i5-12450HX
Frecuencia base / boost: 2.4 GHz / 4.40 GHz
Núcleos / hilos: 8/12
Caché L3: 12 MB
RAM: 23.7 GiB
Almacenamiento: SSD NVMe SAMSUNG MZAMX512HCLV - 00BL2
Sistema operativo: Windows-11-10.0.26200-SP0
Python: 3.14.5

---

## 5. Cómo lograr reproducibilidad estricta

- **Semilla aleatoria fija** (`random.seed(2026)` y `random.Random(2026)`
  en el runner) → las mismas ternas (a, b, n) se generan en cualquier
  máquina.
- Los conteos de operaciones son deterministas dada la semilla.
- Versión de las dependencias fijada en `requirements.txt`.

4. **Comando único de reproducción** en el README. Para este proyecto:

   ```bash
   pip install -r requirements.txt
   python -m pytest tests/ -v               # 177 tests pasan
   python experiments/run_experiments.py    # genera CSVs
   python experiments/plot_results.py       # genera figuras
   ```

5. **No editar CSVs a mano.** Si hace falta corregir algo, regenerar
   desde el script.

---

## 6. Cuánto tarda la batería completa

| Experimento | Muestras | Tiempo aprox. |
|---|---|---|
| scaling (default 20 samples, naive hasta 22 bits) | 20 | ~3–5 min |
| window_size (β=2048, 30 samples) | 30 | ~2 min |
| timing (β hasta 4096, 10 samples × 5 reps) | 10 | ~15–25 min |
| hamming (β=1024, 20 samples) | 20 | ~1 min |
| **Total** | | **~25–35 min** |

En modo `--quick` (5 muestras, naive hasta 16 bits, β máx. 1024 para
window): **< 1 minuto**. Útil para verificar que todo funciona antes
de la corrida final.

---

## 7. Si los tiempos varían mucho

Si al correr `timing` varias veces ven mucha varianza entre corridas
(p.ej. binary_lr a 1024 bits oscila entre 5 ms y 12 ms en runs
distintos), el problema típico es:

- **Thermal throttling**: el CPU se calienta y baja frecuencia.
  Solución: hacer pausas entre experimentos, o usar un escritorio.
- **Procesos en segundo plano**: cerrarlos.
- **Garbage collector de Python**: para timings muy precisos, se puede
  desactivar temporalmente con `gc.disable()` antes de la medición y
  `gc.enable()` después. No es crítico para este proyecto.
- **Frecuencia variable del CPU**: forzar governor "performance" (ver §3).

Si después de todo esto sigue habiendo varianza alta, **aumenten el
número de repeticiones** (parámetro `--samples`) y reporten **la
mediana** en lugar del promedio. La mediana es robusta a outliers.

---

## 8. Para el informe (§5.3)

Sugerencia de redacción:

> Los experimentos se ejecutaron en una máquina con CPU [modelo],
> [N] núcleos a [F] GHz, [R] GiB de RAM, ejecutando [SO] y Python [V].
> Durante las corridas, el sistema operativo se configuró en modo de
> alto rendimiento, el equipo permaneció conectado a corriente, y se
> cerraron las aplicaciones en segundo plano. Cada punto de tiempo se
> obtuvo como la mediana de [k] corridas independientes, precedidas
> por una corrida de calentamiento descartada. Los conteos de operaciones
> son deterministas para la semilla aleatoria fija (`random.seed(2026)`)
> y reproducibles en cualquier hardware.
