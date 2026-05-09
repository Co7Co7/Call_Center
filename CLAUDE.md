# Call Center — Contexto del proyecto

## 📌 Descripción
Análisis y visualización del dataset público "Call Center Data" (Kaggle, autor: satvicoder).
Objetivo: explorar métricas operativas del call center (volumen de llamadas, tiempos de
respuesta, satisfacción, desempeño de agentes) y comunicar hallazgos de forma profesional
mediante dashboard interactivo y análisis reproducible.

**Fuente de datos:** https://www.kaggle.com/datasets/satvicoder/call-center-data

## 🎯 Objetivos del proyecto
- Producir un análisis exploratorio (EDA) reproducible del dataset
- Calcular KPIs típicos de call center: AHT, CSAT, abandonment rate, resolución 1er contacto, etc.
- Mantener un dashboard HTML/JS interactivo para presentar resultados
- Servir como portafolio profesional de data analysis

## 🛠️ Stack técnico

### Análisis de datos (a incorporar)
- Python 3.11+
- pandas, numpy → manipulación
- matplotlib, seaborn, plotly → visualización
- jupyter → exploración inicial
- pytest → tests
- ruff + black → calidad de código

### Dashboard
- HTML, CSS, JavaScript vanilla (o framework si se decide migrar)
- Posiblemente Chart.js / D3.js para gráficos

## 📁 Estructura objetivo del repo
```
Call_Center/
├── data/
│   ├── raw/                 # Call Center Data.csv original (no modificar)
│   └── processed/           # Datos limpios listos para análisis
├── notebooks/
│   └── 01_eda.ipynb         # Exploración inicial
├── src/
│   ├── __init__.py
│   ├── data_loader.py       # Carga y validación
│   ├── cleaning.py          # Limpieza y transformaciones
│   ├── metrics.py           # Cálculo de KPIs
│   └── viz.py               # Funciones de gráficos reutilizables
├── tests/
│   └── test_metrics.py
├── dashboard/
│   ├── index.html           # Dashboard actual movido aquí
│   ├── style.css
│   └── app.js
├── reports/
│   └── findings.md          # Resumen de hallazgos
├── .gitignore
├── pyproject.toml           # Dependencias y config de herramientas
├── README.md
└── CLAUDE.md
```

## 📐 Convenciones de código

### Python
- Type hints en todas las funciones públicas
- Docstrings estilo Google
- Nombres de variables y funciones en inglés (`call_duration`, no `duracion_llamada`)
- Comentarios explicativos en español (es la lengua de trabajo)
- Sin código duplicado entre notebooks → si se usa 2+ veces, va a `src/`
- No usar `print()` para debug, usar `logging`
- Snake_case para variables y funciones, PascalCase para clases

### Notebooks
- Solo para exploración inicial y storytelling
- La lógica reutilizable se extrae a `src/`
- Cada notebook empieza con celda markdown que explica objetivo y conclusiones
- Ejecutar "Restart & Run All" antes de commitear (notebook debe correr de arriba a abajo sin errores)

### Git
- Commits en formato Conventional Commits:
  `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `data:`
- Mensajes en inglés, presente imperativo: "add metrics module" no "added metrics module"
- Una rama por bloque de mejora (`refactor/structure`, `feat/kpi-module`, etc.)
- Pull Request a main aunque sea proyecto solo, para revisar el cambio completo

## 🚫 Qué evitar
- NO modificar `data/raw/Call Center Data.csv` (datos originales intocables)
- NO commitear archivos > 25 MB
- NO commitear datos sensibles, claves API, tokens, ni `.env`
- NO mezcla cambios de distintos temas en un mismo commit
- NO usar rutas absolutas tipo `C:\Users\<nombre>\...` → siempre rutas relativas o `pathlib`
- NO hardcodear nombres de columnas en múltiples sitios → centralizar en `src/`
- NO subir archivos de checkpoint de Jupyter (`.ipynb_checkpoints/`)

## ✅ Antes de hacer cambios grandes
Cuando te pida un refactor o feature importante:
1. **Explica primero** qué archivos vas a tocar y por qué, antes de modificar nada
2. **Espera confirmación** explícita antes de ejecutar
3. **Trabaja en una rama** separada (sugiere el nombre)
4. **Commits por bloque lógico**, no todo junto al final
5. **Verifica que nada se rompe**: corre tests si existen, abre el notebook, verifica el dashboard

## 🧪 Comandos clave

```bash
# Entorno
python -m venv .venv
.venv\Scripts\activate              # Windows
pip install -e ".[dev]"

# Calidad de código
ruff check .                        # Linter
ruff format .                       # Formato (o black .)

# Tests
pytest tests/ -v
pytest --cov=src tests/             # Con cobertura

# Notebooks
jupyter lab

# Dashboard local
# Abrir dashboard/index.html en el navegador, o:
python -m http.server 8000          # luego ir a localhost:8000/dashboard/
```

## 📊 Métricas de calidad del proyecto (objetivo)
- [ ] README claro con setup y resultados
- [ ] Estructura de carpetas profesional
- [ ] Código separado en módulos reutilizables
- [ ] Tests con cobertura > 70% en `src/`
- [ ] Linter sin warnings (ruff)
- [ ] Notebook reproducible end-to-end
- [ ] Dashboard funcional y documentado
- [ ] Reporte de hallazgos en `reports/`
- [ ] Pre-commit hooks configurados
