"""
uidai_full_analysis.py
Comprehensive analysis pipeline for UIDAI enrolment + demographic + biometric CSVs.

Author: ChatGPT (adapted for your hackathon)
Date: 2026-01-19

Outputs (in output/ directory):
 - indices_summary.csv         : SUII, YUR, EPUSI per region
 - anomalies_summary.csv       : detected anomalies with reasons/scores
 - forecast_<region>_html      : interactive forecast + history
 - interactive_plots.html      : combined interactive visualizations
 - logs & intermediate CSVs
"""

import os
import warnings
from datetime import datetime
from typing import List, Optional, Dict

import numpy as np
import pandas as pd
from scipy.stats import zscore
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")
pd.options.display.float_format = "{:,.2f}".format

# -----------------------
# CONFIG: change these
# -----------------------
CONFIG = {
    "enrolment_file": "combined enrolment.csv",          # columns: date,state,district,pincode,age_0_5,age_5_17,age_18_greater
    "demographic_file": "combined demographic.csv",      # columns: date,state,district,pincode,demo_age_5_17,demo_age_17_plus (or similar)
    "biometric_file": "combined biometrics.csv",          # columns: date,state,district,pincode,bio_age_5_17,bio_age_17_plus
    "date_col": "date",
    "output_dir": "output",
    "aggregate_level": "district",              # one of: "state", "district", "pincode"
    "region_filter": None,                      # e.g. "Uttar Pradesh" or None for all
    "zscore_threshold": 2.5,
    "isolation_forest_contamination": 0.03,     # fraction of points expected anomalous
    "forecast_periods": 6,                      # months to forecast
    "octdec_months": [10, 11, 12],              # months considered Oct-Dec season
    "election_periods": [                        # optional list of (start_date, end_date, label)
        # ("2024-04-01","2024-06-01","General Election 2024"),
        # Add if you want election overlays
    ],
    "exam_months": [9, 10, 11, 12],  # months considered exam season (extend as needed)
}

# -----------------------
# Helpers
# -----------------------
def ensure_output_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

def try_parse_dates(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Robustly parse date column using dayfirst and mixed formats, coerce errors."""
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
    if df[date_col].isna().sum() > 0:
        print(f"⚠️  {df[date_col].isna().sum()} rows had unparsable dates. Showing up to 5 rows:")
        print(df[df[date_col].isna()].head())
    df = df.dropna(subset=[date_col])
    return df

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df

def safe_read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    # allow Excel too
    if path.lower().endswith(('.xls', '.xlsx')):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, dtype=str, low_memory=False)
    df = normalize_columns(df)
    return df

# -----------------------
# Load datasets
# -----------------------
def load_and_prep_all(cfg: dict) -> Dict[str, pd.DataFrame]:
    print("Loading datasets...")
    enrol = safe_read_csv(cfg["enrolment_file"])
    demo = safe_read_csv(cfg["demographic_file"])
    bio = safe_read_csv(cfg["biometric_file"])

    # parse dates robustly
    enrol = try_parse_dates(enrol, cfg["date_col"])
    demo = try_parse_dates(demo, cfg["date_col"])
    bio = try_parse_dates(bio, cfg["date_col"])

    # lower-case column names for convenience
    enrol.columns = [c.lower() for c in enrol.columns]
    demo.columns = [c.lower() for c in demo.columns]
    bio.columns = [c.lower() for c in bio.columns]

    return {"enrol": enrol, "demo": demo, "bio": bio}

# -----------------------
# Harmonize columns & derive totals
# -----------------------
def harmonize_and_aggregate(dfs: Dict[str,pd.DataFrame], cfg: dict):
    """
    Make consistent column names for age groups, aggregate monthly at desired level.
    Returns monthly timeseries dataframes (index=date) for each region & dataset.
    """
    level = cfg["aggregate_level"].lower()
    date_col = cfg["date_col"].lower()

    def prepare(df: pd.DataFrame, mapping: dict, dataset_name: str) -> pd.DataFrame:
        # Rename columns that match mapping keys
        df = df.copy()
        # Map keys present
        present_map = {k:v for k,v in mapping.items() if k in df.columns}
        if not present_map:
            print(f"Warning: Could not find any expected columns for {dataset_name}. Columns: {df.columns.tolist()[:10]}")
        df = df.rename(columns=present_map)

        # Fill missing age columns with zeros
        for col in mapping.values():
            if col not in df.columns:
                df[col] = 0

        # Ensure level exists
        if level not in df.columns:
            # try alternative names
            alt = [c for c in df.columns if level in c]
            if alt:
                df = df.rename(columns={alt[0]: level})
            else:
                raise KeyError(f"Expected aggregation level '{level}' not found in {dataset_name} columns.")

        # cast numeric
        for c in mapping.values():
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        # aggregate monthly by level
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df['month'] = df[date_col].dt.to_period('M').dt.to_timestamp()
        agg_cols = [level, 'month'] + list(mapping.values())
        grouped = df[agg_cols].groupby([level,'month']).sum().reset_index()
        # compute totals
        grouped['total_updates'] = grouped[list(mapping.values())].sum(axis=1)
        return grouped

    # mapping for each dataset — keys are possible column names present in source,
    # values are standardized column names we will use
    enrol_map = {
        'age_0_5': 'age_0_5',
        'age_5_17': 'age_5_17',
        'age_18_greater': 'age_18_greater'
    }
    demo_map = {
        'demo_age_5_17': 'demo_age_5_17',
        'demo_age_17_plus': 'demo_age_17_',
        # try common alternates
        'demo_age_18_plus': 'demo_age_17_plus'
    }
    bio_map = {
        'bio_age_5_17': 'bio_age_5_17',
        'bio_age_17_plus': 'bio_age_17_',
        'bio_age_18_plus': 'bio_age_17_plus'
    }

    enrol_monthly = prepare(dfs['enrol'], enrol_map, 'enrolment')
    demo_monthly = prepare(dfs['demo'], demo_map, 'demographic')
    bio_monthly = prepare(dfs['bio'], bio_map, 'biometric')

    return enrol_monthly, demo_monthly, bio_monthly

# -----------------------
# Merge datasets into a unified panel
# -----------------------
def build_panel(enrol_m, demo_m, bio_m, cfg):
    level = cfg['aggregate_level']
    # full outer merge on level + month
    panel = enrol_m.merge(demo_m, on=[level,'month'], how='outer', suffixes=('','_demo'))
    panel = panel.merge(bio_m, on=[level,'month'], how='outer', suffixes=('','_bio'))
    panel = panel.fillna(0)
    # ensure month is datetime
    panel['month'] = pd.to_datetime(panel['month'])
    # compute derived totals
    # normalize column names present
    panel['total_enrolments'] = panel.get('total_updates', 0)  # from enrol mapping name
    panel['total_demo_updates'] = panel.get('total_updates_demo', 0)
    panel['total_bio_updates'] = panel.get('total_updates_bio', 0)
    return panel

# -----------------------
# Indices: SUII, YUR, EPUSI
# -----------------------
def compute_indices(panel: pd.DataFrame, cfg: dict):
    level = cfg['aggregate_level']
    oct_months = cfg['octdec_months']
    exam_months = cfg.get('exam_months', cfg['octdec_months'])
    # create month number column
    panel['month_num'] = panel['month'].dt.month

    summary_rows = []
    regions = panel[level].unique()
    for reg in regions:
        df_reg = panel[panel[level] == reg].sort_values('month')
        if df_reg.empty:
            continue
        # SUII: Oct-Dec average / other months average for demo updates (and biometrics)
        oct_mask = df_reg['month_num'].isin(oct_months)
        other_mask = ~oct_mask
        # avoid division by zero
        demo_oct_avg = df_reg.loc[oct_mask,'total_demo_updates'].mean() if oct_mask.any() else np.nan
        demo_other_avg = df_reg.loc[other_mask,'total_demo_updates'].mean() if other_mask.any() else np.nan
        bio_oct_avg = df_reg.loc[oct_mask,'total_bio_updates'].mean() if oct_mask.any() else np.nan
        bio_other_avg = df_reg.loc[other_mask,'total_bio_updates'].mean() if other_mask.any() else np.nan

        SUII_demo = demo_oct_avg / demo_other_avg if (demo_other_avg and not np.isnan(demo_other_avg)) else np.nan
        SUII_bio = bio_oct_avg / bio_other_avg if (bio_other_avg and not np.isnan(bio_other_avg)) else np.nan

        # YUR: share of youth updates in Oct-Dec
        youth_oct = df_reg.loc[oct_mask, ['demo_age_5_17','bio_age_5_17']].sum().sum() if oct_mask.any() else 0
        total_oct = df_reg.loc[oct_mask, ['total_demo_updates','total_bio_updates']].sum().sum() if oct_mask.any() else 0
        YUR = youth_oct / total_oct if total_oct > 0 else np.nan

        # EPUSI: requires election periods list
        epusi_vals = []
        for (start, end, label) in cfg.get('election_periods', []):
            s = pd.to_datetime(start)
            e = pd.to_datetime(end)
            in_period = df_reg[(df_reg['month'] >= s) & (df_reg['month'] <= e)]
            non_period = df_reg[(df_reg['month'] < s) | (df_reg['month'] > e)]
            per_avg = in_period['total_demo_updates'].mean() if not in_period.empty else np.nan
            non_avg = non_period['total_demo_updates'].mean() if not non_period.empty else np.nan
            val = per_avg / non_avg if (non_avg and not np.isnan(non_avg)) else np.nan
            epusi_vals.append((label, val))
        summary_rows.append({
            level: reg,
            'SUII_demo': SUII_demo,
            'SUII_bio': SUII_bio,
            'YUR_octdec': YUR,
            'EPUSI_list': epusi_vals
        })
    summary_df = pd.DataFrame(summary_rows)
    return summary_df

# -----------------------
# Anomaly detection
# -----------------------
def detect_anomalies(panel: pd.DataFrame, cfg: dict):
    """
    Multi-method anomaly detection:
      - z-score on month-to-month % change
      - IsolationForest on rolling features
      - residual outliers from seasonal_decompose / smoothing
    Returns anomalies dataframe with scores.
    """
    level = cfg['aggregate_level']
    z_th = cfg['zscore_threshold']
    iso_contam = cfg['isolation_forest_contamination']
    anomalies = []

    regions = panel[level].unique()
    for reg in regions:
        df_reg = panel[panel[level] == reg].sort_values('month').copy()
        if df_reg.shape[0] < 6:
            continue
        # use total updates (sum of all types) as a simple signal
        df_reg['total_all'] = df_reg['total_enrolments'] + df_reg['total_demo_updates'] + df_reg['total_bio_updates']
        df_reg['pct_change'] = df_reg['total_all'].pct_change().fillna(0)
        # z-score on pct_change
        df_reg['z_pct'] = zscore(df_reg['pct_change'].replace([np.inf, -np.inf], 0).fillna(0))
        df_reg['z_anom'] = np.abs(df_reg['z_pct']) > z_th

        # IsolationForest on recent rolling features
        df_reg['roll_3'] = df_reg['total_all'].rolling(3, min_periods=1).mean()
        df_reg['roll_6'] = df_reg['total_all'].rolling(6, min_periods=1).mean()
        features = df_reg[['total_all','roll_3','roll_6']].fillna(0).values
        if len(df_reg) >= 10:
            iso = IsolationForest(contamination=iso_contam, random_state=42)
            iso_preds = iso.fit_predict(features)
            df_reg['iso_score'] = -iso.decision_function(features)  # higher => more anomalous
            df_reg['iso_anom'] = iso_preds == -1
        else:
            df_reg['iso_score'] = 0
            df_reg['iso_anom'] = False

        # Simple residual-based anomaly: actual vs HW smoother
        try:
            hw = ExponentialSmoothing(df_reg['total_all'], trend='add', seasonal=None, initialization_method='estimated')
            hwf = hw.fit(optimized=True)
            fitted = hwf.fittedvalues
            resid = df_reg['total_all'] - fitted
            resid_z = (resid - resid.mean()) / (resid.std() if resid.std() else 1)
            df_reg['resid_z'] = resid_z
            df_reg['resid_anom'] = np.abs(resid_z) > 2.8
        except Exception as e:
            df_reg['resid_z'] = 0
            df_reg['resid_anom'] = False

        # combine anomalies
        df_reg['anomaly_combined'] = df_reg[['z_anom','iso_anom','resid_anom']].any(axis=1)
        for _, r in df_reg.iterrows():
            if r['anomaly_combined']:
                anomalies.append({
                    level: reg,
                    'month': r['month'],
                    'total_all': r['total_all'],
                    'z_pct': float(r['z_pct']),
                    'iso_score': float(r.get('iso_score',0)),
                    'resid_z': float(r.get('resid_z',0)),
                    'z_anom': bool(r['z_anom']),
                    'iso_anom': bool(r['iso_anom']),
                    'resid_anom': bool(r['resid_anom'])
                })
    anomalies_df = pd.DataFrame(anomalies)
    return anomalies_df

# -----------------------
# Forecasting per region (Holt-Winters / ETS)
# -----------------------
def forecast_region(series: pd.Series, periods: int = 6):
    """Return forecast (index = months) using ETS/Holt-Winters."""
    if len(series.dropna()) < 6:
        return None
    try:
        model = ExponentialSmoothing(series, trend='add', seasonal=None, initialization_method='estimated')
        fit = model.fit(optimized=True)
        forecast = fit.forecast(periods)
        return forecast
    except Exception as e:
        # fallback simple last-value repeating
        return pd.Series([series.iloc[-1]]*periods, index=pd.date_range(start=series.index[-1] + pd.offsets.MonthBegin(), periods=periods, freq='MS'))

# -----------------------
# Plotting utilities (Plotly interactives)
# -----------------------
def plot_time_series_with_anomalies(panel: pd.DataFrame, anomalies_df: pd.DataFrame, cfg: dict, save_html: str):
    level = cfg['aggregate_level']
    regions = panel[level].unique()
    fig = go.Figure()
    # create small multiples? For simplicity produce one interactive page per region stacked
    pages = []
    for reg in regions:
        df_reg = panel[panel[level] == reg].sort_values('month')
        if df_reg.empty: continue
        df_reg = df_reg.set_index('month').resample('MS').sum().reset_index()
        # main line
        fig_reg = go.Figure()
        fig_reg.add_trace(go.Scatter(x=df_reg['month'], y=df_reg['total_enrolments'], mode='lines+markers', name='Enrolments'))
        fig_reg.add_trace(go.Scatter(x=df_reg['month'], y=df_reg['total_demo_updates'], mode='lines+markers', name='Demo updates'))
        fig_reg.add_trace(go.Scatter(x=df_reg['month'], y=df_reg['total_bio_updates'], mode='lines+markers', name='Bio updates'))
        # anomalies overlay
        ann = anomalies_df[anomalies_df[level] == reg]
        if not ann.empty:
            fig_reg.add_trace(go.Scatter(x=ann['month'], y=ann['total_all'], mode='markers', name='Anomaly', marker=dict(color='red', size=10, symbol='x')))
        # shade Oct-Dec
        for y in sorted(df_reg['month'].dt.year.unique()):
            fig_reg.add_vrect(x0=f"{y}-10-01", x1=f"{y}-12-31", fillcolor="LightSkyBlue", opacity=0.12, line_width=0)
        fig_reg.update_layout(title=f"{level.title()}: {reg}", xaxis_title="Month", yaxis_title="Counts", template="plotly_white")
        pages.append(fig_reg.to_html(full_html=False, include_plotlyjs='cdn'))
    # combine into single HTML
    html_page = "<html><head><meta charset='utf-8'><title>UIDAI Analysis</title></head><body>"
    html_page += "<h1>UIDAI Time Series & Anomalies</h1>"
    for p in pages:
        html_page += p
        html_page += "<hr/>"
    html_page += "</body></html>"
    with open(save_html, 'w', encoding='utf-8') as f:
        f.write(html_page)
    print(f"Interactive plots written to {save_html}")

# -----------------------
# Main workflow
# -----------------------
def main(cfg):
    outdir = ensure_output_dir(cfg['output_dir'])
    dfs = load_and_prep_all(cfg)
    enrol_m, demo_m, bio_m = harmonize_and_aggregate(dfs, cfg)
    panel = build_panel(enrol_m, demo_m, bio_m, cfg)
    # optional region filter
    if cfg['region_filter']:
        panel = panel[panel[cfg['aggregate_level']] == cfg['region_filter']]

    print("\nPanel snapshot:")
    print(panel.head())

    # compute indices
    indices_df = compute_indices(panel, cfg)
    indices_df.to_csv(os.path.join(outdir, "indices_summary.csv"), index=False)
    print(f"Wrote indices_summary.csv ({len(indices_df)} regions)")

    # anomaly detection
    anomalies_df = detect_anomalies(panel, cfg)
    anomalies_df.to_csv(os.path.join(outdir, "anomalies_summary.csv"), index=False)
    print(f"Wrote anomalies_summary.csv ({len(anomalies_df)} anomalies)")

    # interactive plots with anomalies
    html_path = os.path.join(outdir, "interactive_plots.html")
    plot_time_series_with_anomalies(panel, anomalies_df, cfg, html_path)

    # forecasts: top N regions by avg activity
    region_col = cfg['aggregate_level']
    region_avgs = panel.groupby(region_col)['total_enrolments','total_demo_updates','total_bio_updates'].sum().sum(axis=1) if False else None
    # Instead, compute by summing totals
    totals_by_region = panel.groupby(region_col).apply(lambda d: (d['total_enrolments'] + d['total_demo_updates'] + d['total_bio_updates']).mean()).sort_values(ascending=False)
    top_regions = totals_by_region.head(6).index.tolist()
    for reg in top_regions:
        series = panel[panel[region_col] == reg].sort_values('month')
        series = series.set_index('month')
        series_ts = series['total_enrolments'] + series['total_demo_updates'] + series['total_bio_updates']
        series_ts = series_ts.resample('MS').sum()
        forecast = forecast_region(series_ts, periods=cfg['forecast_periods'])
        if forecast is None:
            continue
        # create plot: history + forecast
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series_ts.index, y=series_ts.values, mode='lines+markers', name='History'))
        fig.add_trace(go.Scatter(x=forecast.index, y=forecast.values, mode='lines+markers', name='Forecast'))
        # annotate anomalies
        reg_anom = anomalies_df[anomalies_df[region_col] == reg]
        if not reg_anom.empty:
            fig.add_trace(go.Scatter(x=reg_anom['month'], y=reg_anom['total_all'], mode='markers', name='Anomalies', marker=dict(color='red', size=10, symbol='x')))
        fig.update_layout(title=f"{reg} - History & {cfg['forecast_periods']}-month forecast", xaxis_title='Month', yaxis_title='Counts', template='plotly_white')
        fname = os.path.join(outdir, f"forecast_{reg.replace('/','_')}.html")
        fig.write_html(fname)
        print(f"Wrote forecast for {reg} -> {fname}")

    print("\nDone. Summary files in:", outdir)
    print(" - indices_summary.csv  (SUII, YUR, EPUSI info)")
    print(" - anomalies_summary.csv")
    print(" - interactive_plots.html")
    print(" - forecast_<region>.html (for top regions)")

if __name__ == "__main__":
    main(CONFIG)
