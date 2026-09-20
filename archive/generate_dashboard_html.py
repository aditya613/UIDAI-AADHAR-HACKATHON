import pandas as pd
import plotly.express as px
import plotly.io as pio
import json
import numpy as np
import os

# Set Plotly to render HTML
pio.templates.default = "plotly_white"

# ==========================================
# 1. CSS & STYLING (Copied from test4.py)
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
    
    * {
        box-sizing: border-box;
    }

    body {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: var(--bg-color);
        margin: 0;
        padding: 0;
        color: var(--text-color);
        -webkit-font-smoothing: antialiased;
    }
    
    .container {
        display: flex;
        min-height: 100vh;
        width: 100%;
    }
    
    /* Sidebar Section */
    .sidebar {
        width: var(--sidebar-width);
        background-color: var(--card-bg);
        border-right: 1px solid var(--border-color);
        padding: 2rem 1.5rem;
        flex-shrink: 0;
        height: 100vh;
        position: fixed;
        left: 0;
        top: 0;
        overflow-y: auto;
        z-index: 10;
    }
    
    .main-content {
        margin-left: var(--sidebar-width);
        flex: 1;
        padding: 2.5rem 3rem;
        max-width: calc(100% - var(--sidebar-width));
        background: var(--bg-color);
    }
    
    /* Typography */
    .main-header {
        font-size: 2rem; 
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1rem; 
        color: var(--text-muted); 
        font-weight: 500;
        margin-bottom: 2rem;
    }

    h3 {
        font-weight: 700;
        font-size: 1.25rem;
        color: #0f172a;
        margin: 2.5rem 0 1.25rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Grids */
    .grid-4 {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .grid-2-1 {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 1.5rem;
        margin-bottom: 2rem;
        align-items: start;
    }
    
    /* Cards */
    .metric-box {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }

    .metric-icon { font-size: 1.75rem; margin-bottom: 0.75rem; }
    .metric-label { font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; margin: 0.25rem 0; }
    .metric-change { font-size: 0.875rem; font-weight: 600; display: flex; align-items: center; gap: 0.25rem; }
    
    /* Info Cards */
    .insight-card, .risk-card {
        padding: 1.5rem;
        border-radius: 12px;
        font-size: 0.925rem;
        line-height: 1.6;
    }
    .insight-card { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
    .risk-card { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
    
    /* Sidebar Widgets */
    .sidebar-metric {
        background: #f1f5f9;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.75rem;
    }
    .sidebar-metric-label { font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
    .sidebar-metric-value { font-size: 1.125rem; font-weight: 700; color: #334155; margin-top: 0.25rem; }
    
    .section-divider { border-top: 1px solid var(--border-color); margin: 1.5rem 0; }
    .sidebar-heading { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin: 0 0 1rem 0; }

    /* Plotly Containers */
    .plotly-graph-div {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid var(--border-color);
        /* Ensure charts don't overflow */
        width: 100%;
        overflow: hidden; 
    }

    /* Map Legend */
    .map-legend-card {
        padding: 1rem; 
        border-radius: 10px; 
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 100px;
    }

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
    }
</style>
"""

import sys

# ==========================================
# 2. DATA PROCESSING LOGIC
# ==========================================
def load_and_merge_data(target_state=None):
    try:
        print("Loading data...", flush=True)
        # Load only necessary columns if possible, but for simplicity read all
        df_bio = pd.read_csv('combined biometrics.csv', parse_dates=['date'], dayfirst=True)
        print("Loaded bio", flush=True)
        df_demo = pd.read_csv('combined demographic.csv', parse_dates=['date'], dayfirst=True)
        print("Loaded demo", flush=True)
        df_enrol = pd.read_csv('combined enrolment.csv', parse_dates=['date'], dayfirst=True)
        print("Loaded enrol", flush=True)
        
        df_pop = pd.read_csv('population.csv')
        if 'pincode' not in df_pop.columns:
            if len(df_pop.columns) >= 3:
                df_pop.rename(columns={df_pop.columns[1]: 'pincode', df_pop.columns[2]: 'population'}, inplace=True)
        
        # Calculate National Stats on full data before filtering
        national_stats = {
            'states': df_enrol['state'].nunique(),
            'districts': df_enrol['district'].nunique(),
            'pincodes': df_enrol['pincode'].nunique(),
            'total_enrolment': (df_enrol['age_0_5'].sum() + df_enrol['age_5_17'].sum() + df_enrol['age_18_greater'].sum()),
            # Note: bio/demo might not have all rows, use sum of respective cols
            'total_biometric': df_bio['bio_age_5_17'].sum() if 'bio_age_5_17' in df_bio.columns else 0,
            'total_demographic': df_demo['demo_age_17_'].sum() if 'demo_age_17_' in df_demo.columns else 0
        }
        print("Calculated National Stats", flush=True)

        if target_state:
            available_states = df_enrol['state'].unique()
            print(f"Available states: {available_states[:5]}...", flush=True)
            
            print(f"Filtering for {target_state}...", flush=True)
            df_bio = df_bio[df_bio['state'] == target_state]
            df_demo = df_demo[df_demo['state'] == target_state]
            df_enrol = df_enrol[df_enrol['state'] == target_state]
        
        # Normalize pincodes
        for df in [df_bio, df_demo, df_enrol, df_pop]:
            if 'pincode' in df.columns:
                df['pincode'] = df['pincode'].astype(str)

        print("Merging data...", flush=True)
        merge_keys = ['date', 'state', 'district', 'pincode']
        df_master = pd.merge(df_bio, df_demo, on=merge_keys, how='outer')
        print("Merged 1/2", flush=True)
        df_master = pd.merge(df_master, df_enrol, on=merge_keys, how='outer')
        print("Merged 2/2", flush=True)
        
        return df_master, df_pop, national_stats

    except Exception as e:
        print(f"Error loading data: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame(), {}

def load_geojson():
    try:
        print("Loading GeoJSON...")
        with open('All_India_pincode.geojson', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("GeoJSON not found")
        return None

def calculate_metrics(df, df_pop):
    print("Calculating metrics...")
    df.fillna(0, inplace=True)

    df['total_enrolment'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
    df['child_compliance_ratio'] = df['bio_age_5_17'] / (df['demo_age_5_17'] + 1)
    
    district_summary = df.groupby(['state', 'district']).agg({
        'total_enrolment': 'sum',
        'age_0_5': 'sum',
        'bio_age_5_17': 'sum',
        'demo_age_5_17': 'sum',
        'demo_age_17_': 'sum'
    }).reset_index()

    pincode_district_map = df[['pincode', 'district']].drop_duplicates()
    pop_with_dist = pd.merge(df_pop, pincode_district_map, on='pincode', how='inner')
    district_pop = pop_with_dist.groupby('district')['population'].sum().reset_index()
    
    final_summary = pd.merge(district_summary, district_pop, on='district', how='left')
    final_summary['saturation'] = (final_summary['total_enrolment'] / final_summary['population']) * 100
    
    return df, final_summary

# ==========================================
# 3. HTML GENERATION LOGIC
# ==========================================
def generate_html(selected_state):
    df_raw, df_pop, nat_stats = load_and_merge_data(selected_state)
    geojson = load_geojson()
    
    if df_raw.empty:
        print("No Data Available")
        return

    df_trans, df_dist_summary = calculate_metrics(df_raw, df_pop)

    # Filter for selected state (redundant if filtered in load, but safe)
    if selected_state not in df_trans['state'].unique() and not df_trans.empty:
        # If we filtered by state, it should be there. If not, maybe name mismatch
        print(f"State {selected_state} not found even after filtering. Found: {df_trans['state'].unique()}")
        # Check if empty
    
    state_trans = df_trans # Since we filtered already
    state_summary = df_dist_summary

    # --- Calculations for Side Bar ---
    # Use pre-calculated national stats
    total_national_enrolment = nat_stats.get('total_enrolment', 0)
    total_biometric = nat_stats.get('total_biometric', 0)
    total_demographic = nat_stats.get('total_demographic', 0)
    
    # National Counts
    nat_states_count = nat_stats.get('states', 0)
    nat_districts_count = nat_stats.get('districts', 0)
    nat_pincodes_count = nat_stats.get('pincodes', 0)

    state_districts_count = state_trans['district'].nunique()
    state_pincodes_count = state_trans['pincode'].nunique()
    state_total_pop = state_summary['population'].sum() if 'population' in state_summary.columns else 0

    # --- Calculations for KPIs ---
    total_ops = state_trans['total_enrolment'].sum() + state_trans['demo_age_17_'].sum()
    avg_saturation_val = state_summary['saturation'].dropna().mean()
    avg_saturation = 0 if np.isnan(avg_saturation_val) else avg_saturation_val
    risk_districts = state_summary[state_summary['bio_age_5_17'] < state_summary['demo_age_5_17']].shape[0]
    new_births = state_trans['age_0_5'].sum()

    total_youth = state_trans['age_5_17'].sum() if 'age_5_17' in state_trans.columns else 0
    total_adults = state_trans['age_18_greater'].sum() if 'age_18_greater' in state_trans.columns else 0
    bio_updates_val = state_trans['bio_age_5_17'].sum() if 'bio_age_5_17' in state_trans.columns else 0
    demo_updates_val = state_trans['demo_age_17_'].sum() if 'demo_age_17_' in state_trans.columns else 0
    compliance_rate = (bio_updates_val / (demo_updates_val + 1)) * 100
    
    high_coverage = state_summary[state_summary['saturation'] >= 80].shape[0] if 'saturation' in state_summary.columns else 0
    coverage_pct = (high_coverage / state_districts_count * 100) if state_districts_count > 0 else 0

    # --- Plot Generation ---
    
    # 1. Saturation Chart
    fig_sat = px.bar(
        state_summary.sort_values('saturation', ascending=False).head(10),
        x='district', y='saturation',
        title=f"Top 10 High-Coverage Districts in {selected_state}",
        color='saturation', 
        color_continuous_scale=[[0, '#dbeafe'], [0.4, '#93c5fd'], [0.7, '#3b82f6'], [1, '#1e3a8a']],
        labels={'saturation': 'Coverage %', 'district': 'District'}
    )
    fig_sat.add_hline(y=100, line_dash="dash", line_color="#000000", line_width=2,
                        annotation_text="100% Target", annotation_position="top right",
                        annotation_font=dict(size=11, color="#000000"))
    fig_sat.update_traces(marker=dict(line=dict(width=0)))
    fig_sat.update_layout(
        plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
        font=dict(family="Inter", color="#1f2937", size=12),
        margin=dict(t=55, b=45, l=55, r=35)
    )
    html_sat = fig_sat.to_html(full_html=False, include_plotlyjs='cdn')

    # 2. Compliance Chart
    fig_comp = px.bar(
        state_summary.sort_values('bio_age_5_17', ascending=True).head(10),
        x='district', 
        y=['demo_age_5_17', 'bio_age_5_17'],
        barmode='group',
        title="Priority Districts: Compliance Gap Analysis",
        color_discrete_map={'demo_age_5_17': '#f97316', 'bio_age_5_17': '#22c55e'},
        labels={'value': 'Updates Count', 'variable': 'Type', 'demo_age_5_17': 'Demographic', 'bio_age_5_17': 'Biometric'}
    )
    fig_comp.update_traces(marker=dict(line=dict(width=0)))
    fig_comp.update_layout(
        plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
        font=dict(family="Inter", color="#1f2937", size=12),
        legend=dict(orientation="h", y=1.02, x=1),
        margin=dict(t=55, b=45, l=55, r=35)
    )
    html_comp = fig_comp.to_html(full_html=False, include_plotlyjs=False) # Plotly JS already included

    # 3. Trends Chart
    daily_trend = state_trans.groupby('date')[['demo_age_17_', 'age_0_5']].sum().reset_index()
    fig_line = px.area(daily_trend, x='date', y=['demo_age_17_', 'age_0_5'], 
                       title="Activity Timeline: Updates & New Registrations",
                       labels={'value': 'Volume', 'variable': 'Category', 'demo_age_17_': 'Adult Updates', 'age_0_5': 'New Births'},
                       color_discrete_map={'demo_age_17_': '#2563eb', 'age_0_5': '#7c3aed'})
    fig_line.update_traces(line=dict(width=2.5), opacity=0.85)
    fig_line.update_layout(
        plot_bgcolor='#ffffff', paper_bgcolor='#ffffff',
        font=dict(family="Inter", color="#1f2937", size=12),
        legend=dict(orientation="h", y=1.02, x=1),
        margin=dict(t=55, b=45, l=55, r=35)
    )
    html_trends = fig_line.to_html(full_html=False, include_plotlyjs=False)

    # 4. Map
    html_map = "<div>No GeoJSON data available or empty map</div>"
    map_stats = {'max':0, 'mean':0, 'min':0, 'sum':0}
    
    if geojson:
        print("Generating Map...")
        active_pincodes = state_trans['pincode'].unique().tolist()
        filtered_features = [f for f in geojson['features'] if str(f['properties']['Pincode']) in active_pincodes]
        filtered_geojson = {'type': 'FeatureCollection', 'features': filtered_features}
        
        map_data = state_trans.groupby('pincode').agg({
            'total_enrolment': 'sum',
            'district': 'first'
        }).reset_index()

        map_stats['max'] = map_data['total_enrolment'].max()
        map_stats['mean'] = map_data['total_enrolment'].mean()
        map_stats['min'] = map_data['total_enrolment'].min()
        map_stats['sum'] = map_data['total_enrolment'].sum()

        state_centers = {
            'Maharashtra': {"lat": 19.7515, "lon": 75.7139, "zoom": 6},
            # Add others if needed
        }
        map_center = state_centers.get(selected_state, {"lat": 22.0, "lon": 78.0, "zoom": 5})

        if filtered_features:
            custom_colorscale = [[0.0, '#e0f2fe'], [1.0, '#0c4a6e']]
            fig_map = px.choropleth_mapbox(
                map_data,
                geojson=filtered_geojson,
                locations='pincode',
                featureidkey="properties.Pincode",
                color='total_enrolment',
                color_continuous_scale=custom_colorscale,
                mapbox_style="carto-positron",
                zoom=map_center.get('zoom', 6),
                center={"lat": map_center['lat'], "lon": map_center['lon']},
                opacity=0.75
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
            html_map = fig_map.to_html(full_html=False, include_plotlyjs=False)
    
    # --- Helper to create metric box ---
    def make_metric(icon, label, value, change, color="#6366f1", border_color=""):
        style = f"border-top: 3px solid {color};" if border_color else ""
        change_style = f"color:{color}" if border_color else ""
        return f"""
        <div class="metric-box" style="{style}">
            <span class="metric-icon">{icon}</span>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-change" style="{change_style}">{change}</div>
        </div>
        """

    # --- Helper sidebar metric ---
    def make_sidebar_metric(label, value):
        return f"""
        <div class="sidebar-metric">
            <div class="sidebar-metric-label">{label}</div>
            <div class="sidebar-metric-value">{value}</div>
        </div>
        """

    # --- Colors for compliance/coverage ---
    comp_color = "#10b981" if compliance_rate >= 80 else "#f59e0b" if compliance_rate >= 50 else "#ef4444"
    cov_color = "#10b981" if coverage_pct >= 70 else "#f59e0b" if coverage_pct >= 50 else "#ef4444"

    # --- ASSEMBLE HTML ---
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UIDAI Strategic Oversight Dashboard 2026</title>
    {CSS_STYLES}
</head>
<body>
    <div class="container">
        <!-- SIDEBAR -->
        <aside class="sidebar">
            <h2 style="font-size: 1.5rem; margin-bottom: 2rem;">Filters</h2>
            
            <h3 class="sidebar-heading">📍 Geographic Scope</h3>
            <div class="sidebar-metric">
                <div class="sidebar-metric-label">Selected State</div>
                <div class="sidebar-metric-value">{selected_state}</div>
            </div>

            <div class="section-divider"></div>

            <h3 class="sidebar-heading">📊 National Overview</h3>
            {make_sidebar_metric("Total States", nat_states_count)}
            {make_sidebar_metric("Total Districts", nat_districts_count)}
            {make_sidebar_metric("Active Pincodes", nat_pincodes_count)}
            
            <div class="section-divider"></div>
            <h3 class="sidebar-heading">📈 National Metrics</h3>
            {make_sidebar_metric("Total Enrollments", f"{total_national_enrolment:,.0f}")}
            {make_sidebar_metric("Biometric Updates", f"{total_biometric:,.0f}")}
            {make_sidebar_metric("Demographic Updates", f"{total_demographic:,.0f}")}

             <div class="section-divider"></div>
            <h3 class="sidebar-heading">🏛️ {selected_state} Stats</h3>
            {make_sidebar_metric("State Districts", state_districts_count)}
            {make_sidebar_metric("State Pincodes", state_pincodes_count)}
            {make_sidebar_metric("Est. Population", f"{state_total_pop:,.0f}")}

        </aside>

        <!-- MAIN CONTENT -->
        <main class="main-content">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 2rem;">
                <div>
                    <div class="main-header">🇮🇳 UIDAI Strategic Oversight Dashboard</div>
                    <div class="sub-header">Data-Driven Governance · Real-Time Analytics · Compliance Monitoring</div>
                </div>
                <div style="text-align: right;">
                    <span style="color: #475569; font-size: 0.9rem;">Last Updated</span><br>
                    <span style="color: #0b1324; font-weight: 700;">Jan 20, 2026</span>
                </div>
            </div>

            <!-- KPI ROW 1 -->
            <h3>🎯 Key Performance Indicators</h3>
            <div class="grid-4">
                {make_metric("📊", "Total Transactions", f"{total_ops:,.0f}", "↗ Active Operations")}
                {make_metric("📈", "Avg Saturation", f"{avg_saturation:.1f}%", "Population Coverage")}
                {make_metric("⚠️", "Risk Districts", f"{risk_districts}", "⚠ Needs Attention", "", "")}
                {make_metric("👶", "New Births (0-5)", f"{new_births:,.0f}", "Future Citizens")}
            </div>

            <!-- KPI ROW 2 -->
            <h3>📋 Detailed Analytics</h3>
            <div class="grid-4">
                {make_metric("🧑‍🎓", "Youth (5-17 years)", f"{total_youth:,.0f}", "School-Age Population", "#3b82f6", "true")}
                {make_metric("👨‍💼", "Adults (18+)", f"{total_adults:,.0f}", "Working Population", "#10b981", "true")}
                {make_metric("✅", "Compliance Rate", f"{compliance_rate:.1f}%", "Bio vs Demo Updates", comp_color, "true")}
                {make_metric("🎯", "Districts ≥80% Coverage", f"{high_coverage}/{state_districts_count}", f"{coverage_pct:.0f}% Meeting Target", cov_color, "true")}
            </div>

            <!-- CHARTS ROW 1 -->
            <h3>📊 Population Coverage Analysis</h3>
            <div class="grid-2-1">
                <div class="plotly-graph-div">{html_sat}</div>
                <div class="insight-card">
                    <b>What this means:</b><br>
                    • <b>> 100%:</b> Indicates duplicate registrations or high migration influx.<br>
                    • <b>< 80%:</b> Indicates exclusion zones where citizens lack scheme access.<br><br>
                    <b>Recommended Action:</b> Deploy mobile enrollment units to districts below 85% coverage.
                </div>
            </div>

            <!-- CHARTS ROW 2 -->
            <h3>🛡️ Child Welfare Compliance Monitor</h3>
            <div class="grid-2-1">
                <div class="plotly-graph-div">{html_comp}</div>
                <div class="risk-card">
                    <b>Critical Observation:</b><br>
                    • <b>Red > Blue:</b> Children updating demographic info but missing mandatory biometric updates (Age 5/15).<br><br>
                    <b>Root Cause Analysis:</b> Operators may be bypassing biometric capture to reduce processing time.<br><br>
                    <b>Immediate Action:</b> Conduct operator audits in flagged districts.
                </div>
            </div>

            <!-- TIME TRENDS -->
            <h3>📅 Temporal Operations Analytics</h3>
            <div class="plotly-graph-div" style="margin-bottom: 2rem;">{html_trends}</div>

            <!-- MAP SECTION -->
            <h3>🗺️ Geographic Intelligence: {selected_state}</h3>
            <div style="background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); padding: 16px 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #bfdbfe; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 600; color: #1e40af;">📍 Pincode-Level Enrollment Density Map</span>
                    <p style="color: #475569; margin: 4px 0 0 0; font-size: 0.9rem;">Interactive visualization showing Aadhaar enrollment distribution</p>
                </div>
            </div>
            
            <div class="plotly-graph-div" style="margin-bottom: 2rem;">{html_map}</div>

            <div class="grid-4">
                <div class="map-legend-card" style="background: #f0f9ff; border: 1px solid #bae6fd;">
                    <div style="color: #0369a1;" class="map-legend-label">Highest Enrollment</div>
                    <div style="color: #0c4a6e;" class="map-legend-value">{map_stats['max']:,.0f}</div>
                </div>
                <div class="map-legend-card" style="background: #f0fdf4; border: 1px solid #bbf7d0;">
                     <div style="color: #15803d;" class="map-legend-label">Avg per Pincode</div>
                    <div style="color: #14532d;" class="map-legend-value">{map_stats['mean']:,.0f}</div>
                </div>
                 <div class="map-legend-card" style="background: #fef3c7; border: 1px solid #fcd34d;">
                     <div style="color: #b45309;" class="map-legend-label">Lowest Enrollment</div>
                    <div style="color: #78350f;" class="map-legend-value">{map_stats['min']:,.0f}</div>
                </div>
                 <div class="map-legend-card" style="background: #faf5ff; border: 1px solid #e9d5ff;">
                     <div style="color: #7e22ce;" class="map-legend-label">Total Coverage</div>
                    <div style="color: #581c87;" class="map-legend-value">{map_stats['sum']:,.0f}</div>
                </div>
            </div>
            
            <footer style="margin-top: 50px; text-align: center; color: #9ca3af; font-size: 0.8rem;">
                Generated System Report • Confidential
            </footer>
        </main>
    </div>
</body>
</html>
    """

    with open(f"dashboard_output_{selected_state}.html", "w", encoding='utf-8') as f:
        f.write(html_content)
    print(f"Dashboard generated: dashboard_output_{selected_state}.html")

if __name__ == "__main__":
    try:
        # 1. First load data once to get list of states
        print("Initializing for batch generation...", flush=True)
        # We call load_and_merge_data with None to get all data first (optimized approach could be better but this is safe)
        # Actually to avoid OOM with massive data, we should just read unique states from one CSV first
        temp_df = pd.read_csv('combined enrolment.csv', usecols=['state'])
        all_states = sorted(temp_df['state'].dropna().unique())
        
        print(f"Found {len(all_states)} states: {all_states}", flush=True)
        
        generated_files = []
        
        for state in all_states:
            try:
                print(f"Generating for {state}...", flush=True)
                generate_html(state)
                generated_files.append((state, f"dashboard_output_{state}.html"))
            except Exception as e:
                print(f"Failed for {state}: {str(e)}", flush=True)

        # 2. Generate Index Page
        index_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>UIDAI National Dashboard Portal</title>
            <style>
                body { font-family: -apple-system, system-ui, sans-serif; background: #f8fafc; padding: 40px; }
                .container { max-width: 1000px; margin: 0 auto; }
                h1 { color: #1e293b; text-align: center; margin-bottom: 40px; }
                .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-decoration: none; color: #334155; transition: transform 0.2s; border: 1px solid #e2e8f0; display: block;}
                .card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-color: #6366f1; }
                .state-name { font-weight: 600; font-size: 1.1rem; }
                .view-link { color: #6366f1; font-size: 0.9rem; margin-top: 10px; display: block; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🇮🇳 UIDAI Strategic Oversight Portal</h1>
                <div class="grid">
        """
        
        for state_name, file_name in generated_files:
            index_html += f"""
            <a href="{file_name}" class="card">
                <div class="state-name">{state_name}</div>
                <span class="view-link">View Dashboard →</span>
            </a>
            """
            
        index_html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        with open("index.html", "w", encoding='utf-8') as f:
            f.write(index_html)
            
        print("✅ Batch Generation Complete. Open 'index.html' to view all dashboards.", flush=True)

    except Exception as e:
        print(f"FATAL: {e}", flush=True)
