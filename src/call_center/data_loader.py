"""Carga del dataset de Call Center desde disco."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Nombres de columnas — fuente única de verdad para todo el proyecto
# ---------------------------------------------------------------------------

# Columnas tal como vienen en el CSV crudo
RAW_COLS = {
    "index":          "Index",
    "incoming":       "Incoming Calls",
    "answered":       "Answered Calls",
    "answer_rate":    "Answer Rate",
    "abandoned":      "Abandoned Calls",
    "answer_speed":   "Answer Speed (AVG)",
    "talk_duration":  "Talk Duration (AVG)",
    "waiting_time":   "Waiting Time (AVG)",
    "service_level":  "Service Level (20 Seconds)",
}

# Columnas en el DataFrame limpio (snake_case, tipos correctos)
CLEAN_COLS = {
    "incoming":       "incoming_calls",
    "answered":       "answered_calls",
    "answer_rate":    "answer_rate",        # float [0, 1]
    "abandoned":      "abandoned_calls",
    "answer_speed":   "answer_speed_avg_s", # int, segundos
    "talk_duration":  "talk_duration_avg_s",
    "waiting_time":   "waiting_time_avg_s",
    "service_level":  "service_level_20s",  # float [0, 1]
}

# Ruta por defecto al CSV crudo (relativa a la raíz del repo)
_DEFAULT_RAW = Path(__file__).parent.parent.parent / "data" / "raw" / "Call Center Data.csv"
_DEFAULT_PROCESSED = Path(__file__).parent.parent.parent / "data" / "processed" / "call_center_clean.csv"


def load_raw(path: Path | str | None = None) -> pd.DataFrame:
    """Carga el CSV crudo sin ninguna transformación.

    Args:
        path: Ruta al archivo CSV. Si es None usa data/raw/Call Center Data.csv.

    Returns:
        DataFrame con las columnas originales y tipos inferidos por pandas.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta indicada.
    """
    csv_path = Path(path) if path else _DEFAULT_RAW

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {csv_path}")

    df = pd.read_csv(csv_path, sep=";")
    logger.info("CSV cargado: %d filas, %d columnas — %s", len(df), len(df.columns), csv_path.name)
    return df


def load_clean(path: Path | str | None = None) -> pd.DataFrame:
    """Carga el CSV ya procesado generado por el pipeline de limpieza.

    Args:
        path: Ruta al CSV procesado. Si es None usa data/processed/call_center_clean.csv.

    Returns:
        DataFrame con tipos correctos listos para análisis.

    Raises:
        FileNotFoundError: Si el archivo procesado no existe (ejecutar cleaning primero).
    """
    csv_path = Path(path) if path else _DEFAULT_PROCESSED

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV procesado no encontrado: {csv_path}\n"
            "Ejecuta primero: python -m call_center.cleaning"
        )

    df = pd.read_csv(csv_path)
    logger.info("CSV limpio cargado: %d filas — %s", len(df), csv_path.name)
    return df
