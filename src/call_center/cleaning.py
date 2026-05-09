"""Pipeline de limpieza y transformación del dataset de Call Center."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from call_center.data_loader import (
    CLEAN_COLS,
    RAW_COLS,
    _DEFAULT_PROCESSED,
    load_raw,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funciones de transformación atómicas
# ---------------------------------------------------------------------------


def parse_percentage(series: pd.Series) -> pd.Series:
    """Convierte strings de porcentaje a float en escala [0, 1].

    Args:
        series: Serie con valores como "94.01%" o "100.00%".

    Returns:
        Serie float con valores entre 0.0 y 1.0.

    Example:
        >>> parse_percentage(pd.Series(["94.01%", "100.00%"]))
        0    0.9401
        1    1.0000
    """
    return series.str.replace("%", "", regex=False).astype(float) / 100


def parse_hhmmss_to_seconds(series: pd.Series) -> pd.Series:
    """Convierte strings HH:MM:SS a enteros de segundos.

    Args:
        series: Serie con valores como "0:02:14" o "1:05:30".

    Returns:
        Serie int con la duración total en segundos.

    Example:
        >>> parse_hhmmss_to_seconds(pd.Series(["0:00:17", "0:02:14"]))
        0     17
        1    134
    """
    # pd.to_timedelta acepta "0:02:14" si se le agrega prefijo de horas cuando faltan
    # El formato del CSV ya incluye horas (H:MM:SS), así que funciona directo
    return pd.to_timedelta(series).dt.total_seconds().astype(int)


# ---------------------------------------------------------------------------
# Pipeline completo
# ---------------------------------------------------------------------------


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las transformaciones al DataFrame crudo.

    Transformaciones aplicadas:
        1. Elimina la columna Index (row number redundante).
        2. Renombra columnas a snake_case.
        3. Parsea porcentajes (Answer Rate, Service Level) a float [0, 1].
        4. Parsea tiempos HH:MM:SS (Answer Speed, Talk Duration, Waiting Time) a segundos int.

    Args:
        df: DataFrame crudo cargado con load_raw().

    Returns:
        DataFrame limpio con tipos correctos y nombres estandarizados.
    """
    result = df.copy()

    # 1. Eliminar columna Index — es solo un row number, no una variable
    result = result.drop(columns=[RAW_COLS["index"]])

    # 2. Renombrar columnas a snake_case
    rename_map = {
        RAW_COLS["incoming"]:      CLEAN_COLS["incoming"],
        RAW_COLS["answered"]:      CLEAN_COLS["answered"],
        RAW_COLS["answer_rate"]:   CLEAN_COLS["answer_rate"],
        RAW_COLS["abandoned"]:     CLEAN_COLS["abandoned"],
        RAW_COLS["answer_speed"]:  CLEAN_COLS["answer_speed"],
        RAW_COLS["talk_duration"]: CLEAN_COLS["talk_duration"],
        RAW_COLS["waiting_time"]:  CLEAN_COLS["waiting_time"],
        RAW_COLS["service_level"]: CLEAN_COLS["service_level"],
    }
    result = result.rename(columns=rename_map)

    # 3. Parsear porcentajes
    result[CLEAN_COLS["answer_rate"]] = parse_percentage(result[CLEAN_COLS["answer_rate"]])
    result[CLEAN_COLS["service_level"]] = parse_percentage(result[CLEAN_COLS["service_level"]])

    # 4. Parsear tiempos HH:MM:SS → segundos
    for key in ("answer_speed", "talk_duration", "waiting_time"):
        col = CLEAN_COLS[key]
        result[col] = parse_hhmmss_to_seconds(result[col])

    logger.info(
        "Limpieza completa: %d filas, %d columnas. Tipos: %s",
        len(result),
        len(result.columns),
        result.dtypes.to_dict(),
    )
    return result


def save_processed(df: pd.DataFrame, path: Path | str | None = None) -> Path:
    """Guarda el DataFrame limpio en data/processed/.

    Args:
        df: DataFrame limpio generado por clean().
        path: Ruta de destino. Si es None usa data/processed/call_center_clean.csv.

    Returns:
        Path al archivo guardado.
    """
    dest = Path(path) if path else _DEFAULT_PROCESSED
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    logger.info("CSV procesado guardado: %s", dest)
    return dest


# ---------------------------------------------------------------------------
# Entry point — ejecutar como script: python -m call_center.cleaning
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    raw = load_raw()
    clean_df = clean(raw)
    out = save_processed(clean_df)
    print(f"Listo. CSV procesado en: {out}")
    print(clean_df.dtypes)
