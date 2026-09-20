import pandas as pd
import plotly.express as px
import plotly.io as pio
import json
import numpy as np
import os
import sys

# Set Plotly to render HTML
pio.templates.default = "plotly_white"

# ==========================================
# 1. CSS & STYLING (Single Page App Optimized)
# ==========================================
CSS_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary: #6366f1;
        --secondary: #8b5cf6;
        --bg-color: #f8fafc;
        --card-bg: #ffffff;
        --text-color: #1e293b;
        --text-muted: #64748b;
        --sidebar-width: 280px;
        --border-color: #e2e8f0;
    }
    
    * { box-sizing: border-box; }

    body {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: var(--bg-color);
        margin: 0; padding: 0;
        color: var(--text-color);
        -webkit-font-smoothing: antialiased;
        overflow-x: hidden;
    }
    
    .container { display: flex; min-height: 100vh; width: 100%; }
    
    /* Sidebar Section */
    .sidebar {
        width: var(--sidebar-width);
        background-color: var(--card-bg);
        border-right: 1px solid var(--border-color);
        padding: 2rem 1.5rem;
        flex-shrink: 0;
        height: 100vh;
        position: fixed; left: 0; top: 0;
        overflow-y: auto;
        z-index: 100;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }
    
    .main-content {
        margin-left: var(--sidebar-width);
        flex: 1;
        padding: 2.5rem 3rem;
        max-width: calc(100% - var(--sidebar-width));
        background: var(--bg-color);
        animation: fadeIn 0.5s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Interactive Elements */
    .state-selector {
        width: 100%; padding: 0.875rem;
        border: 2px solid #e2e8f0; border-radius: 8px;
        font-size: 1rem; color: #1e293b; font-weight: 500;
        background: white; margin-bottom: 2rem;
        cursor: pointer; outline: none; transition: all 0.2s;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236B7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
        background-repeat: no-repeat; background-position: right 1rem center; background-size: 1.25em;
        appearance: none; -webkit-appearance: none;
    }
    .state-selector:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1); }
    
    /* Typography */
    .main-header {
        font-size: 2rem; font-weight: 800; letter-spacing: -0.025em;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header { font-size: 1rem; color: var(--text-muted); font-weight: 500; margin-bottom: 2rem; }

    h3 {
        font-weight: 700; font-size: 1.25rem; color: #0f172a;
        margin: 2.5rem 0 1.25rem 0; display: flex; align-items: center; gap: 0.5rem;
    }

    /* Grid Layouts */
    .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .grid-2-1 { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; margin-bottom: 2rem; align-items: start; }
    
    /* Metrics Cards */
    .metric-box {
        background: var(--card-bg); border: 1px solid var(--border-color);
        padding: 1.5rem; border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .metric-box:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .metric-icon { font-size: 1.75rem; margin-bottom: 0.75rem; }
    .metric-label { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; margin: 0.25rem 0; letter-spacing: -0.02em; }
    .metric-change { font-size: 0.875rem; font-weight: 600; display: flex; align-items: center; gap: 0.25rem; }
    
    /* Info Cards */
    .insight-card, .risk-card { padding: 1.5rem; border-radius: 12px; font-size: 0.925rem; line-height: 1.6; }
    .insight-card { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
    .risk-card { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
    
    /* Sidebar Widgets */
    .sidebar-metric { background: #f1f5f9; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; }
    .sidebar-metric-label { font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
    .sidebar-metric-value { font-size: 1.125rem; font-weight: 700; color: #334155; margin-top: 0.25rem; }
    .section-divider { border-top: 1px solid var(--border-color); margin: 1.5rem 0; }
    .sidebar-heading { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin: 0 0 1rem 0; }

    /* Utilities */
    .plotly-graph-div { 
        background: var(--card-bg); border-radius: 12px; padding: 1rem; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid var(--border-color); 
        width: 100%; overflow: hidden; 
    }
    .loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255,255,255,0.95); z-index: 2000;
        display: flex; justify-content: center; align-items: center;
        flex-direction: column; transition: opacity 0.5s;
    }
    .hidden { display: none !important; }
    
    /* Responsive */
    @media (max-width: 1024px) {
        .grid-2-1 { grid-template-columns: 1fr; }
        .sidebar { width: 240px; }
        .main-content { margin-left: 240px; max-width: calc(100% - 240px); }
    }
    @media (max-width: 768px) {
        .container { flex-direction: column; }
        .sidebar { width: 100%; height: auto; position: relative; border-right: none; border-bottom: 1px solid var(--border-color); }
        .main-content { margin-left: 0; max-width: 100%; padding: 1.5rem; }
        .state-selector { position: static; }
    }
</style>
"""

# ==========================================
# 2. DATA LOAD & PROCESS FUNCTIONS
# ==========================================
def load_geojson_centroids():
    print("Loading GeoJSON for map coordinates...", flush=True)
    coords_map = {}
    try:
        with open('data/raw/All_India_pincode.geojson', 'r') as f:
            data = json.load(f)
            
        print(f"Parsing {len(data['features'])} geo-features...", flush=True)
        for f in data['features']:
            try:
                pincode = str(f['properties']['Pincode'])
                # Normalize Pincode (remove .0 and whitespace)
                if pincode.endswith('.0'): pincode = pincode[:-2]
                pincode = pincode.strip()

                geom = f['geometry']
                
                # Simple Centroid Calculation
                lats, lons = [], []
                
                def extract_points(coords_list):
                    for item in coords_list:
                        if isinstance(item[0], (int, float)):
                            lons.append(item[0])
                            lats.append(item[1])
                        else:
                            extract_points(item)

                extract_points(geom['coordinates'])
                
                if lats and lons:
                    coords_map[pincode] = {
                        'lat': sum(lats) / len(lats),
                        'lon': sum(lons) / len(lons)
                    }
            except:
                continue
                
        print(f"Mapped coordinates for {len(coords_map)} pincodes.", flush=True)
        return coords_map
    except Exception as e:
        print(f"GeoJSON Error: {e}")
        return {}

def load_and_merge_data_once():
    """Load all data at once to memory"""
    try:
        print("Loading full datasets...", flush=True)
        # Use dtype optimization to save memory
        df_enrol = pd.read_csv('data/raw/combined enrolment.csv', parse_dates=['date'], dayfirst=True)
        df_bio = pd.read_csv('data/raw/combined biometrics.csv', parse_dates=['date'], dayfirst=True)
        df_demo = pd.read_csv('data/raw/combined demographic.csv', parse_dates=['date'], dayfirst=True)
        
        df_pop = pd.read_csv('data/raw/population.csv')
        # Normalize headers
        if 'pincode' not in df_pop.columns and len(df_pop.columns) >= 3:
            df_pop.rename(columns={df_pop.columns[1]: 'pincode', df_pop.columns[2]: 'population'}, inplace=True)
        
        # LOAD GEOJSON ONCE
        print("Loading GeoJSON...", flush=True)
        geojson = None
        try:
            with open('data/raw/All_India_pincode.geojson', 'r') as f:
                geojson = json.load(f)
            print(f"Loaded GeoJSON with {len(geojson['features'])} features", flush=True)
        except Exception as e:
            print(f"GeoJSON load failed: {e}", flush=True)
        
        # LOAD COORDINATES
        geo_coords = load_geojson_centroids()
        
        print("Calculating National Stats...", flush=True)
        nat_stats = {
            'states': df_enrol['state'].nunique(),
            'total_enrolment': (df_enrol['age_0_5'].sum() + df_enrol['age_5_17'].sum() + df_enrol['age_18_greater'].sum()),
            'total_transactions': len(df_enrol) + len(df_bio) + len(df_demo)
        }
        
        # Merge key fields
        print("Optimizing dataframes...", flush=True)
        for df in [df_bio, df_demo, df_enrol, df_pop]:
            if 'pincode' in df.columns: 
                df['pincode'] = df['pincode'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        # We return the separate frames to join per state on demand (saves memory vs big outer join)
        return {
            "bio": df_bio, "demo": df_demo, "enrol": df_enrol, "pop": df_pop, "coords": geo_coords, "geojson": geojson
        }, nat_stats

    except Exception as e:
        print(f"ERROR LOAD: {e}")
        return None, None

def get_state_metrics(state_name, datasets, geojson_data):
    """Calculate metrics for a specific state on the fly"""
    print(f"Processing {state_name}...", end=" ", flush=True)
    
    # Filter only relevant rows
    d_bio = datasets['bio'][datasets['bio']['state'] == state_name]
    d_demo = datasets['demo'][datasets['demo']['state'] == state_name]
    d_enrol = datasets['enrol'][datasets['enrol']['state'] == state_name]
    
    if d_enrol.empty: return None

    # Merge for this state
    merge_keys = ['date', 'district', 'pincode']
    # Note: 'state' is constant, removed from keys to avoid warnings if category mismatch
    
    # Consolidate
    df_state = pd.merge(d_enrol, d_bio, on=merge_keys, how='outer', suffixes=('', '_bio'))
    df_state = pd.merge(df_state, d_demo, on=merge_keys, how='outer', suffixes=('', '_demo'))
    
    # Fill N/As - Target only numeric columns to avoid crashes/warnings
    num_cols = df_state.select_dtypes(include=['float64', 'int64']).columns
    df_state[num_cols] = df_state[num_cols].fillna(0)
    
    # Metrics
    # Fix column names logic (handle potential suffix issues or missing cols)
    # Using standard names from previous scripts: 'bio_age_5_17', 'demo_age_5_17', 'age_0_5'
    cols = df_state.columns
    
    # Safe getters
    def get_sum(col): return df_state[col].sum() if col in cols else 0
    
    total_enrolment = get_sum('age_0_5') + get_sum('age_5_17') + get_sum('age_18_greater')
    bio_updates = get_sum('bio_age_5_17')
    demo_updates = get_sum('demo_age_17_') # check if it exists or 'demo_age_17_' from merge
    
    # District Summary - safe aggregation
    agg_dict = {}
    for col in ['age_0_5', 'age_5_17', 'age_18_greater', 'bio_age_5_17', 'demo_age_5_17']:
        if col in cols:
            agg_dict[col] = 'sum'
    
    if not agg_dict:
        # If no columns exist, return empty result
        return None
    
    dist_group = df_state.groupby('district').agg(agg_dict).reset_index()
    
    # Create total_enrolment safely
    dist_group['total_enrolment'] = 0
    for col in ['age_0_5', 'age_5_17', 'age_18_greater']:
        if col in dist_group.columns:
            dist_group['total_enrolment'] += dist_group[col]
    
    # Population Calc
    pincodes_in_state = df_state['pincode'].unique()
    state_pop_df = datasets['pop'][datasets['pop']['pincode'].isin(pincodes_in_state)]
    
    # Map pop to district via pincode (approx)
    # create map from enrolment data
    pin_dist_map = df_state[['pincode', 'district']].drop_duplicates().set_index('pincode')['district'].to_dict()
    state_pop_df['district'] = state_pop_df['pincode'].map(pin_dist_map)
    dist_pop = state_pop_df.groupby('district')['population'].sum().reset_index()
    
    # Merge Pop
    final = pd.merge(dist_group, dist_pop, on='district', how='left')
    final.fillna(1, inplace=True) # avoid div by zero, pop 0 -> 1
    final['saturation'] = (final['total_enrolment'] / final['population']) * 100
    
    # Final aggregations
    compliance_rate = (bio_updates / (demo_updates + 1)) * 100
    risk_dists = final[final['bio_age_5_17'] < final['demo_age_5_17']].shape[0]
    
    high_cov_count = final[final['saturation'] >= 80].shape[0]
    total_dists = len(final)
    cov_pct = (high_cov_count / total_dists * 100) if total_dists else 0
    
    # Charts
    # 1. Saturation
    fig_sat = px.bar(
        final.sort_values('saturation', ascending=False).head(10),
        x='district', y='saturation',
        color='saturation', 
        color_continuous_scale=[[0, '#dbeafe'], [1, '#1e3a8a']]
    )
    fig_sat.update_layout(plot_bgcolor='white', margin=dict(t=20,b=20,l=20,r=20), height=300, font=dict(family='Plus Jakarta Sans'))
    json_sat = fig_sat.to_json()

    # 2. Compliance
    fig_comp = px.bar(
        final.sort_values('bio_age_5_17', ascending=True).head(10),
        x='district', y=['demo_age_5_17', 'bio_age_5_17'], barmode='group',
        color_discrete_map={'demo_age_5_17': '#f97316', 'bio_age_5_17': '#22c55e'}
    )
    fig_comp.update_layout(plot_bgcolor='white', margin=dict(t=20,b=20,l=20,r=20), height=300, showlegend=True, legend=dict(orientation="h", y=1.1), font=dict(family='Plus Jakarta Sans'))
    json_comp = fig_comp.to_json()

    # 3. Trends
    daily = df_state.groupby('date')[['age_0_5', 'demo_age_17_']].sum().reset_index()
    fig_tr = px.area(daily, x='date', y=['age_0_5', 'demo_age_17_'], color_discrete_map={'age_0_5': '#7c3aed', 'demo_age_17_': '#2563eb'})
    fig_tr.update_layout(plot_bgcolor='white', margin=dict(t=20,b=20,l=20,r=20), height=350, showlegend=True, legend=dict(orientation="h", y=1.1), font=dict(family='Plus Jakarta Sans'))
    json_tr = fig_tr.to_json()
    
    # 4. Map (Choropleth with Blue Gradient)
    json_map = "{}"
    try:
        # Get active pincodes in this state
        active_pincodes = df_state['pincode'].unique().tolist()
        
        # Filter GeoJSON features to only active pincodes
        if geojson_data:
            filtered_features = [f for f in geojson_data['features'] if str(f['properties']['Pincode']).strip() in [str(p).strip() for p in active_pincodes]]
            
            if filtered_features:
                filtered_geojson = {'type': 'FeatureCollection', 'features': filtered_features}
                
                # Aggregate map data by pincode
                map_df = df_state.groupby('pincode').agg({
                    'total_enrolment': 'sum',
                    'age_0_5': 'sum',
                    'age_5_17': 'sum',
                    'age_18_greater': 'sum',
                    'district': 'first'
                }).reset_index()
                
                map_df['pincode'] = map_df['pincode'].astype(str)
                
                # Custom blue color scale (light to dark blue)
                custom_colorscale = [
                    [0.0, '#e0f2fe'],
                    [0.15, '#7dd3fc'],
                    [0.3, '#38bdf8'],
                    [0.45, '#0ea5e9'],
                    [0.6, '#0284c7'],
                    [0.75, '#0369a1'],
                    [0.9, '#075985'],
                    [1.0, '#0c4a6e']
                ]
                
                # Create choropleth map
                fig_map = px.choropleth_mapbox(
                    map_df,
                    geojson=filtered_geojson,
                    locations='pincode',
                    featureidkey="properties.Pincode",
                    color='total_enrolment',
                    color_continuous_scale=custom_colorscale,
                    mapbox_style="carto-positron",
                    zoom=5,
                    opacity=0.75,
                    hover_data={'pincode': True, 'district': True, 'total_enrolment': ':,.0f', 'age_0_5': ':,.0f', 'age_5_17': ':,.0f', 'age_18_greater': ':,.0f'},
                    labels={
                        'total_enrolment': 'Total Enrollments',
                        'pincode': 'Pincode',
                        'district': 'District',
                        'age_0_5': 'Children (0-5)',
                        'age_5_17': 'Youth (5-17)',
                        'age_18_greater': 'Adults (18+)'
                    }
                )
                
                fig_map.update_layout(
                    margin={"r":0,"t":0,"l":0,"b":0},
                    height=400,
                    font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#1f2937", size=11),
                    paper_bgcolor='#ffffff',
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        font_family="Plus Jakarta Sans, Inter",
                        bordercolor="#0284c7",
                        font_color="#1f2937"
                    ),
                    coloraxis_colorbar=dict(
                        title=dict(text="Enrollments", font=dict(size=11, color="#374151")),
                        tickfont=dict(size=10, color="#4b5563"),
                        thickness=12,
                        len=0.6,
                        bgcolor="rgba(255,255,255,0.95)",
                        bordercolor="#e5e7eb",
                        borderwidth=1
                    )
                )
                
                # Add border/outline to polygons
                fig_map.update_traces(
                    marker_line_width=0.5,
                    marker_line_color='#0284c7'
                )
                
                json_map = fig_map.to_json()
                print(f" [Map: {len(filtered_features)} pincodes rendered]", end="", flush=True)
    except Exception as e:
        print(f" [Map Error: {e}]", end="", flush=True)

    return {
        "metrics": {
            "districts": total_dists,
            "pincodes": len(pincodes_in_state),
            "population": f"{final['population'].sum():,.0f}",
            "enrolment": f"{total_enrolment:,.0f}",
            "saturation": f"{final['saturation'].mean():.1f}%",
            "risk_areas": risk_dists,
            "compliance": f"{compliance_rate:.1f}%",
            "comp_color": "#10b981" if compliance_rate > 80 else "#ef4444",
            "coverage_text": f"{high_cov_count}/{total_dists}",
            "coverage_sub": f"{cov_pct:.0f}%",
            "coverage_color": "#10b981" if cov_pct > 70 else "#f59e0b"
        },
        "charts": {
            "saturation": json_sat,
            "compliance": json_comp,
            "trends": json_tr,
            "map": json_map
        }
    }


# ==========================================
# 3. GENERATION
# ==========================================
def generate_single_file_app():
    datasets, nat_stats = load_and_merge_data_once()
    if not datasets: return
    
    # Load GeoJSON once
    print("Loading GeoJSON data...", flush=True)
    geojson_data = None
    try:
        with open('data/raw/All_India_pincode.geojson', 'r') as f:
            geojson_data = json.load(f)
        print(f"GeoJSON loaded with {len(geojson_data['features'])} features.", flush=True)
    except Exception as e:
        print(f"GeoJSON load error: {e}", flush=True)
    
    all_states = sorted(datasets['enrol']['state'].dropna().unique())
    print(f"Stats: {len(all_states)} states found.")
    
    master_data = {}
    
    for state in all_states:
        try:
            res = get_state_metrics(state, datasets, geojson_data)
            if res:
                master_data[state] = res
                print("✓")
        except Exception as e:
            print(f"X ({e})")

    # JSON Serialize
    print("Serializing data for web...", flush=True)
    json_payload = json.dumps(master_data, default=str)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UIDAI National Dashboard 2026</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    {CSS_STYLES}
</head>
<body>
    <div id="loader" class="loading-overlay">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🇮🇳</div>
        <div style="font-weight: 700; color: #1e293b; font-size: 1.25rem;">Building Experience...</div>
        <div style="color: #64748b; margin-top: 5px;">Loading {len(all_states)} Regions</div>
    </div>

    <div class="container">
        <!-- SIDEBAR -->
        <aside class="sidebar">
            <h2 class="main-header" style="font-size: 1.5rem;">UIDAI <span style="font-weight:300; font-size: 1rem; color: #6366f1;">Insight</span></h2>
            
            <div style="margin-top: 2rem;">
                <label style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Select Region</label>
                <select id="stateSelect" class="state-selector">
                    <option value="" disabled selected>Choose State...</option>
                </select>
            </div>

            <div class="section-divider"></div>

            <h3 class="sidebar-heading">National Context</h3>
            <div class="sidebar-metric">
                <div class="sidebar-metric-label">Total Enrollment</div>
                <div class="sidebar-metric-value">{nat_stats['total_enrolment']:,.0f}</div>
            </div>
            <div class="sidebar-metric">
                <div class="sidebar-metric-label">States Active</div>
                <div class="sidebar-metric-value">{len(all_states)}</div>
            </div>
            
            <div id="stateContext" class="hidden">
                <div class="section-divider"></div>
                <h3 class="sidebar-heading">Regional Context</h3>
                <div class="sidebar-metric">
                    <div class="sidebar-metric-label">Districts</div>
                    <div class="sidebar-metric-value" id="sb_dist">-</div>
                </div>
                <div class="sidebar-metric">
                    <div class="sidebar-metric-label">Population (Est)</div>
                    <div class="sidebar-metric-value" id="sb_pop">-</div>
                </div>
                 <div class="sidebar-metric">
                    <div class="sidebar-metric-label">Pincodes</div>
                    <div class="sidebar-metric-value" id="sb_pin">-</div>
                </div>
            </div>
            
            <div style="margin-top: auto; padding-top: 2rem; color: #94a3b8; font-size: 0.75rem;">
                v3.0.1 Single-File Build<br>All Data Local
            </div>
        </aside>

        <!-- MAIN -->
        <main class="main-content">
            <div id="welcomeScreen" style="text-align: center; margin-top: 10vh;">
                <div style="font-size: 4rem; margin-bottom: 2rem;">🗺️</div>
                <h1 style="color: #1e293b; font-size: 2.5rem; margin-bottom: 1rem;">Welcome to the Dashboard</h1>
                <p style="color: #64748b; font-size: 1.25rem; max-width: 600px; margin: 0 auto;">
                    Select a state from the sidebar dropdown to visualize real-time enrollment, demographic trends, and compliance metrics.
                </p>
            </div>

            <div id="dashboard" class="hidden">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 2rem;">
                    <div>
                        <div class="main-header" id="dashTitle">State Overview</div>
                        <div class="sub-header">Strategic Performance & Compliance Report</div>
                    </div>
                    <div style="text-align: right;">
                         <div style="background: #eff6ff; color: #1e40af; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">
                            Live Data
                        </div>
                    </div>
                </div>

                <!-- METRICS -->
                <h3>Performance Snapshot</h3>
                <div class="grid-4">
                    <div class="metric-box">
                        <span class="metric-icon">👥</span>
                        <div class="metric-label">Total Enrollment</div>
                        <div class="metric-value" id="m_enrol">-</div>
                    </div>
                    <div class="metric-box">
                        <span class="metric-icon">📊</span>
                        <div class="metric-label">Avg Saturation</div>
                        <div class="metric-value" id="m_sat">-</div>
                    </div>
                    <div class="metric-box" id="card_cov">
                        <span class="metric-icon">🎯</span>
                        <div class="metric-label">Target Districts</div>
                        <div class="metric-value" id="m_cov">-</div>
                        <div class="metric-change" id="m_cov_sub">-</div>
                    </div>
                    <div class="metric-box" id="card_comp">
                        <span class="metric-icon">✅</span>
                        <div class="metric-label">Compliance Rate</div>
                        <div class="metric-value" id="m_comp">-</div>
                        <div class="metric-change" style="color: #64748b">Bio vs Demo</div>
                    </div>
                </div>

                <!-- MAP -->
                <div id="map_section" class="hidden">
                    <h3>Geospatial Distribution</h3>
                    <div id="chart_map" class="plotly-graph-div" style="height: 450px; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 2rem;"></div>
                </div>
                
                <!-- CHARTS 1 -->
                <h3>Biometric Saturation & Gaps</h3>
                <div class="grid-2-1">
                    <div id="chart_sat" class="plotly-graph-div"></div>
                    <div class="insight-card">
                        <b>Saturation Insights</b><br><br>
                        Top performing districts shown. Low saturation areas (<80%) require immediate mobile camp deployment.<br><br>
                        <span style="font-size: 0.8rem; color: #64748b;">*Values >100% may indicate migration or duplicity.</span>
                    </div>
                </div>

                <!-- CHARTS 2 -->
                <h3>Process Compliance (5-17 Years)</h3>
                <div class="grid-2-1">
                    <div id="chart_comp" class="plotly-graph-div"></div>
                     <div class="risk-card">
                        <b>Risk Analysis</b><br><br>
                        Districts with high demographic updates (Orange) but low biometric updates (Green) indicate process deviation.<br><br>
                        <b>Action:</b> Audit operators in these zones.
                    </div>
                </div>
                
                <!-- CHARTS 3 -->
                <h3>Trend Analysis</h3>
                <div id="chart_tr" class="plotly-graph-div"></div>
            </div>
        </main>
    </div>

    <script>
        // RAW DATA INJECTION
        const DB = {json_payload};
        const SELECT = document.getElementById('stateSelect');
        
        // 1. Populate Dropdown
        const states = Object.keys(DB).sort();
        states.forEach(s => {{
            const opt = document.createElement('option');
            opt.value = s;
            opt.textContent = s;
            SELECT.appendChild(opt);
        }});

        // 2. Remove Loader
        window.addEventListener('load', () => {{
            setTimeout(() => {{
                document.getElementById('loader').style.opacity = '0';
                setTimeout(() => document.getElementById('loader').classList.add('hidden'), 500);
            }}, 800);
        }});

        // 3. Logic
        SELECT.addEventListener('change', (e) => loadState(e.target.value));

        function loadState(name) {{
            if(!DB[name]) return;
            const d = DB[name];
            const m = d.metrics;
            const c = d.charts;

            // Visibility
            document.getElementById('welcomeScreen').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');
            document.getElementById('stateContext').classList.remove('hidden');

            // Header
            document.getElementById('dashTitle').innerText = name;
            
            // Sidebar
            document.getElementById('sb_dist').innerText = m.districts;
            document.getElementById('sb_pop').innerText = m.population;
            document.getElementById('sb_pin').innerText = m.pincodes;

            // KPI
            document.getElementById('m_enrol').innerText = m.enrolment;
            document.getElementById('m_sat').innerText = m.saturation;
            
            // Coverage Card
            document.getElementById('m_cov').innerText = m.coverage_text;
            document.getElementById('m_cov_sub').innerText = m.coverage_sub + " Meeting Target";
            document.getElementById('m_cov_sub').style.color = m.coverage_color;
            document.getElementById('card_cov').style.borderTop = "3px solid " + m.coverage_color;
            
            // Compliance Card
            document.getElementById('m_comp').innerText = m.compliance;
            document.getElementById('card_comp').style.borderTop = "3px solid " + m.comp_color;

            // Chart Render - using Plotly.react for updates
            const config = {{responsive: true, displayModeBar: false}};
            
            Plotly.newPlot('chart_sat', JSON.parse(c.saturation).data, JSON.parse(c.saturation).layout, config);
            Plotly.newPlot('chart_comp', JSON.parse(c.compliance).data, JSON.parse(c.compliance).layout, config);
            Plotly.newPlot('chart_tr', JSON.parse(c.trends).data, JSON.parse(c.trends).layout, config);

            // Map Handling
            if(c.map && c.map.length > 5) {{
                document.getElementById('map_section').classList.remove('hidden');
                Plotly.newPlot('chart_map', JSON.parse(c.map).data, JSON.parse(c.map).layout, config);
            }} else {{
                document.getElementById('map_section').classList.add('hidden');
            }}
        }}
    </script>
</body>
</html>
    """
    
    with open("outputs/static_site/app_dashboard.html", "w", encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: 'outputs/static_site/app_dashboard.html' generated successfully.")

if __name__ == "__main__":
    generate_single_file_app()
