# app.py
# Streamlit dashboard: UIDAI pincode choropleth + analysis
# Requirements:
# pip install streamlit pandas numpy plotly scipy scikit-learn pycountry

import streamlit as st
import pandas as pd
import numpy as np
import json
from scipy.stats import zscore
from sklearn.ensemble import IsolationForest
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="UIDAI — Pincode Map & Analysis", layout="wide")

# -----------------------
# CONFIG (change filenames if needed)
# -----------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENROL_FILE = os.path.join(SCRIPT_DIR, "combined enrolment.csv")
DEMO_FILE = os.path.join(SCRIPT_DIR, "combined demographic.csv")
BIO_FILE = os.path.join(SCRIPT_DIR, "combined biometrics.csv")
PIN_GEOJSON = os.path.join(SCRIPT_DIR, "All_India_pincode.geojson")
PIN_POP = os.path.join(SCRIPT_DIR, "consolidated_pincode_census.csv")
DATE_COL = "date"
OCTDEC = [10,11,12]
Z_THRESH = 2.5
ISO_CONTAM = 0.03

# -----------------------
# Utilities
# -----------------------
def safe_read_csv(path):
    if not os.path.exists(path):
        st.error(f"File not found: {path}")
        return None
    try:
        df = pd.read_csv(path, engine="python")
        # sometimes data has single-column due to delimiter mismatch: try alternatives
        if df.shape[1] == 1:
            for sep in ['|',';','\t']:
                try:
                    df = pd.read_csv(path, sep=sep, engine='python')
                    if df.shape[1] > 1:
                        break
                except:
                    pass
        return df
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return None

def parse_dates(df):
    df = df.copy()
    if DATE_COL in df.columns:
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], dayfirst=True, errors="coerce")
        df = df.dropna(subset=[DATE_COL])
    else:
        st.warning(f"No '{DATE_COL}' column found.")
    return df

def standardize_cols(df):
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def ensure_pincode_str(x):
    s = str(int(float(x))) if (pd.notna(x) and str(x).replace('.0','').isdigit()) else str(x).strip()
    return s.zfill(6) if len(s) <= 6 else s

# -----------------------
# Load files (cached)
# -----------------------
@st.cache_data(show_spinner=False)
def load_data():
    enrol = safe_read_csv(ENROL_FILE)
    demo = safe_read_csv(DEMO_FILE)
    bio = safe_read_csv(BIO_FILE)
    geo = None
    pop = None
    if os.path.exists(PIN_GEOJSON):
        with open(PIN_GEOJSON, 'r', encoding='utf-8') as f:
            geo = json.load(f)
    if os.path.exists(PIN_POP):
        pop = pd.read_csv(PIN_POP, dtype=str, low_memory=False)
    return enrol, demo, bio, geo, pop

enrol, demo, bio, geojson, pop_df = load_data()

st.title("UIDAI — Pincode Map & Societal Analysis")
st.markdown("Interactive pincode-level maps & metrics: seasonal intensity, youth share, updates per population, biometric risk, anomalies.")

# -----------------------
# Basic checks & UI instructions
# -----------------------
if enrol is None or demo is None or bio is None:
    st.warning("Missing one or more UIDAI CSV files (enrolment/demographic/biometric). Place them next to this app and restart.")
    st.stop()

# Standardize
enrol = standardize_cols(enrol)
demo = standardize_cols(demo)
bio = standardize_cols(bio)

enrol = parse_dates(enrol)
demo = parse_dates(demo)
bio = parse_dates(bio)

st.sidebar.header("Map & Data Options")
agg_level = st.sidebar.selectbox("Aggregate by", ["pincode","district","state"], index=0)

# -----------------------
# Aggregate monthly at pincode level (preferred)
# -----------------------
def aggregate_monthly(df, group_col, age_cols):
    df = df.copy()
    if DATE_COL not in df.columns:
        st.error(f"{DATE_COL} missing from input CSV.")
        return pd.DataFrame()
    df['month'] = df[DATE_COL].dt.to_period('M').dt.to_timestamp()
    # ensure group col exists
    if group_col not in df.columns:
        st.error(f"Grouping column '{group_col}' not found in dataset.")
        return pd.DataFrame()
    # sanitize pincodes
    if group_col == 'pincode':
        df['pincode'] = df['pincode'].apply(lambda x: ensure_pincode_str(x))
    out = df.groupby([group_col,'month'])[age_cols].sum().reset_index()
    out['total'] = out[age_cols].sum(axis=1)
    return out

# Identify plausible age columns in each dataset
enrol_age_cols = [c for c in enrol.columns if c.startswith('age_') or ('age' in c and 'greater' in c)]
demo_age_cols = [c for c in demo.columns if c.startswith('demo_age') or ('age' in c and 'demo' in c)]
bio_age_cols  = [c for c in bio.columns if c.startswith('bio_age') or ('age' in c and 'bio' in c)]

# safest defaults if heuristics fail
if not enrol_age_cols:
    enrol_age_cols = [c for c in enrol.columns if c not in ['date','state','district','pincode']]
if not demo_age_cols:
    demo_age_cols = [c for c in demo.columns if c not in ['date','state','district','pincode']]
if not bio_age_cols:
    bio_age_cols = [c for c in bio.columns if c not in ['date','state','district','pincode']]

st.sidebar.markdown(f"**Detected age columns:**\n\nenrol: {enrol_age_cols}\n\ndemo: {demo_age_cols}\n\nbio: {bio_age_cols}")

group_col = agg_level

with st.spinner("Aggregating data by month..."):
    enrol_m = aggregate_monthly(enrol, group_col, enrol_age_cols)
    demo_m = aggregate_monthly(demo, group_col, demo_age_cols)
    bio_m  = aggregate_monthly(bio, group_col, bio_age_cols)

    # Merge by group + month
    panel = enrol_m.merge(demo_m, on=[group_col,'month'], how='outer', suffixes=('_enrol','_demo'))
    panel = panel.merge(bio_m, on=[group_col,'month'], how='outer', suffixes=('','_bio'))
    panel = panel.fillna(0)
    # unify total columns
    panel['total_enrol'] = panel[[c for c in panel.columns if c.endswith('_enrol') and 'total' in c]].sum(axis=1) if any('total' in c and c.endswith('_enrol') for c in panel.columns) else panel.get('total',0)
    panel['total_demo']  = panel.get('total_demo', 0)
    panel['total_bio']   = panel.get('total_bio', 0)
    panel['total_all']   = panel['total_enrol'] + panel['total_demo'] + panel['total_bio']

st.success(f"✓ Data loaded: {len(panel)} records, {panel['month'].dt.to_period('M').nunique()} months, {panel[group_col].nunique()} {group_col}s")

# -----------------------
# Join population (if pincode-level pop provided)
# -----------------------
if pop_df is not None:
    pop_df = standardize_cols(pop_df)
    # try common names 'pincode','pin','postal'
    cand = None
    for col in pop_df.columns:
        if 'pinc' in col:
            cand = col
            break
    if cand is None:
        st.warning("Could not find pincode column in population file. Provide a column named 'pincode'.")
    else:
        pop_df['pincode'] = pop_df[cand].apply(lambda x: ensure_pincode_str(x))
        # find population column
        pop_col = None
        for c in pop_df.columns:
            if 'pop' in c or 'population' in c or 'tot' in c:
                pop_col = c
                break
        if pop_col is None:
            st.warning("Population column not detected in pincode_pop.csv. Make sure file has 'population' column.")
        else:
            pop_df['population'] = pd.to_numeric(pop_df[pop_col], errors='coerce').fillna(0)
            if group_col == 'pincode':
                # merge panel aggregated at pincode with pop
                panel = panel.merge(pop_df[['pincode','population']], left_on='pincode', right_on='pincode', how='left')
            else:
                # if aggregated by district/state, try aggregate population
                panel = panel.merge(pop_df[['pincode','population']], left_on='pincode' if 'pincode' in panel.columns else group_col, right_on='pincode', how='left')
else:
    st.info("No pincode population CSV found. Coverage % and per-capita metrics will not be available until you provide consolidated_pincode_census.csv.")

    # If population column exists, compute per-10k metrics
    if 'population' in panel.columns and panel['population'].sum() > 0:
        panel['updates_per_10k'] = (panel['total_all'] / panel['population']) * 10000
        panel['enrol_per_10k'] = (panel['total_enrol'] / panel['population']) * 10000
        panel['bio_per_10k'] = (panel['total_bio'] / panel['population']) * 10000
        panel['coverage_percent'] = (panel['total_enrol'] / panel['population']) * 100
    else:
        panel['updates_per_10k'] = np.nan
        panel['enrol_per_10k'] = np.nan
        panel['bio_per_10k'] = np.nan
        panel['coverage_percent'] = np.nan

    # -----------------------
    # Compute indices (SUII, YUR, Biometric Risk)
    # -----------------------
    panel['month_num'] = panel['month'].dt.month
    oct_mask = panel['month_num'].isin(OCTDEC)

    # compute SUII and YUR per region summary
    summary = panel.groupby(group_col).apply(lambda df:
        pd.Series({
            'SUII_demo': (df.loc[df['month_num'].isin(OCTDEC),'total_demo'].mean() / (df.loc[~df['month_num'].isin(OCTDEC),'total_demo'].mean() if df.loc[~df['month_num'].isin(OCTDEC),'total_demo'].mean() else np.nan)),
            'SUII_bio':  (df.loc[df['month_num'].isin(OCTDEC),'total_bio'].mean()  / (df.loc[~df['month_num'].isin(OCTDEC),'total_bio'].mean()  if df.loc[~df['month_num'].isin(OCTDEC),'total_bio'].mean() else np.nan)),
            'YUR_octdec': (df.loc[df['month_num'].isin(OCTDEC), [c for c in df.columns if '5_17' in c]].sum().sum() / df.loc[df['month_num'].isin(OCTDEC),'total_all'].sum() ) if df.loc[df['month_num'].isin(OCTDEC),'total_all'].sum() else np.nan,
            'avg_updates_per_10k': df['updates_per_10k'].mean()
        })
    ).reset_index().rename(columns={0:group_col})

    # Biometric Risk Score (heuristic): bigger child population + low bio updates per 10k -> higher risk
    def compute_risk(group_df):
        child_cols = [c for c in group_df.columns if '5_17' in c]
        child_pop = group_df[child_cols].sum().sum() if child_cols else np.nan
        avg_bio_per_10k = group_df['bio_per_10k'].mean() if 'bio_per_10k' in group_df.columns else np.nan
        if np.isnan(child_pop) or np.isnan(avg_bio_per_10k):
            return np.nan
        return (child_pop / (avg_bio_per_10k + 1))

    risk_scores = panel.groupby(group_col).apply(lambda g: compute_risk(g)).reset_index(name='biometric_risk_score')
    summary = summary.merge(risk_scores, on=group_col, how='left')

    # -----------------------
    # Anomaly detection (zscore on pct change + IsolationForest)
    # -----------------------
    with st.spinner("Detecting anomalies..."):
        panel_sorted = panel.sort_values([group_col,'month']).copy()
        panel_sorted['pct_change'] = panel_sorted.groupby(group_col)['total_all'].pct_change().fillna(0)
        panel_sorted['z_pct'] = panel_sorted.groupby(group_col)['pct_change'].transform(lambda x: zscore(x.replace([np.inf,-np.inf],0).fillna(0)))
        panel_sorted['z_anom'] = panel_sorted['z_pct'].abs() > Z_THRESH

        def add_iso_flags(df):
            out = df.copy()
            if len(out) >= 8:
                iso = IsolationForest(contamination=ISO_CONTAM, random_state=42)
                vals = out[['total_all']].fillna(0).values
                preds = iso.fit_predict(vals)
                out['iso_anom'] = preds == -1
            else:
                out['iso_anom'] = False
            return out

        panel_iso = panel_sorted.groupby(group_col).apply(add_iso_flags).reset_index(drop=True)
        panel_iso['anomaly'] = panel_iso['z_anom'] | panel_iso['iso_anom']

# If population column exists, compute per-10k metrics
if 'population' in panel.columns and panel['population'].sum() > 0:
    panel['updates_per_10k'] = (panel['total_all'] / panel['population']) * 10000
    panel['enrol_per_10k'] = (panel['total_enrol'] / panel['population']) * 10000
    panel['bio_per_10k'] = (panel['total_bio'] / panel['population']) * 10000
    panel['coverage_percent'] = (panel['total_enrol'] / panel['population']) * 100
else:
    panel['updates_per_10k'] = np.nan
    panel['enrol_per_10k'] = np.nan
    panel['bio_per_10k'] = np.nan
    panel['coverage_percent'] = np.nan

# -----------------------
# Compute indices (SUII, YUR, Biometric Risk)
# -----------------------
panel['month_num'] = panel['month'].dt.month
oct_mask = panel['month_num'].isin(OCTDEC)

# compute SUII and YUR per region summary
summary = (
    panel
    .groupby(group_col, group_keys=False)
    .apply(
        lambda df: pd.Series({
            'SUII_demo': (
                df.loc[df['month_num'].isin(OCTDEC), 'total_demo'].mean() /
                df.loc[~df['month_num'].isin(OCTDEC), 'total_demo'].mean()
                if df.loc[~df['month_num'].isin(OCTDEC), 'total_demo'].mean() not in [0, np.nan] else np.nan
            ),
            'SUII_bio': (
                df.loc[df['month_num'].isin(OCTDEC), 'total_bio'].mean() /
                df.loc[~df['month_num'].isin(OCTDEC), 'total_bio'].mean()
                if df.loc[~df['month_num'].isin(OCTDEC), 'total_bio'].mean() not in [0, np.nan] else np.nan
            ),
            'YUR_octdec': (
                df.loc[df['month_num'].isin(OCTDEC), [c for c in df.columns if '5_17' in c]]
                .sum().sum()
                / df.loc[df['month_num'].isin(OCTDEC), 'total_all'].sum()
                if df.loc[df['month_num'].isin(OCTDEC), 'total_all'].sum() > 0 else np.nan
            ),
            'avg_updates_per_10k': df['updates_per_10k'].mean()
        }),
        include_groups=False
    )
    .reset_index()
)


# Biometric Risk Score (heuristic): bigger child population + low bio updates per 10k -> higher risk
# If no child population column available, we approximate using 'age_5_17' fields if present
def compute_risk(group_df):
    child_cols = [c for c in group_df.columns if '5_17' in c]
    child_pop = group_df[child_cols].sum().sum() if child_cols else np.nan
    avg_bio_per_10k = group_df['bio_per_10k'].mean() if 'bio_per_10k' in group_df.columns else np.nan
    # risk higher when child_pop large and bio_per_10k small
    if np.isnan(child_pop) or np.isnan(avg_bio_per_10k):
        return np.nan
    return (child_pop / (avg_bio_per_10k + 1))  # simple heuristic

risk_scores = (
    panel
    .groupby(group_col, group_keys=False)
    .apply(lambda g: compute_risk(g), include_groups=False)
    .reset_index(name='biometric_risk_score')
)
summary = summary.merge(risk_scores, on=group_col, how='left')

# -----------------------
# Anomaly detection (zscore on pct change + IsolationForest)
# -----------------------
panel_sorted = panel.sort_values([group_col,'month']).copy()
panel_sorted['pct_change'] = panel_sorted.groupby(group_col)['total_all'].pct_change().fillna(0)
panel_sorted['z_pct'] = panel_sorted.groupby(group_col)['pct_change'].transform(lambda x: zscore(x.replace([np.inf,-np.inf],0).fillna(0)))
panel_sorted['z_anom'] = panel_sorted['z_pct'].abs() > Z_THRESH

# IsolationForest per region (if enough points)
def add_iso_flags(df):
    out = df.copy()
    if len(out) >= 8:
        iso = IsolationForest(contamination=ISO_CONTAM, random_state=42)
        vals = out[['total_all']].fillna(0).values
        preds = iso.fit_predict(vals)
        out['iso_anom'] = preds == -1
    else:
        out['iso_anom'] = False
    return out

panel_iso = panel_sorted.groupby(group_col).apply(add_iso_flags).reset_index(drop=True)
panel_iso['anomaly'] = panel_iso['z_anom'] | panel_iso['iso_anom']

# -----------------------
# Map: choropleth for a selected month
# -----------------------
st.header("Map: Pincode-level choropleth")

if len(panel) == 0 or len(panel_iso) == 0:
    st.error("No data to display. Check that your CSV files have valid date columns and age columns.")
elif geojson is None:
    st.warning("⚠️ GeoJSON file (All_India_pincode.geojson) not found. Map visualization disabled. Download from data.gov.in and place in this folder.")
else:
    month_sel = st.sidebar.select_slider("Select month", options=sorted(panel['month'].dt.strftime('%Y-%m').unique()), value=sorted(panel['month'].dt.strftime('%Y-%m').unique())[-1])
    month_dt = pd.to_datetime(month_sel + "-01")
    view_metric = st.sidebar.selectbox("Map metric", ['updates_per_10k','total_all','SUII_demo','avg_updates_per_10k','biometric_risk_score'])

    # Prepare map dataframe for selected month
    map_df = summary.copy()
    # For pincode-level mapping, we need one row per polygon feature:
    if group_col == 'pincode':
        sel = panel_iso[panel_iso['month'] == month_dt].copy()
        # aggregate last month per pincode
        map_df = sel.groupby('pincode').agg({
            'total_all':'sum',
            'updates_per_10k':'mean',
            'total_demo':'sum',
            'total_bio':'sum',
            'z_pct':'mean',
            'anomaly':'max'
        }).reset_index()
        # merge with population if present
        if 'population' in panel_iso.columns:
            map_df = map_df.merge(panel_iso[['pincode','population']].drop_duplicates(), on='pincode', how='left')
        # also merge computed SUII or risk from 'summary' if present:
        if 'biometric_risk_score' in summary.columns:
            map_df = map_df.merge(summary[[group_col,'biometric_risk_score']], left_on='pincode', right_on=group_col, how='left')
    else:
        # aggregated view (district/state): use summary computed earlier
        map_df = summary.copy()
        # For monthly drilldown, use average from panel over the month
        monthly = panel_iso[panel_iso['month'] == month_dt].groupby(group_col).agg({'total_all':'sum','updates_per_10k':'mean'}).reset_index()
        map_df = map_df.merge(monthly, on=group_col, how='left')

    # Feature id property: find candidate property name that contains 'pin' or 'pincode'
    sample_props = geojson['features'][0]['properties']
    prop_key = None
    for k in sample_props.keys():
        if 'pin' in k.lower() or 'pincode' in k.lower() or 'postal' in k.lower():
            prop_key = k
            break
    if prop_key is None:
        st.warning("Could not automatically detect property for pincode in GeoJSON. You may need to edit 'prop_key' manually in the code.")
        prop_key = list(sample_props.keys())[0]

    # assemble mapping for Plotly
    # map_df must have a column matching the geojson's property (string). Standardize to strings with zero-padding.
    if group_col == 'pincode':
        map_df['pincode_str'] = map_df['pincode'].apply(lambda x: str(x).zfill(6))
        geo_featureid = f"properties.{prop_key}"
        # prepare metric
        if view_metric not in map_df.columns:
            st.warning(f"{view_metric} not available for selected aggregation; falling back to updates_per_10k.")
            view_metric = 'updates_per_10k'
        fig = px.choropleth_mapbox(
            map_df,
            geojson=geojson,
            locations='pincode_str',
            featureidkey=geo_featureid,
            color=view_metric,
            color_continuous_scale="YlOrRd",
            mapbox_style="carto-positron",
            zoom=4,
            center={"lat": 22.0, "lon": 80.0},
            opacity=0.7,
            labels={view_metric: view_metric}
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        # district/state view: need geojson with district features (unlikely). We'll fallback to bar chart/top ranks
        st.info("Geo-visualization for district/state aggregation not supported with pincode GeoJSON. See ranking table below.")
        # fallback: bar chart top 20 by metric
        topn = map_df.sort_values('avg_updates_per_10k', ascending=False).head(20)
        bar = px.bar(topn, x=group_col, y='avg_updates_per_10k', title=f"Top 20 {group_col} by avg updates per 10k")
        st.plotly_chart(bar, use_container_width=True)

# -----------------------
# Time series & correlations
# -----------------------
st.header("Trends & Correlations")

col1, col2 = st.columns([2,1])
with col1:
    st.subheader("Time-series: total updates (selected region)")
    region_choice = st.selectbox("Choose region for time series", options=sorted(panel[group_col].dropna().unique()))
    ts = panel_iso[panel_iso[group_col] == region_choice].sort_values('month')
    if not ts.empty:
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(x=ts['month'], y=ts['total_enrol'], name='Enrolments'))
        fig_ts.add_trace(go.Scatter(x=ts['month'], y=ts['total_demo'], name='Demo updates'))
        fig_ts.add_trace(go.Scatter(x=ts['month'], y=ts['total_bio'], name='Bio updates'))
        fig_ts.update_layout(template='plotly_white', height=400)
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.write("No time series data for selected region.")

with col2:
    st.subheader("Population vs Updates (scatter)")
    if 'population' in panel.columns and panel['population'].sum() > 0:
        latest_month = panel_iso['month'].max()
        scatter_df = panel_iso[panel_iso['month']==latest_month].dropna(subset=['population'])
        scatter_df['updates_per_10k'] = (scatter_df['total_all'] / scatter_df['population']) * 10000
        fig_sc = px.scatter(scatter_df, x='population', y='updates_per_10k', size='total_all',
                            hover_data=[group_col,'total_all','population'], title="Population vs Updates per 10k (latest month)")
        st.plotly_chart(fig_sc, use_container_width=True)
        # compute Pearson
        corr = scatter_df['population'].corr(scatter_df['updates_per_10k'])
        st.markdown(f"**Pearson correlation (population vs updates_per_10k):** {corr:.3f}")
    else:
        st.write("Population data not available for scatter plot.")

# -----------------------
# Ranked lists & anomaly table (for PDF copy)
# -----------------------
st.header("Rankings & Anomalies (copy to PDF)")

st.subheader("Top 20 regions by avg updates per 10k")
rank_df = summary.sort_values('avg_updates_per_10k', ascending=False).head(20)
st.dataframe(rank_df[[group_col,'avg_updates_per_10k','SUII_demo','YUR_octdec','biometric_risk_score']].round(3))

st.subheader("Detected anomalies (recent months)")
anom_recent = panel_iso[panel_iso['anomaly']].sort_values('month', ascending=False)
st.dataframe(anom_recent[[group_col,'month','total_all','z_pct','iso_anom']].head(50))

st.markdown("---")
st.markdown("### Notes & next steps")
st.markdown("""
- If pincode GeoJSON isn't perfectly aligned with your pincode keys, you may need to clean the GeoJSON properties (open the file and inspect `features[*].properties`).  
- If pincode-level population is not available, use district-level Census 2011 population as a proxy and mention the limitation in your submission. (Census district population data: censusindia.gov.in). :contentReference[oaicite:3]{index=3}  
- You can add election overlay by populating `election_periods` and shading months.  
- For final PDF: take snapshots of the choropleth, top-ranked tables, and the time-series; include the per-10k metrics and the SUII heatmap.
""")
