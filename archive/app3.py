"""
Streamlit dashboard for UIDAI Hackathon
- Loads enrolment / demographic / biometric CSVs
- Loads pincode GeoJSON & pincode census CSV
- Computes per-capita metrics, SUII, YUR, Biometric Risk Score
- Detects anomalies (z-score + IsolationForest)
- Produces choropleths, time-series, scatter, ranked tables
- Generates plain-language summary text for officials

Save this file as app_streamlit_uidai.py and run:
streamlit run app_streamlit_uidai.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
from scipy.stats import zscore
from sklearn.ensemble import IsolationForest
import plotly.express as px
import plotly.graph_objects as go
import os
import textwrap

# ----------------------------
# CONFIG
# ----------------------------
ENROL_FILE = "combined enrolment.csv"
DEMO_FILE = "combined demographic.csv"
BIO_FILE  = "combined biometrics.csv"
GEOJSON_FILE = "All_India_pincode.geojson"
CENSUS_FILE = "consolidated_pincode_census.csv"
DATE_COL = "date"    # expected column name in UIDAI files
OCT_DEC_MONTHS = [10,11,12]
Z_THRESH = 2.5
ISO_CONTAM = 0.03

st.set_page_config(page_title="UIDAI — Pincode Analysis (Simple Language)", layout="wide")

# ----------------------------
# Helper functions
# ----------------------------
def safe_read_csv(path):
    """Robust CSV read with delimiter fallbacks."""
    if not os.path.exists(path):
        st.error(f"Missing file: {path}")
        return None
    try:
        df = pd.read_csv(path, engine="python", low_memory=False)
        if df.shape[1] == 1:
            # try other separators
            for sep in ["|",";","\t"]:
                try:
                    df2 = pd.read_csv(path, sep=sep, engine="python", low_memory=False)
                    if df2.shape[1] > 1:
                        df = df2
                        break
                except:
                    pass
        return df
    except Exception as e:
        st.error(f"Error reading {path}: {e}")
        return None

def parse_dates(df, date_col=DATE_COL):
    if df is None: return None
    df = df.copy()
    if date_col not in df.columns:
        st.warning(f"Warning: date column '{date_col}' not found. Attempting to infer.")
        # try first column
        candidates = [c for c in df.columns if 'date' in c.lower()]
        if candidates:
            date_col = candidates[0]
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
    if df[date_col].isna().sum() > 0:
        st.warning(f"{df[date_col].isna().sum()} rows had unparsable dates; they will be dropped.")
    df = df.dropna(subset=[date_col])
    df[date_col] = pd.to_datetime(df[date_col])
    return df

def standardize_cols(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df

def pad_pincode(x):
    try:
        s = str(int(float(x)))
    except:
        s = str(x).strip()
    s = s.zfill(6) if len(s) <= 6 else s
    return s

def detect_age_cols(columns):
    """Find likely age columns (5-17 etc.)"""
    cols = []
    for c in columns:
        low = c.lower()
        if ("5" in low and "17" in low) or ("5_17" in low) or ("5-17" in low) or ("5...14" in low) or ("x5" in low):
            cols.append(c)
    # fallback heuristics
    if not cols:
        for c in columns:
            if "age" in c.lower() and ("5" in c or "17" in c or "child" in c.lower()):
                cols.append(c)
    return cols

# ----------------------------
# Load files (cached)
# ----------------------------
@st.cache_data
def load_all():
    enrol = safe_read_csv(ENROL_FILE)
    demo = safe_read_csv(DEMO_FILE)
    bio  = safe_read_csv(BIO_FILE)
    geo = None
    census = None
    # geojson
    if os.path.exists(GEOJSON_FILE):
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            geo = json.load(f)
    else:
        geo = None
    # census
    if os.path.exists(CENSUS_FILE):
        census = pd.read_csv(CENSUS_FILE, low_memory=False)
    return enrol, demo, bio, geo, census

enrol, demo, bio, geojson, census_raw = load_all()

# ----------------------------
# UI: header + data checks
# ----------------------------
st.title("UIDAI — Pincode Analysis & Plain-Language Insights")
st.markdown("This dashboard computes simple, policy-relevant metrics and produces maps, charts and a short plain-language summary suitable for UIDAI officials.")

if enrol is None or demo is None or bio is None:
    st.error("Please place the three UIDAI CSVs (enrolment.csv, demographic.csv, biometric.csv) in the app folder.")
    st.stop()

# standardize and parse dates
enrol = standardize_cols(enrol); demo = standardize_cols(demo); bio = standardize_cols(bio)
enrol = parse_dates(enrol); demo = parse_dates(demo); bio = parse_dates(bio)

# quick preview
with st.expander("Preview first rows of input files"):
    st.subheader("Enrolment sample")
    st.dataframe(enrol.head())
    st.subheader("Demographic sample")
    st.dataframe(demo.head())
    st.subheader("Biometric sample")
    st.dataframe(bio.head())

# ----------------------------
# Choose aggregation (pincode preferred)
# ----------------------------
agg_level = st.sidebar.selectbox("Aggregate by", ["pincode","district","state"], index=0)
st.sidebar.markdown("We recommend **pincode** aggregation for maps and precise targeting. Use district/state if pincodes are incomplete.")

group_col = agg_level

# ----------------------------
# Preprocess datasets: ensure group_col exists; create month column
# ----------------------------
def prep_dataset(df, expected_group=group_col):
    df = df.copy()
    # detect group col case-insensitively
    cols_lower = [c.lower() for c in df.columns]
    if expected_group not in cols_lower:
        # try to find approximate name
        for c in df.columns:
            if expected_group in c.lower():
                df = df.rename(columns={c: expected_group})
                break
    # If still missing and group_col is pincode, try 'pincode' variants
    if expected_group not in df.columns and expected_group == 'pincode':
        for c in df.columns:
            if 'pin' in c.lower():
                df = df.rename(columns={c: 'pincode'})
                break
    if expected_group not in df.columns:
        st.warning(f"{expected_group} column missing in dataset. Aggregation will fail or fallback to global.")
    # pad pincodes
    if expected_group in df.columns and expected_group == 'pincode':
        df['pincode'] = df['pincode'].apply(lambda x: pad_pincode(x))
    # month for aggregation
    df['month'] = df[DATE_COL].dt.to_period('M').dt.to_timestamp()
    return df

enrol_p = prep_dataset(enrol)
demo_p  = prep_dataset(demo)
bio_p   = prep_dataset(bio)

# detect age columns to use for youth metrics
enrol_age_cols = detect_age_cols(enrol_p.columns)
demo_age_cols = detect_age_cols(demo_p.columns)
bio_age_cols  = detect_age_cols(bio_p.columns)

# If none detected, fallback: use numeric columns beyond date/location
if not enrol_age_cols:
    enrol_age_cols = [c for c in enrol_p.columns if c not in ['date','month','state','district','pincode']][:3]
if not demo_age_cols:
    demo_age_cols = [c for c in demo_p.columns if c not in ['date','month','state','district','pincode']][:2]
if not bio_age_cols:
    bio_age_cols = [c for c in bio_p.columns if c not in ['date','month','state','district','pincode']][:2]

st.sidebar.markdown(f"Detected youth/age columns (heuristic):\n- enrol: {enrol_age_cols}\n- demo: {demo_age_cols}\n- bio:  {bio_age_cols}")

# ----------------------------
# Aggregate monthly by group
# ----------------------------
def aggregate_monthly(df, group_by, age_cols):
    if group_by in df.columns:
        cols = age_cols.copy()
        # convert age cols to numeric
        for c in cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        grouped = df.groupby([group_by,'month'])[cols].sum().reset_index()
        grouped['total_updates'] = grouped[cols].sum(axis=1)
        return grouped
    else:
        # fallback: aggregate just by month and provide a global row
        cols = age_cols.copy()
        for c in cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        grouped = df.groupby(['month'])[cols].sum().reset_index()
        grouped[group_by] = 'ALL'
        grouped = grouped[[group_by,'month'] + cols]
        grouped['total_updates'] = grouped[cols].sum(axis=1)
        return grouped

enrol_mon = aggregate_monthly(enrol_p, group_col, enrol_age_cols)
demo_mon  = aggregate_monthly(demo_p, group_col, demo_age_cols)
bio_mon   = aggregate_monthly(bio_p, group_col, bio_age_cols)

# ----------------------------
# Merge panel
# ----------------------------
panel = pd.merge(enrol_mon, demo_mon, on=[group_col,'month'], how='outer', suffixes=('_enrol','_demo'))
panel = pd.merge(panel, bio_mon, on=[group_col,'month'], how='outer')
# unify columns safely
panel = panel.fillna(0)
# compute totals
panel['total_enrol'] = panel[[c for c in panel.columns if c.endswith('_enrol') and 'total' not in c]].sum(axis=1) if any(c.endswith('_enrol') for c in panel.columns) else 0
# unify demo and bio totals if present
if 'total_updates' in demo_mon.columns:
    panel['total_demo'] = panel.get('total_updates_demo', panel.get('total_updates',0))
else:
    panel['total_demo'] = 0
panel['total_bio'] = panel.get('total_updates', 0)  # from bio merge
panel['total_all'] = panel['total_enrol'] + panel['total_demo'] + panel['total_bio']

# ----------------------------
# Merge census population by pincode (if available)
# ----------------------------
census = None
if census_raw is not None:
    census = census_raw.copy()
    census.columns = [c.strip() for c in census.columns]
    # try to find pincode column in census
    pcol = None
    for c in census.columns:
        if 'pinc' in c.lower():
            pcol = c
            break
    if pcol:
        census = census.rename(columns={pcol:'pincode'})
        census['pincode'] = census['pincode'].apply(lambda x: pad_pincode(x))
        # try to find population column
        popcol = None
        for c in census.columns:
            if c.lower() in ['persons','population','totals','total']:
                popcol = c
                break
        # fallback heuristics
        if popcol is None:
            # find numeric big column
            numeric_cols = census.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                popcol = numeric_cols[0]
        if popcol:
            census['population'] = pd.to_numeric(census[popcol], errors='coerce').fillna(0)
            # optional child population columns
            child_col = None
            for c in census.columns:
                if 'x5' in c.lower() or '5' in c.lower() and '14' in c.lower():
                    child_col = c
                    break
            if child_col:
                census['child_pop_5_14'] = pd.to_numeric(census[child_col], errors='coerce').fillna(0)
        else:
            st.warning("Census loaded but population column not detected automatically.")
    else:
        st.warning("Census file does not seem to have a pincode column. Will not join population.")

# Attach population where possible (only for pincode aggregation)
if group_col == 'pincode' and census is not None and 'pincode' in census.columns:
    # grab latest month per pincode in panel then merge population
    panel = panel.merge(census[['pincode','population','child_pop_5_14']] if 'child_pop_5_14' in census.columns else census[['pincode','population']],
                        on='pincode', how='left')

# compute per-10k metrics
panel['updates_per_10k'] = np.where(panel.get('population',0)>0, panel['total_all'] / panel['population'] * 10000, np.nan)
panel['bio_per_10k'] = np.where(panel.get('population',0)>0, panel['total_bio'] / panel['population'] * 10000, np.nan)
panel['enrol_per_10k'] = np.where(panel.get('population',0)>0, panel['total_enrol'] / panel['population'] * 10000, np.nan)
panel['coverage_percent'] = np.where(panel.get('population',0)>0, panel['total_enrol'] / panel['population'] * 100, np.nan)

# ----------------------------
# Compute indices per region
# - SUII = mean(Oct-Dec updates) / mean(other months updates)
# - YUR = youth updates share in Oct-Dec (use detected age columns)
# - Biometric Risk Score = (child_pop estimate) / (bio_per_10k + 1)
# ----------------------------
def compute_indices(panel_df):
    rows = []
    groups = panel_df[group_col].unique()
    for g in groups:
        df_g = panel_df[panel_df[group_col]==g].copy()
        if df_g.empty:
            continue
        df_g['month_num'] = df_g['month'].dt.month
        oct_mask = df_g['month_num'].isin(OCT_DEC_MONTHS)
        other_mask = ~oct_mask
        # demo Oct-Dec mean
        demo_oct_mean = df_g.loc[oct_mask,'total_demo'].mean() if 'total_demo' in df_g.columns else np.nan
        demo_other_mean = df_g.loc[other_mask,'total_demo'].mean() if 'total_demo' in df_g.columns else np.nan
        bio_oct_mean = df_g.loc[oct_mask,'total_bio'].mean() if 'total_bio' in df_g.columns else np.nan
        bio_other_mean = df_g.loc[other_mask,'total_bio'].mean() if 'total_bio' in df_g.columns else np.nan
        SUII_demo = demo_oct_mean / demo_other_mean if demo_other_mean and not np.isnan(demo_other_mean) else np.nan
        SUII_bio  = bio_oct_mean / bio_other_mean if bio_other_mean and not np.isnan(bio_other_mean) else np.nan
        # YUR: look at demo/bio youth columns if detected
        youth_cols = [c for c in df_g.columns if ('5_17' in c) or ('5' in c and '17' in c) or ('x5' in c and '14' in c)]
        youth_oct = df_g.loc[oct_mask, youth_cols].sum().sum() if youth_cols else 0
        total_oct = df_g.loc[oct_mask, ['total_demo','total_bio','total_enrol']].sum().sum()
        YUR = youth_oct / total_oct if total_oct and total_oct>0 else np.nan
        avg_updates_per_10k = df_g['updates_per_10k'].mean() if 'updates_per_10k' in df_g.columns else np.nan
        # biometric risk: use census child population if available, else use youth_oct as proxy
        child_pop = df_g['child_pop_5_14'].mean() if 'child_pop_5_14' in df_g.columns else np.nan
        if np.isnan(child_pop) or child_pop==0:
            # approximate by average youth updates times some factor
            child_pop = df_g[youth_cols].sum().sum() if youth_cols else np.nan
        bio_per_10k_avg = df_g['bio_per_10k'].mean() if 'bio_per_10k' in df_g.columns else np.nan
        biometric_risk = child_pop / (bio_per_10k_avg + 1) if (not np.isnan(child_pop) and not np.isnan(bio_per_10k_avg)) else np.nan
        rows.append({
            group_col: g,
            "SUII_demo": SUII_demo,
            "SUII_bio": SUII_bio,
            "YUR_octdec": YUR,
            "avg_updates_per_10k": avg_updates_per_10k,
            "biometric_risk_score": biometric_risk
        })
    return pd.DataFrame(rows)

indices_df = compute_indices(panel)

# ----------------------------
# Anomaly detection (z-score on pct change + IsolationForest)
# ----------------------------
panel_sorted = panel.sort_values([group_col,'month']).copy()
panel_sorted['pct_change'] = panel_sorted.groupby(group_col)['total_all'].pct_change().fillna(0)
# z-score per group
panel_sorted['z_pct'] = panel_sorted.groupby(group_col)['pct_change'].transform(lambda x: zscore(x.replace([np.inf,-np.inf],0).fillna(0)))
panel_sorted['z_anom'] = panel_sorted['z_pct'].abs() > Z_THRESH

# isolation forest per group
def iso_flags(df_g):
    out = df_g.copy()
    if len(out) >= 8:
        iso = IsolationForest(contamination=ISO_CONTAM, random_state=42)
        vals = out[['total_all']].fillna(0).values
        preds = iso.fit_predict(vals)
        out['iso_anom'] = preds == -1
    else:
        out['iso_anom'] = False
    return out

panel_iso = panel_sorted.groupby(group_col, group_keys=False).apply(iso_flags).reset_index(drop=True)
panel_iso['anomaly'] = panel_iso['z_anom'] | panel_iso['iso_anom']

# ----------------------------
# UI: selection controls
# ----------------------------
st.sidebar.header("Map & Filters")
metric_choices = {
    "Updates per 10k population": "updates_per_10k",
    "Total updates (raw)": "total_all",
    "SUII (Demo Oct-Dec intensity)": "SUII_demo",
    "YUR (Youth share Oct-Dec)": "YUR_octdec",
    "Biometric risk score": "biometric_risk_score",
    "Coverage % (enrol / pop)": "coverage_percent"
}
metric_label = st.sidebar.selectbox("Map metric", list(metric_choices.keys()), index=0)
metric = metric_choices[metric_label]
month_options = sorted(panel['month'].dt.strftime('%Y-%m').unique())
default_month = month_options[-1] if month_options else None
sel_month = st.sidebar.selectbox("Select month for map", month_options, index=len(month_options)-1 if month_options else 0)

# ----------------------------
# Prepare map dataframe for selected month
# ----------------------------
month_dt = pd.to_datetime(sel_month + "-01")
panel_month = panel_iso[panel_iso['month'] == month_dt].copy()

# merge indices into panel_month
panel_month = panel_month.merge(indices_df, on=group_col, how='left')

# convert pincode strings
if group_col == 'pincode':
    panel_month['pincode_str'] = panel_month['pincode'].apply(lambda x: pad_pincode(x))

# ----------------------------
# Plot choropleth (pincode geojson expected to have property 'Pincode')
# ----------------------------
st.header("Choropleth Map (Pincode-level)")

if geojson is None:
    st.error("GeoJSON not found. Place All_India_pincode.geojson in the app folder.")
else:
    # determine feature property name for pincode (heuristic)
    sample_props = geojson['features'][0]['properties']
    p_prop = None
    for k in sample_props.keys():
        if 'pinc' in k.lower():
            p_prop = k
            break
    if p_prop is None:
        p_prop = list(sample_props.keys())[0]  # fallback
    # prepare locations and featureidkey
    if group_col == 'pincode':
        # ensure match: geo feature property likely stores numeric string; make sure both sides are zero-padded
        panel_month['loc'] = panel_month['pincode_str']
        featureidkey = f"properties.{p_prop}"
    else:
        panel_month['loc'] = panel_month[group_col]
        featureidkey = f"properties.{p_prop}"

    # choose color
    col_data = panel_month.get(metric)
    if col_data is None:
        st.warning(f"Metric '{metric}' not available for this aggregation/month. Showing updates_per_10k instead.")
        metric = 'updates_per_10k'

    # build choropleth
    try:
        fig_map = px.choropleth_mapbox(
            panel_month,
            geojson=geojson,
            locations="loc",
            featureidkey=featureidkey,
            color=metric,
            color_continuous_scale="YlOrRd",
            mapbox_style="carto-positron",
            zoom=4,
            center={"lat": 22.0, "lon": 80.0},
            opacity=0.7,
            labels={metric: metric_label}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        st.error(f"Error drawing map: {e}. Check that geojson property with pincodes is named similarly to '{p_prop}' and that panel pincode strings match.")

# ----------------------------
# Time series explorer (simple language annotations)
# ----------------------------
st.header("Time-series Explorer")

col_ts_left, col_ts_right = st.columns([2,1])
with col_ts_left:
    st.subheader("Select region to view monthly trend and anomalies")
    if group_col == 'pincode':
        regions = sorted(panel[group_col].dropna().unique())
        sel_region = st.selectbox("Choose pincode", regions, index=regions.index(panel[group_col].dropna().unique()[-1]) if len(regions)>0 else 0)
        df_region = panel_iso[panel_iso[group_col] == sel_region].sort_values('month')
    else:
        regions = sorted(panel[group_col].dropna().unique())
        sel_region = st.selectbox("Choose region", regions)
        df_region = panel_iso[panel_iso[group_col] == sel_region].sort_values('month')

    if df_region.empty:
        st.write("No data for selected region.")
    else:
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(x=df_region['month'], y=df_region['total_enrol'], mode='lines+markers', name='Enrolments'))
        fig_ts.add_trace(go.Scatter(x=df_region['month'], y=df_region['total_demo'], mode='lines+markers', name='Demographic updates'))
        fig_ts.add_trace(go.Scatter(x=df_region['month'], y=df_region['total_bio'], mode='lines+markers', name='Biometric updates'))
        # anomalies
        anom_r = df_region[df_region['anomaly']]
        if not anom_r.empty:
            fig_ts.add_trace(go.Scatter(x=anom_r['month'], y=anom_r['total_all'], mode='markers', name='Anomaly', marker=dict(color='red', size=10, symbol='x')))
        # shade Oct-Dec for each year
        years = sorted(df_region['month'].dt.year.unique())
        for y in years:
            fig_ts.add_vrect(x0=f"{y}-10-01", x1=f"{y}-12-31", fillcolor="LightSkyBlue", opacity=0.12, line_width=0)
        fig_ts.update_layout(title=f"Monthly updates for {sel_region}", xaxis_title="Month", yaxis_title="Count", template="plotly_white")
        st.plotly_chart(fig_ts, use_container_width=True)

with col_ts_right:
    st.subheader("Simple explanation (plain language)")
    # Generate simple textual explanation for selected region
    latest = df_region.iloc[-1] if not df_region.empty else None
    if latest is not None:
        suii_demo = indices_df[indices_df[group_col]==sel_region]['SUII_demo'].values[0] if sel_region in list(indices_df[group_col]) else None
        y_share = indices_df[indices_df[group_col]==sel_region]['YUR_octdec'].values[0] if sel_region in list(indices_df[group_col]) else None
        risk = indices_df[indices_df[group_col]==sel_region]['biometric_risk_score'].values[0] if sel_region in list(indices_df[group_col]) else None

        # Build plain-language points
        bullets = []
        bullets.append(f"Latest month ({latest['month'].strftime('%b %Y')}): total updates = {int(latest['total_all'])}")
        if not np.isnan(suii_demo):
            if suii_demo > 1.2:
                bullets.append(f"Updates are noticeably higher in Oct–Dec (SUII ≈ {suii_demo:.2f}); suggests seasonal demand.")
            else:
                bullets.append(f"No large Oct–Dec surge detected (SUII ≈ {suii_demo:.2f}).")
        if not np.isnan(y_share):
            bullets.append(f"During Oct–Dec, {y_share*100:.1f}% of updates were from youth age-groups (possible education/exam linkage).")
        if not np.isnan(risk):
            bullets.append(f"Biometric risk score ≈ {risk:.1f} (higher means more children with relatively fewer biometric updates).")
        # anomaly note
        if latest['anomaly']:
            bullets.append("Recent month is flagged as anomalous — investigate: possible mass registration/update drive, migration, or a data artefact.")
        else:
            bullets.append("No recent anomaly flagged.")

        # Show as plain text
        for b in bullets:
            st.write("• " + b)
    else:
        st.write("No data to explain.")

# ----------------------------
# Correlations and rankings
# ----------------------------
st.header("Correlations & Ranked Lists (easy copy for report)")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Population vs Updates per 10k (latest month)")
    # latest month across panel
    latest_month = panel_iso['month'].max()
    latest_df = panel_iso[panel_iso['month'] == latest_month].copy()
    if 'population' in latest_df.columns and latest_df['population'].sum() > 0:
        latest_df['updates_per_10k'] = latest_df['total_all'] / latest_df['population'] * 10000
        fig_scatter = px.scatter(latest_df, x='population', y='updates_per_10k', hover_data=[group_col,'total_all'], title=f"Population vs updates_per_10k ({latest_month.strftime('%b %Y')})")
        st.plotly_chart(fig_scatter, use_container_width=True)
        corr = latest_df['population'].corr(latest_df['updates_per_10k'])
        st.write(f"Pearson correlation: {corr:.3f}")
    else:
        st.write("Population data not available for this view.")

with col2:
    st.subheader("Top 20 regions by Biometric Risk Score")
    top_risk = indices_df.sort_values('biometric_risk_score', ascending=False).head(20)
    st.dataframe(top_risk[[group_col,'biometric_risk_score','SUII_demo','YUR_octdec']].round(3))

st.subheader("Top 20 regions by Oct–Dec surge (SUII_demo)")
top_suii = indices_df.sort_values('SUII_demo', ascending=False).head(20)
st.dataframe(top_suii[[group_col,'SUII_demo','avg_updates_per_10k']].round(3))

st.subheader("Recent anomalies (latest 50 rows)")
st.dataframe(panel_iso[panel_iso['anomaly']].sort_values('month', ascending=False)[[group_col,'month','total_all','z_pct','iso_anom']].head(50))

# ----------------------------
# Plain-language summary generator (auto)
# ----------------------------
st.header("Auto-generated Plain-language Summary (copy into your PDF)")

def generate_plain_summary(indices_df, panel_iso, top_n=10):
    now = datetime.now().strftime('%Y-%m-%d')
    latest_month = panel_iso['month'].max().strftime('%B %Y') if not panel_iso.empty else 'N/A'
    text = []
    text.append(f"UIDAI Hackathon — Auto Summary (generated {now})")
    text.append(f"Data covered up to: {latest_month}")
    text.append("")
    # top risk
    tr = indices_df.dropna(subset=['biometric_risk_score']).sort_values('biometric_risk_score', ascending=False).head(top_n)
    if not tr.empty:
        text.append("Top regions by Biometric Risk (high child population + low biometric updates):")
        for i,r in tr.iterrows():
            text.append(f"- {r[group_col]}: risk score {r['biometric_risk_score']:.1f}, SUII_demo {r['SUII_demo']:.2f}, YUR {0 if np.isnan(r['YUR_octdec']) else r['YUR_octdec']*100:.1f}%")
    else:
        text.append("No biometric risk scores available (population/age data missing).")
    text.append("")
    # top seasonal surge
    ts = indices_df.dropna(subset=['SUII_demo']).sort_values('SUII_demo', ascending=False).head(top_n)
    if not ts.empty:
        text.append("Top regions with Oct–Dec surge (possible exam/seasonal effect):")
        for i,r in ts.iterrows():
            text.append(f"- {r[group_col]}: Oct–Dec intensity SUII_demo = {r['SUII_demo']:.2f}")
    else:
        text.append("No SUII values (insufficient time series).")
    text.append("")
    # anomalies
    anom_recent = panel_iso[panel_iso['anomaly']].sort_values('month', ascending=False).head(10)
    if not anom_recent.empty:
        text.append("Recent anomalous months (inspect for drives/migration/data issues):")
        for _,a in anom_recent.iterrows():
            text.append(f"- {a[group_col]}: {a['month'].strftime('%b %Y')} total updates {int(a['total_all'])} (z_pct {a['z_pct']:.2f})")
    else:
        text.append("No strong anomalies detected in the recent months.")
    text.append("")
    # actionable recommendations
    text.append("Suggested immediate actions (plain language):")
    text.append("- For top-risk pincodes: run mobile biometric update camps targeted at youth (5–17→18 transition).")
    text.append("- For high SUII pincodes: coordinate with education boards and schedule extra update counters during Sep–Dec.")
    text.append("- For anomalous months: check logs (mass camps/awareness drives/DBT events) and validate data quality.")
    text.append("- For low-coverage pincodes (low enrol_per_10k): prioritize enrolment drives & CSC capacity.")
    return "\n".join(text)

plain_summary = generate_plain_summary(indices_df, panel_iso, top_n=10)
st.text_area("Plain-language auto summary (editable)", plain_summary, height=300)

# ----------------------------
# Downloadable artifacts: CSVs and summary text
# ----------------------------
st.header("Export / Download")
# prepare CSVs
csv1 = indices_df.to_csv(index=False).encode('utf-8')
csv2 = panel_iso.to_csv(index=False).encode('utf-8')

st.download_button("Download indices_summary.csv", csv1, "indices_summary.csv", "text/csv")
st.download_button("Download panel_with_anomalies.csv", csv2, "panel_with_anomalies.csv", "text/csv")
st.download_button("Download plain-language summary (.txt)", plain_summary.encode('utf-8'), "plain_summary.txt", "text/plain")

st.markdown("""
### Notes for the submission PDF (how to use outputs)
1. Use the choropleth snapshots for: **updates_per_10k**, **SUII_demo**, and **biometric_risk_score**.  
2. Include the top-10 tables and an example anomalous month as a case study.  
3. Copy the plain-language summary into the executive summary of your PDF and refine to local names (district/pincode).  
4. Mention assumptions: population comes from consolidated_pincode_census; if missing, we used district proxies.
""")

st.success("Dashboard ready — use the map, charts and the plain-language text for a concise government-friendly report.")
