## 🤖 10. Machine Learning — Clasificación de perfiles de exclusión digital

<details>
<summary><strong>Ver sección completa</strong></summary>

### 10.1 Objetivo del modelo

El análisis exploratorio y las consultas SQL describen *cuánta* brecha existe. El módulo de Machine Learning añade una dimensión predictiva: **¿puede un algoritmo aprender a identificar automáticamente qué perfiles sociodemográficos tienen alta exclusión digital?**

La pregunta concreta que responde el modelo es:

> *Dado un perfil definido por país, nivel de discapacidad, sexo y grupo de edad, ¿tiene ese perfil alta exclusión digital (uso de Internet inferior al 85%)?*

Esta pregunta tiene sentido práctico directo: si el modelo aprende bien, puede generalizarse para anticipar qué colectivos necesitan políticas de inclusión digital prioritarias.

---

### 10.2 Definición del problema

**Tipo de problema:** clasificación binaria supervisada.

**Variable objetivo (`alta_exclusion`):**

| Clase | Definición | N observaciones |
|:---:|---|:---:|
| **0** — Baja exclusión | Uso de Internet ≥ 85% | 146 (74,1%) |
| **1** — Alta exclusión | Uso de Internet < 85% | 51 (25,9%) |

El umbral del 85% se eligió porque separa de forma natural los dos grupos: la media UE-27 de uso sin discapacidad es 95,22%, mientras que la media con discapacidad severa es 82,29%. El umbral del 85% cae en ese espacio intermedio con mayor poder discriminante.

**Features (4 variables de entrada):**

| Feature | Tipo | Valores posibles |
|---|---|---|
| `nivel_discapacidad` | Categórica nominal | Sin discapacidad / Leve / Severa / Leve o severa |
| `sexo` | Categórica nominal | Total / Female / Male |
| `grupo_edad` | Categórica nominal | Total / 16-24 / 25-54 / 55-74 |
| `país` | Categórica nominal | DE, ES, FR, IT, LT, NL, PT, SE, EU27_2020 |

Todas las variables categóricas se codifican con `LabelEncoder` antes de entrenar. Se excluyen las 19 observaciones con baja fiabilidad estadística (`is_reliable=False`).

**Dataset final:** 197 observaciones × 4 features.

**División train/test:** 80% entrenamiento (157 obs) / 20% test (40 obs), con estratificación para mantener la proporción de clases en ambos conjuntos.

---

### 10.3 Modelos comparados

Se entrenaron y compararon tres algoritmos de clasificación, todos implementados con **Scikit-learn**:

| Modelo | Accuracy test | Accuracy CV (5 folds) |
|---|:---:|:---:|
| Árbol de Decisión (max_depth=4) | 77,5% | 79,2% |
| Random Forest (100 árboles, max_depth=4) | 80,0% | 81,2% |
| **K-Nearest Neighbors (K=5)** | **77,5%** | **82,3%** ← mejor |

La métrica de referencia para la selección del modelo es el **accuracy en validación cruzada estratificada de 5 folds** (`StratifiedKFold`), ya que el conjunto de test (40 observaciones) es pequeño y puede variar según la partición aleatoria.

El modelo seleccionado es **K-Nearest Neighbors (K=5)** con un **82,3% de accuracy en validación cruzada**.

> **Línea base de referencia:** un clasificador aleatorio que predijese siempre la clase mayoritaria (baja exclusión) obtendría un 74,1% de accuracy. Los tres modelos superan claramente esta línea base.

---

### 10.4 Resultado del modelo ganador — K-Nearest Neighbors

**Configuración:** `KNeighborsClassifier(n_neighbors=5)` de Scikit-learn.

**Reporte de clasificación (conjunto de test, 40 observaciones):**

| Clase | Precision | Recall | F1-score | Soporte |
|---|:---:|:---:|:---:|:---:|
| Baja exclusión (≥85%) | 0,80 | 0,93 | 0,86 | 30 |
| Alta exclusión (<85%) | 0,60 | 0,30 | 0,40 | 10 |
| **Accuracy global** | | | **0,78** | **40** |

**Matriz de confusión:**

```
                        Predicción
                    Baja excl.   Alta excl.
Real  Baja excl.       28            2
      Alta excl.        7            3
```

| Indicador | Valor |
|---|:---:|
| Verdaderos negativos (predijo baja, era baja) | 28 |
| Falsos positivos (predijo alta, era baja) | 2 |
| Falsos negativos (predijo baja, era alta) | 7 |
| Verdaderos positivos (predijo alta, era alta) | 3 |

**Interpretación:** el modelo identifica correctamente el 93% de los perfiles de baja exclusión (alta especificidad), aunque tiene más dificultad con los perfiles de alta exclusión (recall del 30%). Esto es coherente con el desbalance de clases (74% / 26%) y con la heterogeneidad de los perfiles de alta exclusión entre países.

---

### 10.5 Importancia de variables — Random Forest

Aunque KNN es el modelo con mejor accuracy en CV, el **Random Forest** permite cuantificar la importancia relativa de cada feature. Estos valores son informativos para el análisis y coherentes con los hallazgos del EDA:

| Feature | Importancia | Interpretación |
|---|:---:|---|
| **País** | **39,5%** | El contexto nacional es el factor más determinante |
| **Nivel de discapacidad** | **30,9%** | Confirma que la discapacidad predice la exclusión |
| **Grupo de edad** | **25,9%** | El envejecimiento amplifica la exclusión digital |
| **Sexo** | **3,6%** | Menor peso individual, aunque relevante en España |

El hecho de que el **nivel de discapacidad sea el segundo factor más importante** (30,9%), por encima del grupo de edad y muy por encima del sexo, respalda cuantitativamente la hipótesis central del proyecto: **la discapacidad es un predictor independiente y significativo de la exclusión digital**, no un efecto secundario del envejecimiento o del género.

---

### 10.6 Ejemplos de predicción

El modelo Random Forest (utilizado aquí por su interpretabilidad mediante probabilidades) predice correctamente los cinco perfiles representativos del proyecto:

| Perfil | Predicción | Real | P(alta exclusión) |
|---|:---:|:---:|:---:|
| España · mujer · 55-74 · discap. severa | Alta exclusión | Alta exclusión ✓ | 0,84 |
| España · hombre · 25-54 · sin discap. | Baja exclusión | Baja exclusión ✓ | 0,02 |
| Países Bajos · total · total · discap. severa | Baja exclusión | Baja exclusión ✓ | 0,29 |
| Lituania · total · 55-74 · discap. severa | Alta exclusión | Alta exclusión ✓ | 0,82 |
| Alemania · mujer · total · discap. leve | Baja exclusión | Baja exclusión ✓ | 0,09 |

Los dos perfiles más vulnerables del proyecto (mujer española de 55-74 años con discapacidad severa y perfil lituano mayor con discapacidad severa) son clasificados correctamente con probabilidades muy altas (0,84 y 0,82), lo que refuerza la validez del modelo.

---

### 10.7 Accuracy desglosado por nivel de discapacidad

| Nivel de discapacidad | Accuracy | Observaciones en test |
|---|:---:|:---:|
| Sin discapacidad | 94% | 17 |
| Leve o severa (agrupada) | 86% | 7 |
| Limitación severa | 75% | 4 |
| Limitación leve | 58% | 12 |

El modelo funciona mejor con los perfiles más extremos (sin discapacidad o con categoría agregada) y tiene más dificultad con la limitación leve, cuyos valores de uso de Internet se solapan con los de la categoría severa en algunos países.

---

### 10.8 Limitaciones del modelo

1. **Tamaño del dataset:** 197 observaciones es un volumen reducido para machine learning. Los resultados son robustos para este análisis descriptivo, pero no deben extrapolarse a poblaciones individuales.

2. **Datos agregados:** el modelo trabaja con porcentajes nacionales, no con registros individuales. Predice el comportamiento de un *perfil estadístico*, no de una persona concreta.

3. **Desbalance de clases:** el 74% de las observaciones son de baja exclusión. Técnicas como SMOTE o ajuste de pesos de clase podrían mejorar el recall de la clase minoritaria en trabajos futuros.

4. **Un único año de observación:** el modelo no captura tendencias temporales. Un análisis longitudinal con datos de varios años permitiría modelos predictivos más robustos.

---

### 10.9 Conclusión del módulo ML

El modelo de clasificación confirma con evidencia cuantitativa lo que el análisis descriptivo sugería: **el nivel de discapacidad y el país de residencia son los dos factores más predictivos de la exclusión digital**, con un peso conjunto del 70% en el modelo. El sexo, aunque relevante en el análisis de doble vulnerabilidad de España, tiene un peso individual menor (3,6%) cuando se considera en el conjunto de todos los países.

Con un **82,3% de accuracy en validación cruzada**, el modelo constituye una herramienta analítica válida para identificar automáticamente perfiles de riesgo de exclusión digital, abriendo la puerta a aplicaciones de política pública basadas en datos.

**Fichero:** `python/ml_clasificacion.py`  
**Figuras generadas:** `images/figures/07_ml_comparacion_modelos.png`, `08_ml_matriz_confusion.png`, `09_ml_importancia_features.png`, `10_ml_arbol_decision.png`  
**Resultados:** `outputs/tables/ml_resultados_clasificacion.csv`

</details>
