"""Validaciones de invariantes del negocio sobre el dataset procesado.

Los valores de referencia (answer_rate ~0.927, service_level ~0.709, etc.)
provienen del reporte R original (index.html) y sirven para verificar que
el pipeline Python reproduce los mismos resultados.
"""

import pandas as pd
from call_center.data_loader import CLEAN_COLS

# ---------------------------------------------------------------------------
# Estructura del dataset
# ---------------------------------------------------------------------------


def test_row_count(df_clean: pd.DataFrame) -> None:
    assert len(df_clean) == 1251


def test_column_count(df_clean: pd.DataFrame) -> None:
    assert len(df_clean.columns) == 8


def test_no_missing_values(df_clean: pd.DataFrame) -> None:
    assert df_clean.isnull().sum().sum() == 0


def test_column_names(df_clean: pd.DataFrame) -> None:
    expected = set(CLEAN_COLS.values())
    assert expected == set(df_clean.columns)


# ---------------------------------------------------------------------------
# Tipos de datos
# ---------------------------------------------------------------------------


def test_integer_columns(df_clean: pd.DataFrame) -> None:
    int_cols = [
        CLEAN_COLS["incoming"],
        CLEAN_COLS["answered"],
        CLEAN_COLS["abandoned"],
        CLEAN_COLS["answer_speed"],
        CLEAN_COLS["talk_duration"],
        CLEAN_COLS["waiting_time"],
    ]
    for col in int_cols:
        assert pd.api.types.is_integer_dtype(df_clean[col]), f"{col} debe ser int"


def test_float_columns(df_clean: pd.DataFrame) -> None:
    float_cols = [CLEAN_COLS["answer_rate"], CLEAN_COLS["service_level"]]
    for col in float_cols:
        assert pd.api.types.is_float_dtype(df_clean[col]), f"{col} debe ser float"


# ---------------------------------------------------------------------------
# Rangos válidos
# ---------------------------------------------------------------------------


def test_answer_rate_range(df_clean: pd.DataFrame) -> None:
    col = CLEAN_COLS["answer_rate"]
    assert df_clean[col].between(0, 1).all(), "answer_rate debe estar en [0, 1]"


def test_service_level_range(df_clean: pd.DataFrame) -> None:
    col = CLEAN_COLS["service_level"]
    assert df_clean[col].between(0, 1).all(), "service_level_20s debe estar en [0, 1]"


def test_time_columns_non_negative(df_clean: pd.DataFrame) -> None:
    for key in ("answer_speed", "talk_duration", "waiting_time"):
        col = CLEAN_COLS[key]
        assert (df_clean[col] >= 0).all(), f"{col} no puede ser negativo"


def test_call_counts_non_negative(df_clean: pd.DataFrame) -> None:
    for key in ("incoming", "answered", "abandoned"):
        col = CLEAN_COLS[key]
        assert (df_clean[col] >= 0).all(), f"{col} no puede ser negativo"


# ---------------------------------------------------------------------------
# Invariantes del negocio
# ---------------------------------------------------------------------------


def test_answered_le_incoming(df_clean: pd.DataFrame) -> None:
    """No puede haber más llamadas respondidas que entrantes."""
    assert (df_clean[CLEAN_COLS["answered"]] <= df_clean[CLEAN_COLS["incoming"]]).all()


def test_abandoned_le_incoming(df_clean: pd.DataFrame) -> None:
    """No puede haber más llamadas abandonadas que entrantes."""
    assert (df_clean[CLEAN_COLS["abandoned"]] <= df_clean[CLEAN_COLS["incoming"]]).all()


def test_answered_plus_abandoned_eq_incoming(df_clean: pd.DataFrame) -> None:
    """Respondidas + abandonadas debe igualar entrantes (tolerancia ±1 por redondeo)."""
    diff = (
        df_clean[CLEAN_COLS["incoming"]]
        - df_clean[CLEAN_COLS["answered"]]
        - df_clean[CLEAN_COLS["abandoned"]]
    ).abs()
    assert (diff <= 1).all(), f"Máxima discrepancia: {diff.max()}"


# ---------------------------------------------------------------------------
# Reproducibilidad de métricas clave (vs reporte R original)
# ---------------------------------------------------------------------------


def test_answer_rate_mean(df_clean: pd.DataFrame) -> None:
    """Answer Rate promedio debe ser ~92.7% (±1pp)."""
    mean = df_clean[CLEAN_COLS["answer_rate"]].mean()
    assert abs(mean - 0.927) < 0.01, f"Answer Rate promedio: {mean:.3f}"


def test_service_level_mean(df_clean: pd.DataFrame) -> None:
    """Service Level promedio debe ser ~70.9% (±1pp)."""
    mean = df_clean[CLEAN_COLS["service_level"]].mean()
    assert abs(mean - 0.709) < 0.01, f"Service Level promedio: {mean:.3f}"


def test_waiting_abandoned_correlation(df_clean: pd.DataFrame) -> None:
    """Correlación Waiting Time / Abandoned debe ser ~0.72 (±0.05)."""
    r = (
        df_clean[[CLEAN_COLS["waiting_time"], CLEAN_COLS["abandoned"]]]
        .corr()
        .iloc[0, 1]
    )
    assert abs(r - 0.72) < 0.05, f"Correlación waiting/abandoned: {r:.3f}"
