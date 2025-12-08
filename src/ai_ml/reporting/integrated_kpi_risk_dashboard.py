from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
import os

"""
AI4OHS-HYBRID
Integrated KPI + ML Risk Forecast Dashboard

Amaç:
- KPI (TRIR, LTIFR, Severity) trendleri
- UnifiedRiskPipeline forecast trendi
tek grafikte bir araya getirilir.
"""




def generate_integrated_dashboard(
    kpis: Dict[str, Dict],
    risk_predictions: Dict[str, float],
    filename="integrated_kpi_risk_dashboard.png",
) -> str:
    periods = sorted(kpis.keys())
    trir = [kpis[p]["TRIR"] for p in periods]
    ltifr = [kpis[p]["LTIFR"] for p in periods]
    sev = [kpis[p]["SeverityIndex"] for p in periods]

    # ML risk forecast
    risk_vals = [risk_predictions.get(p, np.nan) for p in periods]

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(periods, trir, marker="o", label="TRIR")
    ax.plot(periods, ltifr, marker="s", label="LTIFR")
    ax.plot(periods, sev, marker="^", label="Severity Index")

    # ML risk
    ax.plot(periods, risk_vals, marker="x", linestyle="--", label="ML Forecasted Risk")

    ax.set_title("OHS KPI + ML Forecasted Risk (Integrated Analysis)")
    ax.grid(True)
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    plt.savefig(filename)
    plt.close(fig)

    return filename
    return filename
