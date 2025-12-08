"""
AI4OHS-HYBRID
Advanced Dashboard: TRIR/LTIFR/Severity + ESS/6331 Heatmap Tek Grafik

Girdi:
- kpis: compute_kpis çıktısı
- ess_items: ESS/6331 checklist maddeleri

Çıktı:
- Tek PNG: üstte TRIR/LTIFR/Severity trend, altta ESS–6331 heatmap
"""

import os
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

from governance.compliance_heatmap import HEATMAP_COLORS, generate_heatmap_matrix


def plot_advanced_dashboard(
    kpis: Dict[str, Dict], ess_items: List[Dict], filename: str = "advanced_ohs_dashboard.png"
) -> str:
    periods = sorted(kpis.keys())
    trir = [kpis[p]["TRIR"] for p in periods]
    ltifr = [kpis[p]["LTIFR"] for p in periods]
    sev = [kpis[p]["SeverityIndex"] for p in periods]

    # ESS–6331 matrix
    matrix = generate_heatmap_matrix(ess_items)
    ess_list = sorted(matrix.keys())
    laws = sorted({law for vals in matrix.values() for law in vals.keys()})

    # Heatmap veri matrisini oluştur
    status_to_val = {"E": 1.0, "K": 0.5, "H": 0.0, "": np.nan}
    data = np.zeros((len(laws), len(ess_list)))
    data[:] = np.nan

    for i, law in enumerate(laws):
        for j, ess in enumerate(ess_list):
            status = matrix.get(ess, {}).get(law, "")
            data[i, j] = status_to_val.get(status, np.nan)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [1, 1.2]})

    # Üst: KPI trendleri
    ax1.plot(periods, trir, marker="o", label="TRIR")
    ax1.plot(periods, ltifr, marker="s", label="LTIFR")
    ax1.plot(periods, sev, marker="^", label="Severity Index")
    ax1.set_title("OHS KPI Trends (TRIR / LTIFR / Severity Index)")
    ax1.set_xticklabels(periods, rotation=45)
    ax1.grid(True)
    ax1.legend()

    # Alt: ESS–6331 heatmap
    im = ax2.imshow(data, aspect="auto", interpolation="nearest")

    ax2.set_yticks(range(len(laws)))
    ax2.set_yticklabels(laws)
    ax2.set_xticks(range(len(ess_list)))
    ax2.set_xticklabels(ess_list, rotation=45)
    ax2.set_title("ESS–6331 Compliance Heatmap")

    # Colorbar (0=H, 0.5=K, 1=E)
    cbar = fig.colorbar(im, ax=ax2)
    cbar.set_label("Compliance Level (0=H, 0.5=K, 1=E)")

    fig.tight_layout()
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    plt.savefig(filename)
    plt.close(fig)

    return filename
