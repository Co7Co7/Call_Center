"""Tests del módulo metrics.py — KPIs operativos del call center."""

import pytest
import pandas as pd

from call_center import metrics


# ---------------------------------------------------------------------------
# KPIs escalares
# ---------------------------------------------------------------------------


def test_answer_rate_avg_range(df_clean: pd.DataFrame) -> None:
    result = metrics.answer_rate_avg(df_clean)
    assert 0 <= result <= 1, f"answer_rate_avg fuera de [0,1]: {result}"


def test_answer_rate_avg_value(df_clean: pd.DataFrame) -> None:
    """Debe ser ~92.7% según el reporte R original."""
    result = metrics.answer_rate_avg(df_clean)
    assert abs(result - 0.927) < 0.01, f"answer_rate_avg inesperado: {result:.3f}"


def test_abandonment_rate_range(df_clean: pd.DataFrame) -> None:
    result = metrics.abandonment_rate(df_clean)
    assert 0 <= result <= 1, f"abandonment_rate fuera de [0,1]: {result}"


def test_abandonment_rate_consistent(df_clean: pd.DataFrame) -> None:
    """answered + abandoned ≈ incoming → abandonment_rate + answer_rate ≈ 1."""
    ab = metrics.abandonment_rate(df_clean)
    ar = metrics.answer_rate_avg(df_clean)
    # No son exactamente complementarios (answer_rate es media de tasas,
    # abandonment_rate es ratio global), pero ambos deben ser razonables.
    assert ab < 0.20, f"Tasa de abandono demasiado alta: {ab:.3f}"
    assert ar > 0.80, f"Answer rate demasiado baja: {ar:.3f}"


def test_aht_avg_positive(df_clean: pd.DataFrame) -> None:
    result = metrics.aht_avg(df_clean)
    assert result > 0, f"AHT debe ser positivo: {result}"


def test_aht_avg_reasonable(df_clean: pd.DataFrame) -> None:
    """AHT = talk (~163s) + waiting (~366s) ≈ 529s. Tolerancia amplia."""
    result = metrics.aht_avg(df_clean)
    assert 300 < result < 800, f"AHT fuera de rango esperado: {result:.1f}s"


def test_service_level_avg_range(df_clean: pd.DataFrame) -> None:
    result = metrics.service_level_avg(df_clean)
    assert 0 <= result <= 1


def test_service_level_avg_value(df_clean: pd.DataFrame) -> None:
    """Debe ser ~70.9% según el reporte R original."""
    result = metrics.service_level_avg(df_clean)
    assert abs(result - 0.709) < 0.01, f"service_level_avg inesperado: {result:.3f}"


# ---------------------------------------------------------------------------
# KPIs de cumplimiento
# ---------------------------------------------------------------------------


def test_sla_compliance_rate_range(df_clean: pd.DataFrame) -> None:
    result = metrics.sla_compliance_rate(df_clean, threshold=0.80)
    assert 0 <= result <= 1


def test_sla_compliance_rate_monotone(df_clean: pd.DataFrame) -> None:
    """Exigir más SLA → menos periodos que lo cumplen."""
    low = metrics.sla_compliance_rate(df_clean, threshold=0.50)
    high = metrics.sla_compliance_rate(df_clean, threshold=0.90)
    assert low >= high, "Compliance con threshold mayor debería ser <= que con threshold menor"


def test_critical_periods_returns_dataframe(df_clean: pd.DataFrame) -> None:
    result = metrics.critical_periods(df_clean, threshold=0.50)
    assert isinstance(result, pd.DataFrame)


def test_critical_periods_below_threshold(df_clean: pd.DataFrame) -> None:
    threshold = 0.50
    result = metrics.critical_periods(df_clean, threshold=threshold)
    assert (result["service_level_20s"] < threshold).all()


def test_critical_periods_sorted(df_clean: pd.DataFrame) -> None:
    result = metrics.critical_periods(df_clean, threshold=0.50)
    assert result["service_level_20s"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# Análisis de SLA
# ---------------------------------------------------------------------------


def test_speed_threshold_returns_int_or_none(df_clean: pd.DataFrame) -> None:
    result = metrics.speed_threshold_for_sla(df_clean)
    assert result is None or isinstance(result, int)


def test_speed_threshold_positive(df_clean: pd.DataFrame) -> None:
    result = metrics.speed_threshold_for_sla(df_clean)
    if result is not None:
        assert result > 0


# ---------------------------------------------------------------------------
# Resumen ejecutivo
# ---------------------------------------------------------------------------


def test_summary_keys(df_clean: pd.DataFrame) -> None:
    expected_keys = {
        "answer_rate", "abandonment_rate", "aht_avg_s",
        "service_level", "sla_compliance",
        "critical_period_pct", "speed_threshold_s",
    }
    result = metrics.summary(df_clean)
    assert set(result.keys()) == expected_keys


def test_summary_values_in_range(df_clean: pd.DataFrame) -> None:
    result = metrics.summary(df_clean)
    for key in ("answer_rate", "abandonment_rate", "service_level",
                "sla_compliance", "critical_period_pct"):
        assert 0 <= result[key] <= 1, f"{key} fuera de [0,1]: {result[key]}"
