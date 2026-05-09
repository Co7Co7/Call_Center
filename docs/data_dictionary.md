# Diccionario de datos — Call Center Dataset

Fuente original: [Kaggle — Call Center Data](https://www.kaggle.com/datasets/satvicoder/call-center-data)

El CSV crudo (`data/raw/Call Center Data.csv`) usa `;` como separador.
El CSV procesado (`data/processed/call_center_clean.csv`) tiene tipos correctos y nombres en snake_case.

## Columnas del dataset procesado

| Nombre (procesado) | Nombre original | Tipo | Unidad | Descripción | Rango válido |
|---|---|---|---|---|---|
| `incoming_calls` | `Incoming Calls` | int | llamadas | Total de llamadas recibidas en el periodo | >= 0 |
| `answered_calls` | `Answered Calls` | int | llamadas | Llamadas efectivamente atendidas por un agente | >= 0, <= incoming |
| `answer_rate` | `Answer Rate` | float | proporción [0, 1] | Fracción de llamadas respondidas sobre el total entrante | [0, 1] |
| `abandoned_calls` | `Abandoned Calls` | int | llamadas | Llamadas colgadas por el cliente antes de ser atendidas | >= 0, <= incoming |
| `answer_speed_avg_s` | `Answer Speed (AVG)` | int | segundos | Tiempo medio hasta que un agente contesta la llamada | >= 0 |
| `talk_duration_avg_s` | `Talk Duration (AVG)` | int | segundos | Duración media de la conversación agente-cliente | >= 0 |
| `waiting_time_avg_s` | `Waiting Time (AVG)` | int | segundos | Tiempo medio de espera del cliente en cola | >= 0 |
| `service_level_20s` | `Service Level (20 Seconds)` | float | proporción [0, 1] | Fracción de llamadas respondidas en 20 segundos o menos | [0, 1] |

## Notas de transformación

- **Porcentajes:** las columnas `answer_rate` y `service_level_20s` venían como strings (`"94.01%"`) y fueron convertidas a float dividiendo por 100. Escala resultante: 0.0–1.0.
- **Tiempos:** las columnas de tiempo venían en formato `H:MM:SS` (p. ej. `"0:02:14"`) y fueron convertidas a segundos enteros usando `pd.to_timedelta`.
- **Columna Index:** eliminada — era un row number sin valor analítico.

## Invariante del negocio

```
answered_calls + abandoned_calls ≈ incoming_calls  (tolerancia ±1 por redondeo)
```

## Estadísticas clave (dataset completo, n=1251)

| Métrica | Media | Mediana | Std |
|---|---|---|---|
| `incoming_calls` | ~128 | ~133 | ~47 |
| `answered_calls` | ~119 | ~124 | ~44 |
| `answer_rate` | ~0.927 | ~0.935 | ~0.046 |
| `abandoned_calls` | ~9 | ~7 | ~8 |
| `answer_speed_avg_s` | ~27s | ~19s | ~29s |
| `talk_duration_avg_s` | ~163s (2.7 min) | ~161s | ~28s |
| `waiting_time_avg_s` | ~366s (6.1 min) | ~274s | ~333s |
| `service_level_20s` | ~0.709 | ~0.736 | ~0.172 |
