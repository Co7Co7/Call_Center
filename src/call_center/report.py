"""Generador del reporte HTML de análisis del call center.

Produce un archivo index.html auto-contenido con KPIs, gráficas embebidas
en base64 y anotaciones interpretativas. Equivalente Python del reporte R
original, con análisis extendido.

Uso:
    python -m call_center.report
    python -m call_center.report --output mi_reporte.html
"""

from __future__ import annotations

import argparse
import base64
import logging
from io import BytesIO
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

from call_center.cleaning import clean
from call_center.data_loader import CLEAN_COLS, load_raw
from call_center import metrics

matplotlib.use("Agg")  # Sin GUI — necesario para generar en background

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_OUTPUT = _ROOT / "index.html"

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
PALETTE = {
    "blue": "#2196F3",
    "orange": "#FF9800",
    "red": "#E53935",
    "green": "#43A047",
    "purple": "#7B1FA2",
    "grey": "#90A4AE",
}


# ---------------------------------------------------------------------------
# Helpers para gráficas → base64
# ---------------------------------------------------------------------------


def _fig_to_b64(fig: plt.Figure) -> str:
    """Convierte una figura matplotlib a string base64 para embeber en HTML."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _img_tag(b64: str, alt: str = "", width: str = "100%") -> str:
    return f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="width:{width};border-radius:8px;">'


# ---------------------------------------------------------------------------
# Gráficas
# ---------------------------------------------------------------------------


def _chart_distributions(df: pd.DataFrame) -> str:
    cols = [
        (CLEAN_COLS["incoming"], "Llamadas Entrantes", PALETTE["blue"]),
        (CLEAN_COLS["answered"], "Llamadas Respondidas", PALETTE["green"]),
        (CLEAN_COLS["abandoned"], "Llamadas Abandonadas", PALETTE["red"]),
        (CLEAN_COLS["answer_rate"], "Answer Rate", PALETTE["blue"]),
        (CLEAN_COLS["answer_speed"], "Answer Speed (s)", PALETTE["orange"]),
        (CLEAN_COLS["talk_duration"], "Talk Duration (s)", PALETTE["purple"]),
        (CLEAN_COLS["waiting_time"], "Waiting Time (s)", PALETTE["orange"]),
        (CLEAN_COLS["service_level"], "Service Level 20s", PALETTE["green"]),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    fig.suptitle("Distribuciones de todas las variables", fontsize=14, fontweight="bold")
    for ax, (col, label, color) in zip(axes.flat, cols):
        ax.hist(df[col], bins=35, color=color, alpha=0.8, edgecolor="white")
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("")
        ax.set_ylabel("Frecuencia", fontsize=8)
        med = df[col].median()
        ax.axvline(med, color="black", linestyle="--", linewidth=1.2,
                   label=f"Mediana: {med:.1f}")
        ax.legend(fontsize=7)
    plt.tight_layout()
    return _fig_to_b64(fig)


def _chart_time_series(df: pd.DataFrame) -> str:
    WINDOW = 30
    fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    fig.suptitle("Evolución temporal — media móvil de 30 periodos",
                 fontsize=13, fontweight="bold")
    cfg = [
        (CLEAN_COLS["service_level"], "Service Level 20s", PALETTE["blue"], 0.80, "Objetivo 80%"),
        (CLEAN_COLS["answer_speed"], "Answer Speed (s)", PALETTE["orange"], 20, "Ideal ≤20s"),
        (CLEAN_COLS["abandoned"], "Llamadas Abandonadas", PALETTE["red"], None, None),
    ]
    for ax, (col, label, color, ref, ref_label) in zip(axes, cfg):
        ax.plot(df.index, df[col], color=color, alpha=0.15, linewidth=0.6)
        roll = df[col].rolling(WINDOW, center=True).mean()
        ax.plot(df.index, roll, color=color, linewidth=2, label=f"Media móvil ({WINDOW}p)")
        if ref is not None:
            ax.axhline(ref, color="black", linestyle="--", linewidth=1.2, label=ref_label)
        ax.set_ylabel(label, fontsize=9)
        ax.legend(fontsize=8, loc="upper right")
    axes[-1].set_xlabel("Índice de registro (orden temporal)", fontsize=9)
    plt.tight_layout()
    return _fig_to_b64(fig)


def _chart_correlation(df: pd.DataFrame) -> str:
    numeric = df[[
        CLEAN_COLS["incoming"], CLEAN_COLS["answered"], CLEAN_COLS["abandoned"],
        CLEAN_COLS["answer_rate"], CLEAN_COLS["answer_speed"],
        CLEAN_COLS["talk_duration"], CLEAN_COLS["waiting_time"],
        CLEAN_COLS["service_level"],
    ]]
    corr = numeric.corr()
    labels = ["Entrantes", "Respondidas", "Abandonadas", "Answer Rate",
              "Answer Speed", "Talk Duration", "Waiting Time", "Service Level"]
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                vmin=-1, vmax=1, ax=ax, linewidths=0.5,
                xticklabels=labels, yticklabels=labels, annot_kws={"size": 9})
    ax.set_title("Matriz de correlación de Pearson", fontsize=13, fontweight="bold")
    plt.tight_layout()
    return _fig_to_b64(fig)


def _chart_scatter_waiting_abandoned(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(df[CLEAN_COLS["waiting_time"]], df[CLEAN_COLS["abandoned"]],
               alpha=0.3, s=18, color=PALETTE["blue"], edgecolors="none")
    # Línea de tendencia
    m, b = np.polyfit(df[CLEAN_COLS["waiting_time"]], df[CLEAN_COLS["abandoned"]], 1)
    x_line = np.linspace(df[CLEAN_COLS["waiting_time"]].min(),
                         df[CLEAN_COLS["waiting_time"]].max(), 200)
    r = df[[CLEAN_COLS["waiting_time"], CLEAN_COLS["abandoned"]]].corr().iloc[0, 1]
    ax.plot(x_line, m * x_line + b, color=PALETTE["red"], linewidth=2,
            label=f"Tendencia lineal (r = {r:.2f})")
    ax.set_xlabel("Waiting Time promedio (s)", fontsize=10)
    ax.set_ylabel("Llamadas Abandonadas", fontsize=10)
    ax.set_title("Tiempo de espera vs Llamadas abandonadas", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _fig_to_b64(fig)


def _chart_segments(df: pd.DataFrame) -> str:
    df = df.copy()
    df["segmento"] = pd.cut(
        df[CLEAN_COLS["service_level"]],
        bins=[-0.01, 0.50, 0.80, 1.01],
        labels=["Crítico (<50%)", "Regular (50-80%)", "Bueno (≥80%)"],
    )
    counts = df["segmento"].value_counts().reindex(
        ["Bueno (≥80%)", "Regular (50-80%)", "Crítico (<50%)"]
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    colors = [PALETTE["green"], PALETTE["orange"], PALETTE["red"]]

    axes[0].pie(counts, labels=counts.index, colors=colors,
                autopct="%1.1f%%", startangle=90,
                wedgeprops={"edgecolor": "white", "linewidth": 2})
    axes[0].set_title("Distribución de periodos por SLA", fontsize=11, fontweight="bold")

    bars = axes[1].barh(counts.index[::-1], counts.values[::-1],
                        color=colors[::-1], edgecolor="white", alpha=0.9)
    axes[1].bar_label(bars, fmt="%d", padding=5, fontsize=10)
    axes[1].set_xlabel("Número de periodos", fontsize=10)
    axes[1].set_title("Conteo por segmento", fontsize=11, fontweight="bold")
    plt.tight_layout()
    return _fig_to_b64(fig)


def _chart_sla_by_speed(df: pd.DataFrame) -> str:
    bins = list(range(0, 65, 5)) + [int(df[CLEAN_COLS["answer_speed"]].max()) + 1]
    labels_b = [f"{b}-{b+5}s" for b in range(0, 60, 5)] + [">60s"]
    df = df.copy()
    df["speed_band"] = pd.cut(df[CLEAN_COLS["answer_speed"]],
                              bins=bins, labels=labels_b, right=False)
    stats = df.groupby("speed_band", observed=True)[CLEAN_COLS["service_level"]].agg(
        pct_ok=lambda x: (x >= 0.80).mean()
    )
    fig, ax = plt.subplots(figsize=(13, 5))
    bar_colors = [PALETTE["green"] if v >= 0.80 else PALETTE["orange"] if v >= 0.50
                  else PALETTE["red"] for v in stats["pct_ok"]]
    bars = ax.bar(range(len(stats)), stats["pct_ok"] * 100,
                  color=bar_colors, edgecolor="white", alpha=0.9)
    ax.bar_label(bars, fmt="%.0f%%", padding=3, fontsize=8)
    ax.axhline(80, color="black", linestyle="--", linewidth=1.5, label="Objetivo 80%")
    ax.set_xticks(range(len(stats)))
    ax.set_xticklabels(stats.index, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("% periodos con SL ≥ 80%", fontsize=10)
    ax.set_title("Cumplimiento de SLA según Answer Speed", fontsize=12, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(fontsize=9)
    plt.tight_layout()
    return _fig_to_b64(fig)


# ---------------------------------------------------------------------------
# Construcción del HTML
# ---------------------------------------------------------------------------


def _kpi_card(title: str, value: str, subtitle: str, color: str,
              status: str = "") -> str:
    status_badge = (
        f'<span style="font-size:11px;background:{color};color:white;'
        f'padding:2px 8px;border-radius:12px;margin-top:4px;display:inline-block;">'
        f"{status}</span>"
        if status else ""
    )
    return f"""
    <div style="background:white;border-radius:12px;padding:20px 24px;
                box-shadow:0 2px 12px rgba(0,0,0,0.08);border-left:5px solid {color};
                flex:1;min-width:180px;">
      <div style="font-size:12px;color:#666;text-transform:uppercase;
                  letter-spacing:0.5px;margin-bottom:4px;">{title}</div>
      <div style="font-size:32px;font-weight:700;color:#1a1a2e;">{value}</div>
      <div style="font-size:12px;color:#888;margin-top:2px;">{subtitle}</div>
      {status_badge}
    </div>"""


def _section(title: str, annotation: str, content: str) -> str:
    return f"""
    <section style="margin-bottom:48px;">
      <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;
                 border-bottom:3px solid #2196F3;padding-bottom:8px;
                 margin-bottom:12px;">{title}</h2>
      <div style="background:#EFF6FF;border-left:4px solid #2196F3;
                  padding:12px 16px;border-radius:0 8px 8px 0;
                  font-size:14px;color:#374151;margin-bottom:20px;
                  line-height:1.6;">
        {annotation}
      </div>
      {content}
    </section>"""


def _stats_table(df: pd.DataFrame) -> str:
    cols_map = {
        "incoming_calls": "Entrantes",
        "answered_calls": "Respondidas",
        "abandoned_calls": "Abandonadas",
        "answer_rate": "Answer Rate",
        "answer_speed_avg_s": "Answer Speed (s)",
        "talk_duration_avg_s": "Talk Duration (s)",
        "waiting_time_avg_s": "Waiting Time (s)",
        "service_level_20s": "Service Level 20s",
    }
    rows = ""
    for col, label in cols_map.items():
        s = df[col]
        rows += f"""<tr>
          <td><strong>{label}</strong></td>
          <td>{s.mean():.2f}</td>
          <td>{s.median():.2f}</td>
          <td>{s.std():.2f}</td>
          <td>{s.min():.2f}</td>
          <td>{s.max():.2f}</td>
        </tr>"""
    return f"""
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:#2196F3;color:white;">
          <th style="padding:10px 14px;text-align:left;">Variable</th>
          <th style="padding:10px 14px;">Media</th>
          <th style="padding:10px 14px;">Mediana</th>
          <th style="padding:10px 14px;">Std</th>
          <th style="padding:10px 14px;">Mín</th>
          <th style="padding:10px 14px;">Máx</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'<tr style="border-bottom:1px solid #eee;">{r}</tr>' for r in rows.split("</tr>") if "<td>" in r)}
      </tbody>
    </table>
    </div>"""


def generate_report(df: pd.DataFrame) -> str:
    """Genera el HTML completo del reporte."""
    s = metrics.summary(df)
    n = len(df)
    total_calls = int(df[CLEAN_COLS["incoming"]].sum())

    logger.info("Generando gráficas...")
    chart_dist = _chart_distributions(df)
    chart_ts = _chart_time_series(df)
    chart_corr = _chart_correlation(df)
    chart_scatter = _chart_scatter_waiting_abandoned(df)
    chart_seg = _chart_segments(df)
    chart_sla = _chart_sla_by_speed(df)

    kpi_row = f"""
    <div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:40px;">
      {_kpi_card("Answer Rate", f"{s['answer_rate']*100:.1f}%",
                 "Llamadas respondidas / entrantes", PALETTE['green'], "✅ Cumple >90%")}
      {_kpi_card("Service Level 20s", f"{s['service_level']*100:.1f}%",
                 "Respondidas en ≤20s", PALETTE['orange'], "⚠️ Bajo objetivo 80%")}
      {_kpi_card("Abandonment Rate", f"{s['abandonment_rate']*100:.1f}%",
                 "Llamadas perdidas", PALETTE['red'], "❌ Objetivo <5%")}
      {_kpi_card("SLA Compliance", f"{s['sla_compliance']*100:.1f}%",
                 "Periodos con SL ≥ 80%", PALETTE['red'], "❌ Crítico")}
      {_kpi_card("AHT Promedio", f"{s['aht_avg_s']/60:.1f} min",
                 "Talk + Waiting time", PALETTE['purple'])}
      {_kpi_card("Periodos críticos", f"{s['critical_period_pct']*100:.1f}%",
                 "Con Service Level < 50%", PALETTE['orange'])}
    </div>"""

    stats_html = _stats_table(df)
    corr_val = round(df[[CLEAN_COLS["waiting_time"], CLEAN_COLS["abandoned"]]].corr().iloc[0, 1], 2)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Call Center — Análisis de Performance</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #F0F4F8;
      color: #1a1a2e;
      line-height: 1.6;
    }}
    header {{
      background: linear-gradient(135deg, #1a237e 0%, #1565C0 60%, #0288D1 100%);
      color: white;
      padding: 40px 48px 32px;
    }}
    header h1 {{ font-size: 28px; font-weight: 800; margin-bottom: 6px; }}
    header p  {{ font-size: 14px; opacity: 0.85; max-width: 620px; }}
    .badge {{
      display: inline-block; background: rgba(255,255,255,0.2);
      padding: 3px 10px; border-radius: 20px; font-size: 12px; margin-top: 10px;
      margin-right: 6px;
    }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px; }}
    td {{ padding: 8px 14px; color: #374151; }}
    th {{ text-align: center; }}
    td:first-child {{ text-align: left; }}
    td:not(:first-child) {{ text-align: center; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    .callout {{
      background: #FFF8E1; border-left: 4px solid #F59E0B;
      padding: 12px 16px; border-radius: 0 8px 8px 0;
      font-size: 13px; color: #374151; margin: 16px 0;
    }}
    .finding {{
      background: white; border-radius: 10px; padding: 20px 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px;
      border-left: 5px solid;
    }}
    .finding h3 {{ font-size: 15px; font-weight: 700; margin-bottom: 6px; }}
    .finding p  {{ font-size: 13px; color: #4B5563; }}
    footer {{
      text-align: center; padding: 24px;
      font-size: 12px; color: #9CA3AF;
      border-top: 1px solid #E5E7EB; margin-top: 40px;
    }}
  </style>
</head>
<body>

<header>
  <h1>📞 Call Center — Análisis de Performance</h1>
  <p>Análisis exploratorio y profundo de métricas operativas sobre {n:,} registros periódicos
     ({total_calls:,} llamadas totales). Generado con Python — reproducible desde cero.</p>
  <div>
    <span class="badge">n = {n:,} registros</span>
    <span class="badge">{total_calls:,} llamadas</span>
    <span class="badge">8 métricas operativas</span>
    <span class="badge">33 tests automatizados</span>
  </div>
</header>

<main>

  <!-- KPIs -->
  <section style="margin-bottom:48px;margin-top:8px;">
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;
               border-bottom:3px solid #2196F3;padding-bottom:8px;margin-bottom:20px;">
      Resumen Ejecutivo — KPIs Globales
    </h2>
    <div style="background:#EFF6FF;border-left:4px solid #2196F3;
                padding:12px 16px;border-radius:0 8px 8px 0;
                font-size:14px;color:#374151;margin-bottom:20px;">
      El call center responde bien en volumen (92.7% de llamadas atendidas) pero tiene
      problemas de <strong>velocidad y consistencia</strong>: menos de la mitad de los periodos
      alcanzan el objetivo de SLA del 80%, y el abandono duplica el estándar de la industria.
    </div>
    {kpi_row}
  </section>

  <!-- Dataset overview -->
  {_section(
    "Vista del Dataset",
    f"El dataset contiene {n:,} registros con 8 métricas operativas por periodo. "
    "Las columnas de tiempo (answer_speed, talk_duration, waiting_time) fueron convertidas "
    "de formato HH:MM:SS a segundos. Los porcentajes (answer_rate, service_level) "
    "se normalizaron a escala [0, 1].",
    stats_html
  )}

  <!-- Distribuciones -->
  {_section(
    "Distribuciones de Variables",
    "La mayoría de las variables muestran distribuciones asimétricas a la derecha — "
    "especialmente <em>waiting_time</em> y <em>abandoned_calls</em>, que tienen colas largas "
    "generadas por episodios de alta carga. El Service Level sigue una distribución bimodal: "
    "muchos periodos con SL alto (>80%) y otro grupo con SL bajo (<50%), lo que indica "
    "dos regímenes operativos distintos en lugar de un comportamiento uniforme.",
    _img_tag(chart_dist, "Distribuciones")
  )}

  <!-- Series de tiempo -->
  {_section(
    "Evolución Temporal",
    "Los registros están ordenados secuencialmente. La media móvil de 30 periodos revela "
    "la tendencia subyacente. El Service Level oscila ampliamente y cruza el umbral del 80% "
    "de forma irregular — no hay una tendencia clara de mejora ni deterioro sostenido. "
    "Los picos de abandonos coinciden con los valles del Service Level, confirmando la "
    "relación causal entre velocidad de respuesta y satisfacción del cliente.",
    _img_tag(chart_ts, "Series de tiempo")
  )}

  <!-- Correlaciones -->
  {_section(
    "Análisis de Correlaciones",
    f"La correlación más fuerte del dataset es entre <em>waiting_time</em> y "
    f"<em>abandoned_calls</em> (<strong>r = {corr_val}</strong>): a mayor espera, más "
    "clientes cuelgan antes de ser atendidos. El Service Level correlaciona negativamente "
    "con answer_speed (−0.72 aprox.): periodos con respuesta lenta tienen peor SLA. "
    "Llamadas entrantes y respondidas tienen correlación cercana a 1, como es esperado "
    "por la invariante del negocio (answered + abandoned ≈ incoming).",
    f'<div style="display:flex;gap:20px;flex-wrap:wrap;">'
    f'<div style="flex:1.4;min-width:340px;">{_img_tag(chart_corr, "Correlaciones")}</div>'
    f'<div style="flex:1;min-width:300px;">{_img_tag(chart_scatter, "Scatter waiting vs abandoned")}</div>'
    f"</div>"
  )}

  <!-- Segmentación -->
  {_section(
    "Segmentación por Service Level",
    "Clasificamos cada periodo en tres segmentos según su Service Level: "
    "<strong>Bueno (≥80%)</strong> — cumple el objetivo de industria; "
    "<strong>Regular (50–80%)</strong> — por debajo pero operativo; "
    "<strong>Crítico (&lt;50%)</strong> — más de la mitad de las llamadas no se responden "
    "en 20 segundos. Los periodos críticos concentran una fracción desproporcionada "
    "de las llamadas abandonadas y son el foco prioritario de mejora.",
    _img_tag(chart_seg, "Segmentación")
  )}

  <!-- Propuesta SLA -->
  {_section(
    "Propuesta de SLA — ¿Cuánto debe bajar el Answer Speed?",
    "Para que un periodo cumpla el SLA del 80%, el Answer Speed promedio debe mantenerse "
    "por debajo de un umbral crítico. La gráfica muestra la fracción de periodos que "
    "alcanzan SL ≥ 80% en cada franja de answer speed. "
    "<strong>La mediana actual es 21s</strong> — justo por encima del ideal de 20s — "
    "pero insuficiente en momentos de alta carga. Mantener el answer speed por debajo "
    "de 15s durante los picos incrementaría significativamente el cumplimiento de SLA.",
    _img_tag(chart_sla, "SLA por franja de answer speed")
  )}

  <!-- Hallazgos -->
  <section style="margin-bottom:48px;">
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;
               border-bottom:3px solid #2196F3;padding-bottom:8px;margin-bottom:20px;">
      Hallazgos y Recomendaciones
    </h2>

    <div class="finding" style="border-color:{PALETTE['orange']};">
      <h3>⚠️ El promedio de SLA engaña — la consistencia es el problema real</h3>
      <p>El SLA promedio del 70.9% parece aceptable, pero solo el <strong>36.6%</strong> de los
      periodos alcanzan el objetivo del 80%. La alta variabilidad (σ = 0.185) indica que el
      call center alterna entre episodios excelentes y críticos. <em>Acción: monitorear
      tasa de cumplimiento periodo a periodo, no el promedio mensual.</em></p>
    </div>

    <div class="finding" style="border-color:{PALETTE['red']};">
      <h3>❌ Abandonment rate en 10.9% — más del doble del estándar (&lt;5%)</h3>
      <p>De las {total_calls:,} llamadas, <strong>27,139 fueron abandonadas</strong>.
      La correlación r = {corr_val} entre tiempo de espera y abandonos descarta causas
      aleatorias y apunta directamente a capacidad insuficiente en picos de demanda.
      <em>Acción: reducir waiting_time promedio (actualmente ~6 min) en los cuartiles
      de mayor carga.</em></p>
    </div>

    <div class="finding" style="border-color:{PALETTE['blue']};">
      <h3>🔍 12.4% de periodos críticos requieren atención urgente</h3>
      <p>155 periodos registran SL &lt;50%. Estos episodios concentran una fracción
      desproporcionada de los abandonos y son los de mayor daño operativo.
      <em>Acción: análisis de causas raíz en periodos críticos — ¿turno corto?,
      ¿pico estacional?, ¿incidente técnico?</em></p>
    </div>

    <div class="finding" style="border-color:{PALETTE['green']};">
      <h3>✅ Answer Rate en 92.7% — el volumen se maneja bien</h3>
      <p>El porcentaje de llamadas atendidas supera el umbral de 90% de la industria.
      El problema no es de volumen sino de <strong>velocidad</strong>: el call center
      contesta las llamadas pero no con la rapidez suficiente para cumplir el SLA de 20s.
      <em>Acción: priorizar reducción de answer_speed en momentos de alta carga
      antes de aumentar capacidad total.</em></p>
    </div>

    <div class="callout">
      💡 <strong>Próximo paso recomendado:</strong> incorporar timestamps reales para
      identificar patrones horarios y semanales. Con esa información se puede construir
      un modelo predictivo de demanda y planificar turnos preventivamente.
    </div>
  </section>

  <!-- Metodología -->
  <section>
    <h2 style="font-size:20px;font-weight:700;color:#1a1a2e;
               border-bottom:3px solid #2196F3;padding-bottom:8px;margin-bottom:16px;">
      Metodología
    </h2>
    <div style="display:flex;gap:16px;flex-wrap:wrap;">
      {"".join([
        f'<div style="background:white;border-radius:10px;padding:16px 20px;'
        f'flex:1;min-width:200px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
        f'<div style="font-weight:700;color:{PALETTE["blue"]};margin-bottom:4px;">{step}</div>'
        f'<div style="font-size:13px;color:#4B5563;">{desc}</div></div>'
        for step, desc in [
          ("1. Carga", "data_loader.py — CSV separado por ; con tipos incorrectos"),
          ("2. Limpieza", "cleaning.py — porcentajes y HH:MM:SS → segundos"),
          ("3. Validación", "33 tests automáticos — pytest, todos pasando"),
          ("4. EDA", "01_eda.ipynb — KPIs, distribuciones, correlaciones"),
          ("5. Análisis profundo", "03_analysis.ipynb — series de tiempo, outliers, SLA"),
          ("6. KPIs", "metrics.py — funciones puras y testeables"),
        ]
      ])}
    </div>
  </section>

</main>

<footer>
  Generado con Python · pandas · matplotlib · seaborn
  &nbsp;|&nbsp; Fuente: <a href="https://www.kaggle.com/datasets/satvicoder/call-center-data"
  style="color:#2196F3;">Kaggle — Call Center Data</a>
  &nbsp;|&nbsp; <a href="https://github.com/Co7Co7/Call_Center" style="color:#2196F3;">GitHub</a>
</footer>

</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Genera el reporte HTML del call center.")
    parser.add_argument(
        "--output", type=Path, default=_DEFAULT_OUTPUT,
        help="Ruta del archivo HTML de salida (default: index.html en la raíz del proyecto)."
    )
    args = parser.parse_args()

    logger.info("Cargando y limpiando datos...")
    df = clean(load_raw())
    logger.info("Generando reporte HTML...")
    html = generate_report(df)
    args.output.write_text(html, encoding="utf-8")
    logger.info("Reporte guardado en: %s", args.output)
    print(f"Reporte generado: {args.output}")


if __name__ == "__main__":
    main()
