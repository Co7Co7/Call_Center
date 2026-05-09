# Call Center Performance Analysis

Análisis exploratorio de métricas operativas de un call center sobre 1,251 registros periódicos.
Proyecto de portafolio que demuestra pipeline de datos reproducible, EDA y validación de calidad.

## Hallazgos principales

| Métrica | Valor | Referencia | Estado |
|---|---|---|---|
| Answer Rate (avg) | 92.7% | >90% | OK |
| Service Level 20s (avg) | 70.9% | >80% industria | Por debajo |
| Answer Speed (avg) | 27s | <20s ideal | Por debajo |
| Correlación Waiting Time / Abandonos | r = 0.72 | — | Fuerte positiva |
| Periodos críticos (<50% SL) | ~18% | — | — |

## Dataset

- **Fuente:** [Kaggle — Call Center Data](https://www.kaggle.com/datasets/satvicoder/call-center-data)
- **Registros:** 1,251 filas × 8 métricas operativas
- **Ver:** [docs/data_dictionary.md](docs/data_dictionary.md)

## Estructura del proyecto

```
Call_Center/
├── data/
│   ├── raw/                        # CSV original (no modificar)
│   └── processed/                  # CSV limpio generado por el pipeline
├── docs/
│   └── data_dictionary.md
├── notebooks/
│   ├── 01_eda.ipynb                # Análisis exploratorio completo
│   └── 02_cleaning.ipynb           # Pipeline de limpieza documentado
├── reports/figures/                # Gráficas exportadas
├── src/call_center/
│   ├── data_loader.py              # Carga del CSV y constantes de columnas
│   └── cleaning.py                 # Transformaciones y pipeline
├── tests/
│   ├── conftest.py
│   └── test_data_quality.py        # 16 tests de invariantes del negocio
├── .gitignore
├── pyproject.toml
└── CLAUDE.md
```

## Instalación

Requiere Python 3.11+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

## Uso

**Ejecutar el pipeline de limpieza** (genera `data/processed/call_center_clean.csv`):

```bash
python -m call_center.cleaning
```

**Abrir los notebooks:**

```bash
jupyter lab
```

**Correr los tests:**

```bash
pytest tests/ -v
```

**Regenerar el reporte HTML** (actualiza `index.html`):

```bash
python -m call_center.report
```

## Notebooks

| Notebook | Descripción |
|---|---|
| [01_eda.ipynb](notebooks/01_eda.ipynb) | EDA completo: KPIs, distribuciones, correlaciones, segmentación |
| [02_cleaning.ipynb](notebooks/02_cleaning.ipynb) | Documenta cada transformación del pipeline de limpieza |
| [03_analysis.ipynb](notebooks/03_analysis.ipynb) | Análisis profundo: series de tiempo, outliers, propuesta de SLA |
