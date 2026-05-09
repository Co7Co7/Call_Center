# Reporte de Hallazgos — Call Center Performance Analysis

**Dataset:** 1,251 registros periódicos · 248,373 llamadas totales
**Fuente:** [Kaggle — Call Center Data](https://www.kaggle.com/datasets/satvicoder/call-center-data)
**Análisis:** `notebooks/01_eda.ipynb` · `notebooks/03_analysis.ipynb`

---

## KPIs globales

| Métrica | Valor | Referencia industria | Estado |
|---|---|---|---|
| Answer Rate | 92.7% | > 90% | ✅ Cumple |
| Service Level 20s | 70.9% | > 80% | ⚠️ Por debajo |
| SLA Compliance (≥80% SL) | 36.6% de periodos | > 80% | ❌ Crítico |
| Abandonment Rate | 10.9% | < 5% | ❌ Crítico |
| Answer Speed (mediana) | 21s | < 20s | ⚠️ Límite |
| AHT promedio | 390s (~6.5 min) | — | Referencia |
| Correlación Waiting / Abandonos | r = 0.72 | — | Fuerte positiva |

---

## Hallazgo 1 — El SLA 80% se cumple en menos de la mitad de los periodos

El Service Level promedio es 70.9%, pero el promedio oculta una variabilidad muy alta
(σ = 0.185, rango completo 0%–100%). Solo **el 36.6% de los periodos** alcanzan el
objetivo del 80% que fija la industria.

El problema no es de nivel promedio sino de **consistencia**: hay periodos excelentes
(SL > 95%) que coexisten con periodos donde ninguna llamada se responde en 20 segundos.

**Implicación:** reportar únicamente el promedio de SL da una imagen engañosamente
optimista. El indicador relevante es la tasa de cumplimiento periodo a periodo.

---

## Hallazgo 2 — La tasa de abandono es el doble del umbral aceptable

De las 248,373 llamadas entrantes, **27,139 fueron abandonadas** (10.9%).
El estándar de la industria para centros de llamadas de servicio al cliente es < 5%.

La correlación entre tiempo de espera y llamadas abandonadas es **r = 0.72** (fuerte
positiva): a mayor espera, más abandonos. Esto descarta causas aleatorias y apunta
directamente a problemas de capacidad de respuesta.

El cuartil de mayor carga (Q4) concentra desproporcionadamente los abandonos, lo que
sugiere que el equipo **no escala al ritmo del volumen** en picos de demanda.

---

## Hallazgo 3 — 12.4% de los periodos son críticos (SL < 50%)

155 de los 1,251 periodos registran un Service Level inferior al 50%: menos de la
mitad de las llamadas son atendidas en 20 segundos.

El análisis de outliers (método IQR) identifica que estos periodos concentran una
fracción desproporcionada de las llamadas abandonadas, lo que confirma que son los
episodios de mayor daño operativo y de experiencia al cliente.

---

## Hallazgo 4 — El Answer Speed es el principal palanca de mejora del SLA

El análisis de franjas de `answer_speed` muestra una relación clara: a menor tiempo
de respuesta promedio del agente, mayor es la probabilidad de cumplir el SLA 80%.

| Franja Answer Speed | % periodos con SL ≥ 80% |
|---|---|
| 0–10s | Alto (> 80%) |
| 10–20s | Moderado |
| 20–30s | Bajo |
| > 30s | Muy bajo |

La mediana actual es 21s, rozando el umbral ideal de 20s pero insuficiente para
sostener el SLA de forma consistente en periodos de alta carga.

---

## Recomendaciones

### Corto plazo (0–3 meses)
1. **Monitorear SLA periodo a periodo**, no solo el promedio mensual. Añadir alerta
   automática cuando el SL cae por debajo del 50% en dos periodos consecutivos.
2. **Reducir Answer Speed en picos de carga** — el Q4 de volumen es donde más se
   degrada. Puede requerir redistribución de turnos o escalado temporal de agentes.

### Mediano plazo (3–6 meses)
3. **Objetivo de abandonment rate < 5%** — actualmente en 10.9%. Requiere bajar
   el tiempo de espera promedio (hoy ~366s) que es el driver principal del abandono.
4. **Revisar dimensionamiento de personal en periodos críticos** — los 155 periodos
   con SL < 50% son candidatos directos para un análisis de causas raíz (¿turno
   corto?, ¿pico estacional?, ¿incidente técnico?).

### Largo plazo (> 6 meses)
5. **Incorporar serie temporal con fechas reales** — el dataset actual solo tiene
   índice ordinal. Con timestamps reales se podría identificar patrones horarios,
   semanales y estacionales para planificación predictiva de capacidad.

---

## Metodología

| Paso | Herramienta |
|---|---|
| Carga y limpieza | `src/call_center/data_loader.py` + `cleaning.py` |
| KPIs | `src/call_center/metrics.py` |
| EDA | `notebooks/01_eda.ipynb` |
| Análisis profundo | `notebooks/03_analysis.ipynb` |
| Validación | `tests/` — 33 tests, todos pasando |

Todos los resultados son **reproducibles**: `pip install -e ".[dev]"` + `pytest` +
`jupyter lab` es suficiente para regenerar el análisis desde cero.
