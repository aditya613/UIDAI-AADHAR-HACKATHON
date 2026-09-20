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
MAX_REGIONS_FOR_ISOLATION = 5000  # Skip IsolationForest if more regions
DEBUG_MODE = True  # Set False to hide debug messages

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

# Robust z-score that tolerates constant series and NaNs
def safe_zscore(series):
    vals = series.replace([np.inf, -np.inf], 0).fillna(0).to_numpy()
    if vals.size == 0:
        return pd.Series([], index=series.index, dtype=float)
    if np.all(vals == vals[0]):
        return pd.Series(np.zeros_like(vals, dtype=float), index=series.index)
    with np.errstate(invalid='ignore', divide='ignore'):
        zs = zscore(vals, nan_policy='omit')
    return pd.Series(np.nan_to_num(zs, nan=0.0), index=series.index)

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
        try:
            with open(PIN_GEOJSON, 'r', encoding='utf-8') as f:
                geo = json.load(f)
        except Exception as e:
            if DEBUG_MODE:
                st.warning(f"Failed to load GeoJSON: {e}")
    if os.path.exists(PIN_POP):
        try:
            pop = pd.read_csv(PIN_POP, dtype=str, low_memory=False)
        except Exception as e:
            if DEBUG_MODE:
                st.warning(f"Failed to load population data: {e}")
    return enrol, demo, bio, geo, pop

try:
    enrol, demo, bio, geojson, pop_df = load_data()
except Exception as e:
    st.error(f"Fatal error loading data: {e}")
    st.stop()

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

# Add sampling option for testing
if DEBUG_MODE:
    use_sample = st.sidebar.checkbox("Use sample data (faster)", value=False)
    if use_sample:
        sample_pct = st.sidebar.slider("Sample %", 10, 100, 20)
        enrol = enrol.sample(frac=sample_pct/100, random_state=42)
        demo = demo.sample(frac=sample_pct/100, random_state=42)
        bio = bio.sample(frac=sample_pct/100, random_state=42)
        st.sidebar.warning(f"Using {sample_pct}% sample")

# -----------------------
# Aggregate monthly at pincode level (preferred)
# -----------------------
def aggregate_monthly(df, group_col, age_cols):
    df = df.copy()
    if DATE_COL not in df.columns:
        st.error(f"{DATE_COL} missing from input CSV.")
        return pd.DataFrame()
    df['month'] = df[DATE_COL].dt.to_period('M').dt.to_timestamp()
    if 'state' in df.columns:
        df['state'] = df['state'].astype(str).str.strip()
    # ensure group col exists
    if group_col not in df.columns:
        st.error(f"Grouping column '{group_col}' not found in dataset.")
        return pd.DataFrame()
    # sanitize pincodes
    if group_col == 'pincode':
        df['pincode'] = df['pincode'].apply(lambda x: ensure_pincode_str(x))
    
    # Preserve state column if it exists (for heatmap visualization)
    group_cols = [group_col, 'month']
    if 'state' in df.columns and group_col != 'state':
        # Get the first state per pincode (they should be consistent)
        state_map = df.groupby(group_col)['state'].first()
        out = df.groupby(group_cols)[age_cols].sum().reset_index()
        out = out.merge(state_map.reset_index(), on=group_col, how='left')
    else:
        out = df.groupby(group_cols)[age_cols].sum().reset_index()
    
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

if DEBUG_MODE:
    st.sidebar.markdown(f"**Detected age columns:**\n\nenrol: {enrol_age_cols}\n\ndemo: {demo_age_cols}\n\nbio: {bio_age_cols}")

group_col = agg_level

@st.cache_data(show_spinner=False)
def process_panel_data(group_col):
    """Cache expensive panel aggregation"""
    enrol_m = aggregate_monthly(enrol, group_col, enrol_age_cols)
    demo_m = aggregate_monthly(demo, group_col, demo_age_cols)
    bio_m  = aggregate_monthly(bio, group_col, bio_age_cols)
    
    # Merge by group + month
    panel = enrol_m.merge(demo_m, on=[group_col,'month'], how='outer', suffixes=('_enrol','_demo'))
    panel = panel.merge(bio_m, on=[group_col,'month'], how='outer', suffixes=('','_bio'))
    panel = panel.fillna(0)

    # Coalesce any duplicated state columns into a single 'state'
    state_cols = [c for c in panel.columns if c.startswith('state')]
    if state_cols:
        panel['state'] = panel[state_cols].bfill(axis=1).iloc[:,0]
        drop_cols = [c for c in state_cols if c != 'state']
        if drop_cols:
            panel = panel.drop(columns=drop_cols)
    # unify total columns
    panel['total_enrol'] = panel[[c for c in panel.columns if c.endswith('_enrol') and 'total' in c]].sum(axis=1) if any('total' in c and c.endswith('_enrol') for c in panel.columns) else panel.get('total',0)
    panel['total_demo']  = panel.get('total_demo', 0)
    panel['total_bio']   = panel.get('total_bio', 0)
    panel['total_all']   = panel['total_enrol'] + panel['total_demo'] + panel['total_bio']
    return panel

with st.spinner("Aggregating data by month..."):
    panel = process_panel_data(group_col)

st.success(f"✓ Data loaded: {len(panel)} records, {panel['month'].dt.to_period('M').nunique()} months, {panel[group_col].nunique()} {group_col}s")

if DEBUG_MODE:
    st.sidebar.markdown("### Debug Info")
    st.sidebar.text(f"Panel shape: {panel.shape}")
    st.sidebar.text(f"Memory: {panel.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

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
# Compute indices (SUII, YUR, Biometric Risk) - OPTIMIZED
# -----------------------
with st.spinner("Computing indices..."):
    panel['month_num'] = panel['month'].dt.month
    panel['is_octdec'] = panel['month_num'].isin(OCTDEC)
    
    # Vectorized SUII computation
    octdec_stats = panel[panel['is_octdec']].groupby(group_col).agg({
        'total_demo': 'mean',
        'total_bio': 'mean'
    }).add_suffix('_oct')
    
    other_stats = panel[~panel['is_octdec']].groupby(group_col).agg({
        'total_demo': 'mean',
        'total_bio': 'mean'
    }).add_suffix('_other')
    
    summary = octdec_stats.join(other_stats, how='outer').reset_index()
    summary['SUII_demo'] = summary['total_demo_oct'] / summary['total_demo_other'].replace(0, np.nan)
    summary['SUII_bio'] = summary['total_bio_oct'] / summary['total_bio_other'].replace(0, np.nan)
    summary['avg_updates_per_10k'] = panel.groupby(group_col)['updates_per_10k'].mean().values
    
    # Simplified YUR computation
    child_cols = [c for c in panel.columns if '5_17' in c]
    if child_cols:
        octdec_panel = panel[panel['is_octdec']]
        yur_data = octdec_panel.groupby(group_col).agg({
            'total_all': 'sum',
            **{c: 'sum' for c in child_cols}
        })
        yur_data['child_sum'] = yur_data[child_cols].sum(axis=1)
        yur_data['YUR_octdec'] = yur_data['child_sum'] / yur_data['total_all'].replace(0, np.nan)
        summary = summary.merge(yur_data[['YUR_octdec']], left_on=group_col, right_index=True, how='left')
    else:
        summary['YUR_octdec'] = np.nan
    
    # Simplified risk computation
    if 'bio_per_10k' in panel.columns and child_cols:
        risk_data = panel.groupby(group_col).agg({
            **{c: 'sum' for c in child_cols},
            'bio_per_10k': 'mean'
        })
        risk_data['child_pop'] = risk_data[child_cols].sum(axis=1)
        risk_data['biometric_risk_score'] = risk_data['child_pop'] / (risk_data['bio_per_10k'] + 1)
        summary = summary.merge(risk_data[['biometric_risk_score']], left_on=group_col, right_index=True, how='left')
    else:
        summary['biometric_risk_score'] = np.nan
    
    if DEBUG_MODE:
        st.sidebar.info(f"Summary computed for {len(summary)} regions")
# -----------------------
# Anomaly detection (zscore on pct change + IsolationForest)
# -----------------------
with st.spinner("Detecting anomalies..."):
    panel_sorted = panel.sort_values([group_col,'month']).copy()
    panel_sorted['pct_change'] = panel_sorted.groupby(group_col)['total_all'].pct_change().fillna(0)
    panel_sorted['z_pct'] = panel_sorted.groupby(group_col)['pct_change'].transform(safe_zscore)
    panel_sorted['z_anom'] = panel_sorted['z_pct'].abs() > Z_THRESH
    
    n_regions = panel_sorted[group_col].nunique()
    
    # Skip IsolationForest for large datasets (too slow)
    if n_regions > MAX_REGIONS_FOR_ISOLATION:
        if DEBUG_MODE:
            st.warning(f"⚠️ Skipping IsolationForest (too many regions: {n_regions}). Using z-score only.")
        panel_sorted['iso_anom'] = False
        panel_iso = panel_sorted
    else:
        try:
            def add_iso_flags(df):
                out = df.copy()
                # Add group column if pandas excludes it (future behavior) to keep downstream joins stable
                if group_col not in out.columns:
                    out[group_col] = df.name
                if len(out) >= 8:
                    iso = IsolationForest(contamination=ISO_CONTAM, random_state=42)
                    vals = out[['total_all']].fillna(0).values
                    preds = iso.fit_predict(vals)
                    out['iso_anom'] = preds == -1
                else:
                    out['iso_anom'] = False
                return out
            try:
                panel_iso = panel_sorted.groupby(group_col, group_keys=False).apply(add_iso_flags, include_groups=False).reset_index(drop=True)
            except TypeError:
                # Fallback for older pandas that lack include_groups
                panel_iso = panel_sorted.groupby(group_col, group_keys=False).apply(add_iso_flags).reset_index(drop=True)
        except Exception as e:
            if DEBUG_MODE:
                st.warning(f"IsolationForest failed: {e}. Using z-score only.")
            panel_sorted['iso_anom'] = False
            panel_iso = panel_sorted
    
    panel_iso['anomaly'] = panel_iso['z_anom'] | panel_iso['iso_anom']

# -----------------------
# Map: choropleth for a selected month
# -----------------------
st.header("🗺️ Maps: India Visualization")

# Map type selector in sidebar
map_type = st.sidebar.radio("Map Type", ["Heatmap (State-level)", "Choropleth (Pincode)"], index=0)

if len(panel) == 0 or len(panel_iso) == 0:
    st.error("No data to display. Check that your CSV files have valid date columns and age columns.")
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
        
        # Add state info for heatmap
        if 'state' in sel.columns:
            state_map = sel[['pincode', 'state']].drop_duplicates()
            map_df = map_df.merge(state_map, on='pincode', how='left')
    else:
        # aggregated view (district/state): use summary computed earlier
        map_df = summary.copy()
        # For monthly drilldown, use average from panel over the month
        monthly = panel_iso[panel_iso['month'] == month_dt].groupby(group_col).agg({'total_all':'sum','updates_per_10k':'mean'}).reset_index()
        map_df = map_df.merge(monthly, on=group_col, how='left')
    
    # prepare metric
    if view_metric not in map_df.columns:
        st.warning(f"{view_metric} not available for selected aggregation; falling back to updates_per_10k.")
        view_metric = 'updates_per_10k'
    
    # -----------------------
    # HEATMAP VIEW (State-level scatter on India map)
    # -----------------------
    if map_type == "Heatmap (State-level)":
        st.subheader(f"📊 India Heatmap: {view_metric} ({month_sel})")
        
        # Check if state column exists
        if 'state' not in panel_iso.columns:
            st.warning("⚠️ State column not found in data. Showing top regions instead.")
            # Fallback: show top 20 regions as bar chart
            top_regions = map_df.nlargest(20, view_metric) if view_metric in map_df.columns else map_df.head(20)
            if len(top_regions) > 0:
                fig_bar = px.bar(
                    top_regions,
                    x=group_col,
                    y=view_metric,
                    title=f"Top 20 {group_col} by {view_metric} ({month_sel})",
                    color=view_metric,
                    color_continuous_scale="YlOrRd"
                )
                fig_bar.update_layout(xaxis_tickangle=-45, height=500)
                st.plotly_chart(fig_bar, width='stretch')
            st.info("💡 Tip: State-level heatmap requires 'state' column in your CSV files (enrolment, demographic, biometric).")
        
        # Aggregate data by state for cleaner visualization
        elif 'state' in panel_iso.columns:
            state_data = panel_iso[panel_iso['month'] == month_dt].groupby('state').agg({
                'total_all': 'sum',
                'total_enrol': 'sum',
                'total_demo': 'sum',
                'total_bio': 'sum'
            }).reset_index()
            
            # Add population and compute per-10k metrics
            if 'population' in panel_iso.columns:
                state_pop = panel_iso.groupby('state')['population'].sum().reset_index()
                state_data = state_data.merge(state_pop, on='state', how='left')
                state_data['population'] = state_data['population'].replace(0, np.nan)
                state_data['updates_per_10k'] = (state_data['total_all'] / state_data['population']) * 10000
                state_data['enrol_per_10k'] = (state_data['total_enrol'] / state_data['population']) * 10000
            
            # Merge summary metrics (SUII, risk, etc.)
            state_summary = summary.groupby('state' if 'state' in summary.columns else summary.index).agg({
                'avg_updates_per_10k': 'mean',
                'SUII_demo': 'mean',
                'biometric_risk_score': 'mean'
            }).reset_index() if 'state' in summary.columns or 'state' in str(summary.index) else pd.DataFrame()
            
            if not state_summary.empty and 'state' in state_summary.columns:
                state_data = state_data.merge(state_summary, on='state', how='left')
            
            # India state center coordinates
            state_coords = {
                'Andhra Pradesh': (15.9129, 79.7400), 'Arunachal Pradesh': (28.2180, 94.7278),
                'Assam': (26.2006, 92.9376), 'Bihar': (25.0961, 85.3131),
                'Chhattisgarh': (21.2787, 81.8661), 'Goa': (15.2993, 74.1240),
                'Gujarat': (22.2587, 71.1924), 'Haryana': (29.0588, 76.0856),
                'Himachal Pradesh': (31.1048, 77.1734), 'Jharkhand': (23.6102, 85.2799),
                'Karnataka': (15.3173, 75.7139), 'Kerala': (10.8505, 76.2711),
                'Madhya Pradesh': (22.9734, 78.6569), 'Maharashtra': (19.7515, 75.7139),
                'Manipur': (24.6637, 93.9063), 'Meghalaya': (25.4670, 91.3662),
                'Mizoram': (23.1645, 92.9376), 'Nagaland': (26.1584, 94.5624),
                'Odisha': (20.9517, 85.0985), 'Punjab': (31.1471, 75.3412),
                'Rajasthan': (27.0238, 74.2179), 'Sikkim': (27.5330, 88.5122),
                'Tamil Nadu': (11.1271, 78.6569), 'Telangana': (18.1124, 79.0193),
                'Tripura': (23.9408, 91.9882), 'Uttar Pradesh': (26.8467, 80.9462),
                'Uttarakhand': (30.0668, 79.0193), 'West Bengal': (22.9868, 87.8550),
                'Andaman and Nicobar Islands': (11.7401, 92.6586), 'Chandigarh': (30.7333, 76.7794),
                'Dadra and Nagar Haveli and Daman and Diu': (20.1809, 73.0169),
                'Delhi': (28.7041, 77.1025), 'Jammu and Kashmir': (33.7782, 76.5762),
                'Ladakh': (34.1526, 77.5771), 'Lakshadweep': (10.5667, 72.6417),
                'Puducherry': (11.9416, 79.8083)
            }
            
            # Add coordinates
            state_data['lat'] = state_data['state'].map(lambda x: state_coords.get(x, (None, None))[0])
            state_data['lon'] = state_data['state'].map(lambda x: state_coords.get(x, (None, None))[1])
            state_data = state_data.dropna(subset=['lat', 'lon'])

            # Fallback if metric is missing or mostly NaN
            if view_metric not in state_data.columns or state_data[view_metric].count() <= 1:
                fallback_metric = 'total_all'
                st.info(f"Using '{fallback_metric}' for heatmap because '{view_metric}' is missing/mostly empty.")
                view_metric = fallback_metric
                if fallback_metric not in state_data.columns:
                    state_data[fallback_metric] = state_data['total_all']
            
            if len(state_data) > 0 and view_metric in state_data.columns:
                # Clean NaNs/Infs to keep scatter marker sizes valid for Plotly
                state_data[view_metric] = pd.to_numeric(state_data[view_metric], errors='coerce').replace([np.inf, -np.inf], np.nan)
                # Drop rows with invalid or non-positive sizes
                state_data = state_data.dropna(subset=[view_metric])
                state_data = state_data[state_data[view_metric] > 0]
                if state_data.empty:
                    st.warning(f"No non-null values for {view_metric} to plot on heatmap.")
                else:
                    # Create scatter geo map
                    fig_heat = px.scatter_geo(
                        state_data,
                        lat='lat',
                        lon='lon',
                        size=view_metric,
                        color=view_metric,
                        hover_name='state',
                        hover_data={
                            'lat': False,
                            'lon': False,
                            view_metric: ':,.1f',
                            'total_all': ':,.0f'
                        },
                        color_continuous_scale="YlOrRd",
                        size_max=50
                    )
                    
                    fig_heat.update_geos(
                        scope='asia',
                        center=dict(lat=22.0, lon=80.0),
                        projection_scale=4,
                        showcountries=True,
                        showsubunits=True,
                        showland=True,
                        landcolor="rgb(243, 243, 243)",
                        coastlinecolor="rgb(204, 204, 204)",
                        countrycolor="rgb(204, 204, 204)",
                    )
                    
                    fig_heat.update_layout(height=600, margin={"r":0,"t":50,"l":0,"b":0})
                    st.plotly_chart(fig_heat, width='stretch')
            else:
                st.warning(f"Cannot create heatmap: metric '{view_metric}' not available in state data")
    
    # -----------------------
    # CHOROPLETH VIEW (Pincode-level with GeoJSON)
    # -----------------------
    elif map_type == "Choropleth (Pincode)":
        if geojson is None:
            st.warning("⚠️ GeoJSON file (All_India_pincode.geojson) not found. Switch to Heatmap view or download GeoJSON from data.gov.in.")
        else:
            st.subheader("📍 Pincode Choropleth Map")
            
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
            if group_col == 'pincode':
                map_df['pincode_str'] = map_df['pincode'].apply(lambda x: str(x).zfill(6))
                geo_featureid = f"properties.{prop_key}"
                
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
                st.plotly_chart(fig, width='stretch')
            else:
                # district/state view: fallback to bar chart
                st.info("Geo-visualization for district/state aggregation not supported with pincode GeoJSON. See ranking table below.")
                topn = map_df.sort_values('avg_updates_per_10k', ascending=False).head(20)
                bar = px.bar(topn, x=group_col, y='avg_updates_per_10k', title=f"Top 20 {group_col} by avg updates per 10k")
                st.plotly_chart(bar, width='stretch')

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
        st.plotly_chart(fig_ts, width='stretch')
    else:
        st.write("No time series data for selected region.")

with col2:
    st.subheader("Population vs Updates (scatter)")
    if 'population' in panel.columns and panel['population'].sum() > 0:
        latest_month = panel_iso['month'].max()
        scatter_df = panel_iso[panel_iso['month']==latest_month].dropna(subset=['population'])
        scatter_df['updates_per_10k'] = (scatter_df['total_all'] / scatter_df['population']) * 10000
        scatter_df = scatter_df.dropna(subset=['population','updates_per_10k'])
        fig_sc = px.scatter(scatter_df, x='population', y='updates_per_10k', size='total_all',
                            hover_data=[group_col,'total_all','population'], title="Population vs Updates per 10k (latest month)")
        st.plotly_chart(fig_sc, width='stretch')
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
