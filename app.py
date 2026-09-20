import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import zscore
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
import os

st.set_page_config(
    page_title="UIDAI Aadhaar Analysis Dashboard",
    layout="wide"
)

# --------------------------------------------------
# Robust CSV Loader
# --------------------------------------------------
def safe_read_csv(path):
    try:
        df = pd.read_csv(path, engine="python")
        if df.shape[1] == 1:
            raise ValueError
        return df
    except:
        for sep in ["|", ";"]:
            try:
                df = pd.read_csv(path, sep=sep, engine="python")
                if df.shape[1] > 1:
                    return df
            except:
                pass
        df = pd.read_csv(path, skiprows=2, engine="python")
        return df

def parse_dates(df):
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date"])
    return df

# --------------------------------------------------
# Load Data
# --------------------------------------------------
@st.cache_data
def load_all():
    enrol = safe_read_csv("combined enrolment.csv")
    demo = safe_read_csv("combined demographic.csv")
    bio = safe_read_csv("combined biometrics.csv")

    enrol = parse_dates(enrol)
    demo = parse_dates(demo)
    bio = parse_dates(bio)

    return enrol, demo, bio

enrol, demo, bio = load_all()

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
st.sidebar.title("Filters")

level = st.sidebar.selectbox("Aggregation Level", ["state", "district"])

regions = sorted(enrol[level].dropna().unique())
region = st.sidebar.selectbox("Select Region", ["ALL"] + regions)

# --------------------------------------------------
# Aggregate Monthly
# --------------------------------------------------
def aggregate(df, cols):
    if region != "ALL":
        df = df[df[level] == region]

    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    grouped = df.groupby("month")[cols].sum().reset_index()
    grouped["total"] = grouped[cols].sum(axis=1)
    return grouped

enrol_m = aggregate(enrol, ["age_0_5", "age_5_17", "age_18_greater"])
demo_m = aggregate(demo, ["demo_age_5_17", "demo_age_17_"])
bio_m = aggregate(bio, ["bio_age_5_17", "bio_age_17_"])

# --------------------------------------------------
# Combine
# --------------------------------------------------
df = enrol_m.merge(demo_m, on="month", how="outer", suffixes=("_enrol","_demo"))
df = df.merge(bio_m, on="month", how="outer", suffixes=("","_bio"))
df = df.fillna(0)

df["total_all"] = df["total_enrol"] + df["total_demo"] + df["total"]

# --------------------------------------------------
# Anomaly Detection
# --------------------------------------------------
df["pct_change"] = df["total_all"].pct_change().fillna(0)
df["zscore"] = zscore(df["pct_change"].replace([np.inf,-np.inf],0))
df["z_anomaly"] = abs(df["zscore"]) > 2.5

iso = IsolationForest(contamination=0.05, random_state=42)
df["iso_score"] = iso.fit_predict(df[["total_all"]])
df["iso_anomaly"] = df["iso_score"] == -1

df["anomaly"] = df["z_anomaly"] | df["iso_anomaly"]

# --------------------------------------------------
# Metrics
# --------------------------------------------------
oct_dec = df[df["month"].dt.month.isin([10,11,12])]
rest = df[~df["month"].dt.month.isin([10,11,12])]

SUII = oct_dec["total_all"].mean() / rest["total_all"].mean() if not rest.empty else np.nan
YUR = (oct_dec["demo_age_5_17"].sum() + oct_dec["bio_age_5_17"].sum()) / oct_dec["total_all"].sum()

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("📊 UIDAI Aadhaar Enrolment & Update Analysis")

col1, col2, col3 = st.columns(3)
col1.metric("Seasonal Update Intensity (Oct–Dec)", f"{SUII:.2f}")
col2.metric("Youth Update Ratio (Oct–Dec)", f"{YUR:.2%}")
col3.metric("Total Anomalies Detected", int(df["anomaly"].sum()))

# --------------------------------------------------
# Plot
# --------------------------------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["month"], y=df["total_enrol"],
    mode="lines+markers", name="Enrolments"
))

fig.add_trace(go.Scatter(
    x=df["month"], y=df["total_demo"],
    mode="lines+markers", name="Demographic Updates"
))

fig.add_trace(go.Scatter(
    x=df["month"], y=df["total"],
    mode="lines+markers", name="Biometric Updates"
))

anom = df[df["anomaly"]]
fig.add_trace(go.Scatter(
    x=anom["month"], y=anom["total_all"],
    mode="markers", name="Anomaly",
    marker=dict(color="red", size=10, symbol="x")
))

for y in df["month"].dt.year.unique():
    fig.add_vrect(
        x0=f"{y}-10-01", x1=f"{y}-12-31",
        fillcolor="LightSkyBlue", opacity=0.2, line_width=0
    )

fig.update_layout(
    title="Monthly Aadhaar Activity with Seasonality & Anomalies",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Data Table
# --------------------------------------------------
st.subheader("📄 Anomaly Details")
st.dataframe(
    df[df["anomaly"]][["month","total_all","zscore","iso_score"]],
    use_container_width=True
)
