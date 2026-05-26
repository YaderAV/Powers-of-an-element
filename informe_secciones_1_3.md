# Informe técnico — secciones 1, 2 y 3 (prosa redactada)

> Este archivo contiene la prosa lista para las secciones teóricas del
> informe. Está pensado para integrarse al outline general
> (`outline_informe.md`) sustituyendo las marcas `[REDACTAR]` de §1, §2
> y §3 por el contenido que aquí aparece. La notación matemática usa
> sintaxis LaTeX para poder convertirlo a Overleaf o pandoc-LaTeX
> directamente.

---

## 1. Introducción

### 1.1 Motivación

La exponenciación modular —el cálculo de $a^b \bmod n$ para enteros
$a$, $b$ y $n$— es una de las operaciones más recurrentes en la
criptografía contemporánea. El criptosistema RSA depende de ella en
cada operación de cifrado y descifrado: tanto el texto en claro como
el texto cifrado se obtienen elevando al exponente público (o privado)
módulo un compuesto $n = pq$ del orden de $2^{2048}$ o más. La misma
operación es la primitiva fundamental del intercambio de claves
Diffie–Hellman, del esquema de firma DSA y del test probabilístico de
primalidad de Miller–Rabin (Cormen et al., 2022, §31.8).

Lo que vuelve este problema interesante desde el punto de vista
algorítmico es que **no se puede resolver ingenuamente**. El número
$a^b$, evaluado sin reducción intermedia, tiene aproximadamente
$b \log_2 a$ bits; para un exponente de $2048$ bits y una base del
mismo orden, ese entero ocuparía más memoria que átomos hay en el
universo observable. Incluso si la memoria no fuera obstáculo,
multiplicar $a$ por sí mismo $b - 1$ veces requiere $b - 1$
operaciones aritméticas, y para $b \approx 2^{2048}$ esto excede en
muchos órdenes de magnitud la edad del universo expresada en
nanosegundos. La única forma de hacer factible la operación es
combinar dos ideas: (i) reducir módulo $n$ tras cada multiplicación,
manteniendo los operandos acotados por $n^2$; y (ii) explotar la
representación binaria de $b$ para reducir el número de
multiplicaciones de $O(b)$ a $O(\log b)$.

Sobre esta idea base hay variantes que reducen aún más el conteo
de multiplicaciones a expensas de memoria y precomputación: los
métodos de *ventana fija* y *ventana deslizante*. El propósito del
presente trabajo es implementar y comparar empíricamente cinco
variantes de exponenciación modular, cuantificar su costo en
términos del número de multiplicaciones y cuadrados modulares, e
identificar el régimen en que cada una es preferible.

### 1.2 Objetivos

**Objetivo general.** Implementar y caracterizar experimentalmente
cinco algoritmos para el cálculo de $a^b \bmod n$, contrastando su
desempeño teórico con mediciones empíricas en exponentes de tamaño
criptográfico.

**Objetivos específicos.**

1. Implementar los métodos ingenuo, de cuadrados repetidos en sus
   versiones de izquierda a derecha y derecha a izquierda, de ventana
   fija $k$-aria y de ventana deslizante, instrumentando cada uno con
   un contador separado para multiplicaciones y cuadrados modulares.
2. Validar la correctitud de las implementaciones mediante una suite
   de pruebas comparativas contra la función nativa `pow` de CPython.
3. Caracterizar empíricamente la dependencia del número de
   operaciones respecto al tamaño del exponente $\beta$ y, en los
   métodos de ventana, respecto al parámetro $k$.
4. Identificar el tamaño de ventana empíricamente óptimo y
   contrastarlo con la predicción teórica.
5. Analizar el impacto del peso de Hamming del exponente sobre el
   conteo de operaciones, factor relevante para implementaciones
   criptográficas seguras contra ataques de canal lateral.

### 1.3 Estructura del documento

La sección 2 establece el marco teórico necesario para los
algoritmos: grupos multiplicativos modulares, orden de un elemento,
los teoremas de Euler y Fermat y el concepto de raíz primitiva. La
sección 3 presenta los cinco algoritmos con su pseudocódigo y un
análisis del costo en multiplicaciones. La sección 4 describe la
implementación. La sección 5 detalla la metodología experimental, la
sección 6 reporta y discute los resultados, y la sección 7 ofrece las
conclusiones.

---

## 2. Marco teórico

Todo el aparato matemático que se presenta a continuación proviene
del capítulo 31 de Cormen, Leiserson, Rivest y Stein (2022). Las
referencias específicas se indican mediante el número del teorema o
corolario tal y como aparece en la obra.

### 2.1 Aritmética modular y el grupo $\mathbb{Z}_n^*$

Sea $n > 1$ un entero. El conjunto $\mathbb{Z}_n = \{0, 1, \dots, n - 1\}$
dotado de las operaciones suma y multiplicación módulo $n$ es un
anillo conmutativo. El subconjunto

$$
\mathbb{Z}_n^* = \{a \in \mathbb{Z}_n : \gcd(a, n) = 1\}
$$

es precisamente el conjunto de elementos *invertibles* respecto a la
multiplicación módulo $n$: un elemento $a \in \mathbb{Z}_n$ posee
inverso multiplicativo módulo $n$ si y sólo si es coprimo con $n$.
$\mathbb{Z}_n^*$ forma un **grupo abeliano finito** bajo la
multiplicación módulo $n$, con elemento neutro $1$.

La cardinalidad de este grupo está dada por la función phi de Euler:

$$
\phi(n) = |\mathbb{Z}_n^*|.
$$

Dos identidades de $\phi$ resultan especialmente útiles en
criptografía. Primero, si $p$ es primo entonces todo elemento no nulo
de $\mathbb{Z}_p$ es invertible, así que $\phi(p) = p - 1$. Segundo,
si $n = pq$ es producto de dos primos distintos —situación canónica
de RSA— entonces $\phi(n) = (p - 1)(q - 1)$.

### 2.2 Sucesión de potencias, subgrupo generado y orden

Dado $a \in \mathbb{Z}_n^*$, la sucesión

$$
a^0, a^1, a^2, a^3, \dots \pmod{n} \tag{31.33 de Cormen}
$$

toma valores en $\mathbb{Z}_n^*$ y, por la finitud de este conjunto,
es eventualmente periódica. Como ejemplo, las potencias de $3$ módulo
$7$ se repiten con periodo $6$:

| $i$ | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| $3^i \bmod 7$ | 1 | 3 | 2 | 6 | 4 | 5 | 1 | 3 | 2 |

mientras que las de $2$ tienen periodo $3$: $1, 2, 4, 1, 2, 4, \dots$

El conjunto de valores que toma esta sucesión,

$$
\langle a \rangle = \{a^i \bmod n : i \geq 0\},
$$

es un subgrupo cíclico de $\mathbb{Z}_n^*$. El **orden de $a$ módulo
$n$**, denotado $\operatorname{ord}_n(a)$, se define como el menor
entero positivo $k$ tal que $a^k \equiv 1 \pmod n$, y coincide con el
cardinal $|\langle a \rangle|$. En el ejemplo anterior,
$\operatorname{ord}_7(3) = 6$ y $\operatorname{ord}_7(2) = 3$.

Por el teorema de Lagrange aplicado al grupo finito $\mathbb{Z}_n^*$,
todo orden divide al orden del grupo:

$$
\operatorname{ord}_n(a) \mid \phi(n).
$$

### 2.3 Teorema de Euler y pequeño teorema de Fermat

Una consecuencia inmediata del teorema de Lagrange es que cualquier
elemento de $\mathbb{Z}_n^*$, elevado a $\phi(n)$, devuelve el
neutro.

> **Teorema 31.30 (Euler).** Sea $n > 1$. Entonces, para todo
> $a \in \mathbb{Z}_n^*$,
> $$a^{\phi(n)} \equiv 1 \pmod n.$$

Cuando $n$ es primo, $\phi(n) = n - 1$, y se obtiene como caso
particular el resultado clásico de Fermat.

> **Teorema 31.31 (Pequeño teorema de Fermat).** Si $p$ es primo,
> entonces $a^{p-1} \equiv 1 \pmod p$ para todo $a \in \mathbb{Z}_p^*$.

Estos dos teoremas tienen una implicación operativa central para los
algoritmos de exponenciación modular y, en particular, para RSA:
**los exponentes pueden reducirse módulo $\phi(n)$** siempre que
$\gcd(a, n) = 1$. En otras palabras, calcular $a^b \bmod n$ equivale a
calcular $a^{b \bmod \phi(n)} \bmod n$. La dificultad práctica está en
que conocer $\phi(n)$ es equivalente a factorizar $n$, lo cual es —al
menos según el estado del arte— computacionalmente inviable para
$n$ del tamaño usado en RSA.

### 2.4 Raíces primitivas y logaritmo discreto

Un elemento $g \in \mathbb{Z}_n^*$ se denomina **raíz primitiva** (o
*generador*) de $\mathbb{Z}_n^*$ si su orden iguala al cardinal del
grupo, esto es, $\operatorname{ord}_n(g) = \phi(n)$. En tal caso, la
sucesión $g^0, g^1, \dots, g^{\phi(n) - 1}$ recorre todos los
elementos de $\mathbb{Z}_n^*$, y se dice que el grupo es **cíclico**.

En el ejemplo de la sección 2.2, $3$ es raíz primitiva de
$\mathbb{Z}_7^*$ (su orden es $\phi(7) = 6$), mientras que $2$ no lo
es. La existencia de una raíz primitiva no está garantizada para todo
$n$.

> **Teorema 31.32 (Cormen).** $\mathbb{Z}_n^*$ es cíclico si y sólo si
> $n \in \{2, 4, p^e, 2p^e\}$, donde $p$ es un primo impar y $e \geq 1$.

Cuando $g$ es raíz primitiva de $\mathbb{Z}_n^*$, todo elemento
$a \in \mathbb{Z}_n^*$ se expresa de forma única como
$a \equiv g^z \pmod n$ para algún $z \in \{0, 1, \dots, \phi(n) - 1\}$.
Ese exponente $z$ se llama **logaritmo discreto** de $a$ en base $g$
y se denota $\operatorname{ind}_{n, g}(a)$. Calcular logaritmos
discretos en grupos grandes —es decir, dado $a$ y $g$, encontrar
$z$— es, por su parte, otro problema que se cree intratable: en él
descansan la seguridad de Diffie–Hellman y de ElGamal.

### 2.5 Raíces cuadradas no triviales de 1

Una propiedad fina de las potencias módulo primos que será relevante
para entender la conexión con el test de Miller–Rabin es el
comportamiento de las raíces cuadradas de $1$.

> **Teorema 31.34 (Cormen).** Sea $p$ un primo impar y $e \geq 1$. La
> ecuación $x^2 \equiv 1 \pmod{p^e}$ posee únicamente las dos
> soluciones $x \equiv 1 \pmod{p^e}$ y $x \equiv -1 \pmod{p^e}$.

Se denomina **raíz cuadrada no trivial de $1$ módulo $n$** a cualquier
$x \in \mathbb{Z}_n^*$ tal que $x^2 \equiv 1 \pmod n$ pero
$x \not\equiv \pm 1 \pmod n$. Por ejemplo, $6$ es una raíz cuadrada
no trivial de $1$ módulo $35$, dado que $6^2 = 36 \equiv 1 \pmod{35}$
y $6 \not\equiv \pm 1 \pmod{35}$.

> **Corolario 31.35 (Cormen).** Si existe una raíz cuadrada no trivial
> de $1$ módulo $n$, entonces $n$ es compuesto.

Esta es la observación que sustenta la corrección del test de
Miller–Rabin. Aunque no es el foco del presente trabajo, conviene
mencionar la conexión porque ilustra por qué la exponenciación
modular es una primitiva compartida entre varios algoritmos
criptográficos: para ejecutar Miller–Rabin sobre un candidato $n$ con
testigo $a$, lo primero es calcular $a^{n-1} \bmod n$, y la búsqueda
de raíces no triviales de $1$ se realiza inspeccionando los cuadrados
intermedios de esa exponenciación.

### 2.6 El problema computacional

Formalmente, el problema que abordamos es: dado $a, b \in \mathbb{N}$
con $0 \leq a < n$ y $b \geq 0$, y dado $n \in \mathbb{N}_{> 0}$,
calcular el único valor $a^b \bmod n$ en $\{0, 1, \dots, n - 1\}$.

Como se argumentó en la sección 1.1, calcular $a^b$ exactamente y
luego reducir es inviable. La estrategia universal consiste en
mantener el resultado parcial siempre reducido módulo $n$, de modo
que ningún entero intermedio supere aproximadamente $n^2$ bits.
Sobre esta base, el reto algorítmico es minimizar el número de
multiplicaciones modulares requeridas.

### 2.7 Aplicaciones

La exponenciación modular aparece, entre otras, en los siguientes
contextos:

- **RSA.** El cifrado de un mensaje $m$ con clave pública $(e, n)$
  produce $c = m^e \bmod n$; el descifrado con clave privada
  $(d, n)$ recupera $m = c^d \bmod n$ (Rivest, Shamir, Adleman,
  1978). Los tamaños típicos de $n$ van de $2048$ a $4096$ bits.
- **Diffie–Hellman.** Dos partes acuerdan una clave compartida
  intercambiando $A = g^a \bmod p$ y $B = g^b \bmod p$, donde $g$ es
  una raíz primitiva pública.
- **DSA y firmas digitales.** Tanto la firma como su verificación
  requieren múltiples exponenciaciones modulares con módulos grandes.
- **Miller–Rabin.** El núcleo del test es la exponenciación
  $a^{n-1} \bmod n$ con inspección de cuadrados intermedios.

En todos estos casos, $b$ tiene varios miles de bits y la
exponenciación domina el costo total. Optimizar el número de
multiplicaciones se traduce directamente en menor latencia y menor
consumo energético, factores especialmente relevantes en dispositivos
móviles, *smart cards* y servidores que procesan grandes volúmenes
de operaciones TLS.

---

## 3. Algoritmos

A lo largo de esta sección, $\beta = \lfloor \log_2 b \rfloor + 1$
denota el número de bits del exponente, y $H(b)$ su peso de Hamming
(número de unos en su representación binaria). Las complejidades se
reportan en **número de multiplicaciones modulares**, contabilizando
por separado las multiplicaciones genéricas ($x \cdot y$ con
$x \neq y$) de los cuadrados ($x \cdot x$).

### 3.1 Método ingenuo

El algoritmo más directo consiste en iterar la multiplicación
modular un total de $b$ veces:

```
NAIVE-MODEXP(a, b, n):
  result ← 1
  for i ← 1 to b:
      result ← (result · a) mod n
  return result
```

Su correctitud se sigue por inducción inmediata: tras la iteración
$i$, `result` $= a^i \bmod n$. El costo es de exactamente $b$
multiplicaciones modulares y $0$ cuadrados, lo que se traduce en
complejidad $O(b)$ en operaciones aritméticas y $O(b \cdot \beta^2)$
en operaciones de bit, dado que cada multiplicación de operandos de
$\beta$ bits cuesta $O(\beta^2)$ usando el algoritmo escolar. El
método se incluye únicamente como referencia, pues resulta
inutilizable para los $b$ usados en criptografía.

### 3.2 Cuadrados repetidos de izquierda a derecha

El algoritmo `MODULAR-EXPONENTIATION` que aparece en la página 957 de
Cormen es la implementación canónica del método de cuadrados
repetidos. Procesa la representación binaria
$\langle b_k, b_{k-1}, \dots, b_0 \rangle$ del exponente desde el bit
más significativo hacia el menos significativo.

```
MODULAR-EXPONENTIATION(a, b, n):                  // Cormen, p. 957
  c ← 0
  d ← 1
  let ⟨b_k, b_{k-1}, ..., b_0⟩ be the binary representation of b
  for i ← k downto 0:
      c ← 2c
      d ← (d · d) mod n
      if b_i == 1:
          c ← c + 1
          d ← (d · a) mod n
  return d
```

La correctitud descansa en un invariante de bucle de dos partes que
Cormen formula así: justo antes de cada iteración del lazo (líneas
4–9),

1. el valor de $c$ coincide con el prefijo
   $\langle b_k, b_{k-1}, \dots, b_{i+1} \rangle$ de la
   representación binaria de $b$, y
2. $d = a^c \bmod n$.

La inicialización es inmediata: con $i = k$, el prefijo
$\langle b_k, \dots, b_{i+1} \rangle$ está vacío, lo cual corresponde
a $c = 0$, y se cumple $d = 1 = a^0 \bmod n$. Para el mantenimiento,
en cada iteración $c$ pasa a ser $2c$ (si $b_i = 0$) o $2c + 1$ (si
$b_i = 1$), correspondientes al nuevo prefijo extendido en un bit.
La actualización de $d$ refleja exactamente este cambio: si $b_i = 0$,
entonces $d \leftarrow d^2 \equiv (a^c)^2 = a^{2c} \pmod n$; si
$b_i = 1$, entonces $d \leftarrow d^2 \cdot a \equiv a^{2c + 1} \pmod n$.
Al terminar, $i = -1$ y $c = b$, por lo que $d = a^b \bmod n$.

Como ejemplo, la figura 31.4 de Cormen detalla el cálculo de
$7^{560} \bmod 561$, donde $560 = (1000110000)_2$. Tras las diez
iteraciones, $d$ toma sucesivamente los valores $7$, $49$, $157$,
$526$, $160$, $241$, $298$, $166$, $67$ y, finalmente, $1$.

**Complejidad.** El bucle se ejecuta $\beta = k + 1$ veces, cada una
con un cuadrado modular incondicional; las multiplicaciones por $a$
ocurren únicamente cuando $b_i = 1$, lo cual sucede $H(b)$ veces. El
costo total es por tanto $\beta$ cuadrados más $H(b)$
multiplicaciones, lo que en promedio (sobre exponentes uniformemente
aleatorios) equivale a $1.5\beta$ operaciones modulares. Cormen
reporta $O(\beta)$ operaciones aritméticas y $O(\beta^3)$ operaciones
de bit considerando $n$ también de $\beta$ bits.

### 3.3 Cuadrados repetidos de derecha a izquierda

El ejercicio 31.6-2 de Cormen invita a derivar una variante que
examine los bits del exponente desde el menos significativo. Su
estructura habitual es la siguiente:

```
RIGHT-TO-LEFT-MODEXP(a, b, n):
  result ← 1
  base ← a mod n
  while b > 0:
      if b mod 2 == 1:
          result ← (result · base) mod n
      b ← b div 2
      if b > 0:
          base ← (base · base) mod n
  return result
```

El invariante es distinto al de la versión L→R pero igualmente
natural: al inicio de cada iteración, si $i$ es el bit menos
significativo aún por procesar de la $b$ original, se cumple
que `base` $= a^{2^i} \bmod n$ y que `result` $= a^{e}$, donde $e$ es
la suma de las potencias de $2$ correspondientes a los bits ya
procesados. Cuando $b$ se agota, $e$ ha acumulado el exponente
completo.

Asintóticamente la complejidad coincide con la versión L→R: $\beta$
cuadrados —uno menos en realidad, pues no es necesario elevar al
cuadrado tras procesar el bit más significativo, optimización que la
implementación incorpora— y $H(b)$ multiplicaciones. La diferencia
es estructural: cada iteración realiza el cuadrado y la posible
multiplicación sobre variables distintas (`base` y `result`), lo que
permite ejecutar ambas operaciones en paralelo a nivel de
instrucción si el hardware lo soporta. A cambio, el algoritmo mantiene
simultáneamente en memoria la potencia $a^{2^i}$ y el resultado
parcial, en lugar de un solo registro como en la versión L→R.

### 3.4 Método de ventana fija ($k$-ario)

La idea de los métodos de ventana es procesar varios bits del
exponente a la vez, a costa de una precomputación inicial. En el
método $k$-ario fijo se precomputa una tabla con todas las potencias
posibles de la ventana, $T[j] = a^j \bmod n$ para $j = 0, 1, \dots,
2^k - 1$, y luego se procesa el exponente en bloques disjuntos de
$k$ bits consecutivos.

```
FIXED-WINDOW(a, b, n, k):                          // HAC, Algoritmo 14.82
  precompute T[j] = a^j mod n for j = 0, …, 2^k − 1
  split b into windows (w_{m−1}, w_{m−2}, …, w_0) of k bits each
  result ← T[w_{m−1}]
  for i ← m − 2 downto 0:
      repeat k times: result ← (result · result) mod n     // k cuadrados
      result ← (result · T[w_i]) mod n                      // 1 multiplicación
  return result
```

donde $m = \lceil \beta / k \rceil$ es el número de ventanas. La
correctitud se sigue de un argumento análogo al del algoritmo
binario: tras procesar la ventana $i$, el invariante es
`result` $= a^{(w_{m-1} w_{m-2} \cdots w_i)_{2^k}}$, donde los
subíndices indican concatenación de los bits de las ventanas ya
procesadas, interpretados como número en base $2^k$.

**Complejidad.** La precomputación —construida incrementalmente
mediante $T[j] = T[j-1] \cdot a$ a partir de $T[0] = 1$— requiere
$2^k - 2$ multiplicaciones modulares. El bucle principal ejecuta
$(m-1) \cdot k \approx \beta$ cuadrados y $m - 1 \approx \beta/k$
multiplicaciones por entradas de la tabla. El total es

$$
T_{\text{kary}}(\beta, k) \approx \beta + \frac{\beta}{k} + 2^k - 2.
$$

**Tamaño óptimo de ventana.** Derivando esta expresión respecto a
$k$ e igualando a cero se obtiene la condición
$2^k \ln 2 = \beta/k^2$, cuya solución se aproxima por

$$
k_{\mathrm{opt}} \approx \log_2 \beta - \log_2 \log_2 \beta.
$$

Para $\beta = 1024$ esto entrega $k_{\mathrm{opt}} \approx 6.7$; para
$\beta = 2048$, $k_{\mathrm{opt}} \approx 7.7$. En la práctica, $k$
debe ser entero, así que los valores naturales a probar son $6$, $7$
y $8$ para exponentes en el rango criptográfico.

**Costo en memoria.** La tabla almacena $2^k$ enteros de $n$ bits,
es decir, un costo de memoria $O(2^k \cdot \beta)$ bits.

### 3.5 Método de ventana deslizante

El método de ventana deslizante (HAC, Algoritmo 14.85) introduce tres
refinamientos sobre la ventana fija:

1. **La tabla almacena solo potencias impares**: $T[j] = a^j \bmod n$
   para $j$ impar entre $1$ y $2^k - 1$, es decir, $2^{k-1}$ entradas
   en lugar de $2^k$. Las potencias pares no son necesarias porque la
   ventana se elige para terminar siempre en un bit $1$, lo que
   garantiza un valor impar.
2. **Las ventanas tienen tamaño variable** entre $1$ y $k$ bits, y se
   construyen de modo que empiecen *y* terminen en $1$. La ausencia
   de ceros al borde garantiza que la entrada de tabla
   correspondiente exista en la tabla reducida.
3. **Los bits $0$ entre ventanas son simples cuadrados**, sin
   multiplicación por tabla. En la ventana fija, en cambio, una
   ventana cuyos $k$ bits sean cero igualmente se multiplica por
   $T[0] = 1$, gasto que se ahorra aquí.

```
SLIDING-WINDOW(a, b, n, k):                        // HAC, Algoritmo 14.85
  precompute T[j] = a^j mod n for j = 1, 3, 5, …, 2^k − 1
  result ← 1
  i ← β − 1
  while i ≥ 0:
      if b_i == 0:
          result ← (result · result) mod n
          i ← i − 1
      else:
          // ventana maximal de longitud ≤ k que empiece en i y termine en '1'
          ℓ ← largest length in [1, k] s.t. b_{i − ℓ + 1} == 1
          v ← (b_i b_{i−1} … b_{i − ℓ + 1})_2
          repeat ℓ times: result ← (result · result) mod n
          result ← (result · T[v]) mod n
          i ← i − ℓ
  return result
```

**Costo de precomputación.** Construir la tabla cuesta un cuadrado
inicial ($a^2$) más $2^{k-1} - 1$ multiplicaciones por $a^2$ para
generar los impares $a^3, a^5, \dots, a^{2^k - 1}$. Total:
$1 + (2^{k-1} - 1) = 2^{k-1}$ operaciones.

**Complejidad.** El análisis estándar (Menezes et al., 1996, §14.85)
muestra que, en promedio sobre exponentes uniformemente aleatorios,
las ventanas tienen una longitud media de $k + 1$ posiciones contando
los bits cero adyacentes, lo cual conduce a aproximadamente
$\beta / (k + 1)$ multiplicaciones por entradas de la tabla. Sumando
todo:

$$
T_{\text{sliding}}(\beta, k) \approx \beta + \frac{\beta}{k + 1} + 2^{k - 1}.
$$

La comparación con la fórmula de ventana fija revela dos fuentes de
ahorro: el segundo término pasa de $\beta/k$ a $\beta/(k+1)$, y el
tercero pasa de $2^k - 2$ a $2^{k-1}$. En términos prácticos, para
$\beta = 1024$ y $k = 6$, la diferencia se traduce en un ahorro del
orden del $5$–$10\,\%$ en operaciones totales y de un $50\,\%$ en
memoria.

### 3.6 Resumen comparativo

La tabla siguiente sintetiza el costo asintótico de los cinco
algoritmos. Las constantes ignoran términos de orden inferior y se
expresan en función de $\beta$ y, donde aplica, del tamaño de
ventana $k$.

| Método | Multiplicaciones (promedio) | Cuadrados | Memoria de tabla |
|---|---|---|---|
| Ingenuo | $b$ | $0$ | $O(1)$ |
| Binario L→R | $\beta/2$ | $\beta$ | $O(1)$ |
| Binario R→L | $\beta/2$ | $\beta - 1$ | $O(1)$ |
| Ventana fija $k$-aria | $\beta/k + 2^k - 2$ | $\beta$ | $O(2^k)$ |
| Ventana deslizante | $\beta/(k+1) + 2^{k-1}$ | $\beta$ | $O(2^{k-1})$ |

Para exponentes de tamaño criptográfico ($\beta \geq 1024$), los
métodos de ventana mejoran a los binarios en aproximadamente un
$20$–$25\,\%$ en el conteo total de operaciones, a costa de una
tabla cuyo tamaño puede regularse mediante $k$. La ventana
deslizante domina a la fija para todo $k$ común, y por ello es la
elección estándar en bibliotecas criptográficas modernas como
OpenSSL (`BN_mod_exp_mont`) y GMP (`mpz_powm`).

---

## Notas para integración

- Las citas a Cormen siguen el formato del libro original: número de
  teorema (p. ej. 31.30), corolario (p. ej. 31.35) o ecuación
  (p. ej. 31.33). Verificar que la bibliografía esté correctamente
  formateada según el estilo elegido (APA o IEEE).
- Las referencias a HAC corresponden a Menezes, van Oorschot y
  Vanstone (1996), capítulo 14, §14.6. Los números de algoritmo
  (14.82, 14.85) son los del libro.
- El pseudocódigo usa `←` para asignación y `·` para multiplicación,
  siguiendo la convención de Cormen. Mantener consistencia en todo
  el informe.
- Si se imprime en LaTeX, considerar `algorithm2e` o `algorithmicx`
  para el pseudocódigo formal. Si se entrega en Word/PDF directo,
  bloques de código con tipografía monoespaciada es suficiente.
