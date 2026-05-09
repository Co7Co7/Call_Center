"""Cálculo de KPIs operativos de call center.

Todas las funciones reciben un DataFrame limpio (salida de clean()) y devuelven
escalares o Series. Sin efectos secundarios — puras y testeables.

KPIs implementados:
    - answer_rate_avg: tasa promedio de llamadas respondidas
    - abandonment_rate: tasa de llamadas abandonadas sobre total entrante
    - aht_avg: Average Handle Time (talk + waiting)
    - service_level_avg: promedio de Service Level 20s
    - sla_compliance_rate: fracción de periodos que cumplen un umbral de SLA
    - critical_periods: periodos con SL por debajo de un umbral crítico
    - speed_threshold_for_sla: answer speed máximo para alcanzar un SLA objetivo
"""

from __future__ import annotations

import logging

import pandas as pd

from call_center.data_loader import CLEAN_COLS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# KPIs escalares (resumen global)
# ---------------------------------------------------------------------------


def answer_rate_avg(df: pd.DataFrame) -> float:
    """Tasa promedio de llamadas respondidas sobre el total entrante.

    Args:
        df: DataFrame limpio.

    Returns:
        Float en [0, 1]. Ej: 0.927 significa 92.7% respondidas.
    """
    return float(df[CLEAN_COLS["answer_rate"]].mean())


def abandonment_rate(df: pd.DataFrame) -> float:
    """Tasa global de abandono: llamadas abandonadas / llamadas entrantes totales.

    Se calcula a nivel de dataset completo (no promedio de tasas por periodo),
    lo que evita sesgo cuando los volúmenes varían mucho entre periodos.

    Args:
        df: DataFrame limpio.

    Returns:
        Float en [0, 1]. Ej: 0.073 significa 7.3% de abandono.
    """
    total_abandoned = df[CLEAN_COLS["abandoned"]].sum()
    total_incoming = df[CLEAN_COLS["incoming"]].sum()
    if total_incoming == 0:
        logger.warning("Total de llamadas entrantes es 0 — abandonment_rate devuelve 0.")
        return 0.0
    return float(total_abandoned / total_incoming)


def aht_avg(df: pd.DataFrame) -> float:
    """Average Handle Time (AHT) promedio en segundos.

    AHT = talk_duration + waiting_time (tiempo de conversación + tiempo de espera).
    Refleja el tiempo total que el sistema ocupa por llamada atendida.

    Args:
        df: DataFrame limpio.

    Returns:
        Float en segundos.
    """
    talk = df[CLEAN_COLS["talk_duration"]]
    wait = df[CLEAN_COLS["waiting_time"]]
    return float((talk + wait).mean())


def service_level_avg(df: pd.DataFrame) -> float:
    """Promedio del Service Level 20s sobre todos los periodos.

    Args:
        df: DataFrame limpio.

    Returns:
        Float en [0, 1]. Ej: 0.709 significa 70.9% de SL promedio.
    """
    return float(df[CLEAN_COLS["service_level"]].mean())


# ---------------------------------------------------------------------------
# KPIs de cumplimiento (con umbral parametrizable)
# ---------------------------------------------------------------------------


def sla_compliance_rate(df: pd.DataFrame, threshold: float = 0.80) -> float:
    """Fracción de periodos que cumplen el umbral de Service Level.

    Args:
        df: DataFrame limpio.
        threshold: Umbral de SLA a cumplir. Default 0.80 (80% industria).

    Returns:
        Float en [0, 1]. Ej: 0.55 significa que el 55% de los periodos
        alcanzan el SLA objetivo.
    """
    col = df[CLEAN_COLS["service_level"]]
    return float((col >= threshold).mean())


def critical_periods(df: pd.DataFrame, threshold: float = 0.50) -> pd.DataFrame:
    """Devuelve los periodos con Service Level por debajo del umbral crítico.

    Args:
        df: DataFrame limpio.
        threshold: Umbral crítico. Default 0.50 (50%).

    Returns:
        DataFrame filtrado con los periodos críticos, ordenado por SL ascendente.
    """
    col = CLEAN_COLS["service_level"]
    mask = df[col] < threshold
    result = df[mask].sort_values(col)
    logger.info(
        "Periodos críticos (SL < %.0f%%): %d de %d (%.1f%%)",
        threshold * 100,
        len(result),
        len(df),
        len(result) / len(df) * 100,
    )
    return result


# ---------------------------------------------------------------------------
# Análisis de SLA (propuesta operativa)
# ---------------------------------------------------------------------------


def speed_threshold_for_sla(
    df: pd.DataFrame,
    sla_target: float = 0.80,
    compliance_target: float = 0.80,
    band_width: int = 5,
) -> int | None:
    """Answer speed máximo (segundos) para alcanzar el SLA objetivo.

    Divide los registros en franjas de answer_speed de `band_width` segundos
    y busca la primera franja donde la tasa de cumplimiento del SLA objetivo
    supera `compliance_target`.

    Args:
        df: DataFrame limpio.
        sla_target: Umbral de Service Level a cumplir por periodo. Default 0.80.
        compliance_target: Fracción de periodos dentro de la franja que deben
            alcanzar sla_target. Default 0.80.
        band_width: Ancho de cada franja de answer_speed en segundos. Default 5.

    Returns:
        Límite superior de la franja óptima en segundos, o None si ninguna franja
        cumple el objetivo.

    Example:
        >>> threshold = speed_threshold_for_sla(df)
        >>> print(f"Mantener answer_speed <= {threshold}s para SLA >= 80%")
    """
    max_speed = int(df[CLEAN_COLS["answer_speed"]].max())
    bins = list(range(0, max_speed + band_width, band_width))

    for lo, hi in zip(bins, bins[1:]):
        band = df[
            df[CLEAN_COLS["answer_speed"]].between(lo, hi - 1)
        ]
        if len(band) == 0:
            continue
        compliance = (band[CLEAN_COLS["service_level"]] >= sla_target).mean()
        if compliance >= compliance_target:
            logger.info(
                "Umbral óptimo: answer_speed <= %ds (%.0f%% de periodos cumplen SLA %.0f%%)",
                hi,
                compliance * 100,
                sla_target * 100,
            )
            return hi

    logger.warning(
        "Ninguna franja de answer_speed cumple el objetivo SLA %.0f%% con compliance >= %.0f%%.",
        sla_target * 100,
        compliance_target * 100,
    )
    return None


# ---------------------------------------------------------------------------
# Resumen ejecutivo (todos los KPIs de una vez)
# ---------------------------------------------------------------------------


def summary(df: pd.DataFrame, sla_threshold: float = 0.80) -> dict[str, float | int | None]:
    """Calcula todos los KPIs y los devuelve en un diccionario.

    Args:
        df: DataFrame limpio.
        sla_threshold: Umbral de SLA para compliance y periodos críticos.

    Returns:
        Dict con claves: answer_rate, abandonment_rate, aht_avg_s, service_level,
        sla_compliance, critical_period_pct, speed_threshold_s.
    """
    return {
        "answer_rate": round(answer_rate_avg(df), 4),
        "abandonment_rate": round(abandonment_rate(df), 4),
        "aht_avg_s": round(aht_avg(df), 1),
        "service_level": round(service_level_avg(df), 4),
        "sla_compliance": round(sla_compliance_rate(df, sla_threshold), 4),
        "critical_period_pct": round(
            len(critical_periods(df, threshold=0.50)) / len(df), 4
        ),
        "speed_threshold_s": speed_threshold_for_sla(df),
    }
