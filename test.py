import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import zscore

# =========================
# CONFIG
# =========================
FILE = "combined demographic.csv"   # change to enrolment.csv / biometric.csv
DATE_COL = "date"
VALUE_COLS = ["demo_age_5_17", "demo_age_17_"]  # adjust for dataset
LEVEL = "state"  # state / district / pincode
TARGET = "ALL"   # e.g. "Uttar Pradesh" or "ALL"

Z_THRESHOLD = 2.5  # anomaly sensitivity

# =========================
# LOAD & CLEAN
# =========================
df = pd.read_csv(FILE)
df[DATE_COL] = pd.to_datetime(df[DATE_COL], dayfirst=True, errors="coerce")

if TARGET != "ALL":
    df = df[df[LEVEL] == TARGET]

# Aggregate monthly
df_grouped = df.groupby(pd.Grouper(key=DATE_COL, freq="M"))[VALUE_COLS].sum().reset_index()
df_grouped["total_updates"] = df_grouped[VALUE_COLS].sum(axis=1)

# =========================
# ANOMALY DETECTION
# =========================
df_grouped["zscore"] = zscore(df_grouped["total_updates"])
df_grouped["anomaly"] = np.abs(df_grouped["zscore"]) > Z_THRESHOLD

# =========================
# INTERACTIVE PLOT
# =========================
fig = go.Figure()

# Main line
fig.add_trace(go.Scatter(
    x=df_grouped[DATE_COL],
    y=df_grouped["total_updates"],
    mode="lines+markers",
    name="Total Updates",
    line=dict(width=3),
))

# Highlight anomalies
anomalies = df_grouped[df_grouped["anomaly"]]
fig.add_trace(go.Scatter(
    x=anomalies[DATE_COL],
    y=anomalies["total_updates"],
    mode="markers",
    name="Anomaly",
    marker=dict(color="red", size=10, symbol="x")
))

# =========================
# OCT–DEC SEASONAL HIGHLIGHT
# =========================
for year in df_grouped[DATE_COL].dt.year.unique():
    fig.add_vrect(
        x0=f"{year}-10-01",
        x1=f"{year}-12-31",
        fillcolor="LightSkyBlue",
        opacity=0.25,
        layer="below",
        line_width=0,
    )

# =========================
# LAYOUT
# =========================
fig.update_layout(
    title="Aadhaar Updates: Seasonality & Anomaly Detection",
    xaxis_title="Date",
    yaxis_title="Total Updates",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(y=0.99, x=0.01)
)

fig.show()

# =========================
# PRINT ANOMALY SUMMARY
# =========================
print("\nDetected Anomalies:")
print(anomalies[[DATE_COL, "total_updates", "zscore"]])
