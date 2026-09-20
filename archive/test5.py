import streamlit as st
import pandas as pd
import plotly.express as px
import json
import numpy as np

# ==========================================
# 1. PAGE CONFIGURATION & GOVT STYLING
# ==========================================
st.set_page_config(
    page_title="UIDAI Strategic Oversight Dashboard 2026",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern White Theme with Gradients
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
    }
    
    .main-header {
        font-size: 3rem; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
        margin-bottom: 10px;
        letter-spacing: -1px;
    }
    
    .sub-header {
        font-size: 1.1rem; 
        color: #6b7280; 
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }
    
    .metric-box {
        background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
        border: 1px solid #e5e7eb;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    .metric-value {
        font-size: 2.5rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .metric-label {
        font-size: 0.85rem; 
        color: #9ca3af; 
        text-transform: uppercase; 
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    .insight-card {
        background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
        border: 1px solid #bfdbfe;
        padding: 20px;
        border-radius: 16px;
        color: #1e40af;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1);
    }
    
    .risk-card {
        background: linear-gradient(135deg, #fee2e2 0%, #fef2f2 100%);
        border: 1px solid #fecaca;
        padding: 20px;
        border-radius: 16px;
        color: #991b1b;
        line-height: 1.6;
        box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.1);
    }
    
    .stPlotlyChart {
        background: white;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    h3 {
        color: #1f2937;
        font-weight: 700;
        font-size: 1.5rem;
        margin-top: 40px;
        margin-bottom: 20px;
        border-bottom: 3px solid;
        border-image: linear-gradient(90deg, #667eea 0%, #764ba2 100%) 1;
        padding-bottom: 10px;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
    }
    
    .stSelectbox label {
        color: #374151;
        font-weight: 600;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING ENGINE
# ==========================================
@st.cache_data
def load_and_merge_data():
    """
    Loads all 4 CSVs and merges them into a single Master DataFrame.
    """
    try:
        # 1. Load Transactional Data (Parse dates automatically)
        df_bio = pd.read_csv('combined biometrics.csv', parse_dates=['date'], dayfirst=True)
        df_demo = pd.read_csv('combined demographic.csv', parse_dates=['date'], dayfirst=True)
        df_enrol = pd.read_csv('combined enrolment.csv', parse_dates=['date'], dayfirst=True)
        
        # 2. Load Population Data (Handling the specific structure: index, pincode, population)
        # We assume column 1 is pincode and column 2 is population based on your sample
        df_pop = pd.read_csv('population.csv')
        # Rename columns to standard names if they aren't already
        if 'pincode' not in df_pop.columns:
            df_pop.rename(columns={df_pop.columns[1]: 'pincode', df_pop.columns[2]: 'population'}, inplace=True)
        
        # Ensure Pincode is string for accurate merging
        for df in [df_bio, df_demo, df_enrol, df_pop]:
            if 'pincode' in df.columns:
                df['pincode'] = df['pincode'].astype(str)

        # 3. Merge Transactional Files First
        merge_keys = ['date', 'state', 'district', 'pincode']
        df_master = pd.merge(df_bio, df_demo, on=merge_keys, how='outer')
        df_master = pd.merge(df_master, df_enrol, on=merge_keys, how='outer')
        
        # 4. Merge Population (Left Join: We keep transactions even if pop is missing)
        # Note: Population file doesn't have date/state/district usually, just pincode-pop mapping
        # We aggregate transactions by Pincode first to create a "Static View" for Saturation
        
        return df_master, df_pop

    except FileNotFoundError as e:
        st.error(f"❌ Critical Error: File {e.filename} not found.")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data
def load_geojson():
    try:
        with open('All_India_pincode.geojson', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# ==========================================
# 3. ANALYTICAL LOGIC (The Brain)
# ==========================================
def calculate_metrics(df, df_pop):
    # Fill NaNs with 0 for calculation
    df.fillna(0, inplace=True)

    # 1. Total Enrolment Per Row
    df['total_enrolment'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
    
    # 2. Compliance Ratio (Key Policy Metric)
    # Logic: Are kids (5-17) doing Bio updates? Or just Demo updates?
    # We add 1 to denominator to avoid DivideByZero
    df['child_compliance_ratio'] = df['bio_age_5_17'] / (df['demo_age_5_17'] + 1)
    
    # 3. Prepare District-Level Summary
    # We group by District to get aggregated stats
    district_summary = df.groupby(['state', 'district']).agg({
        'total_enrolment': 'sum',
        'age_0_5': 'sum',
        'bio_age_5_17': 'sum',
        'demo_age_5_17': 'sum',
        'demo_age_17_': 'sum'
    }).reset_index()

    # 4. Merge Population into District Summary for "Saturation"
    # First, aggregate population by pincode -> district mapping (if available in master)
    # Since df_pop only has pincode, we map it via the master df
    pincode_district_map = df[['pincode', 'district']].drop_duplicates()
    pop_with_dist = pd.merge(df_pop, pincode_district_map, on='pincode', how='inner')
    district_pop = pop_with_dist.groupby('district')['population'].sum().reset_index()
    
    final_summary = pd.merge(district_summary, district_pop, on='district', how='left')
    
    # 5. Calculate Saturation
    final_summary['saturation'] = (final_summary['total_enrolment'] / final_summary['population']) * 100
    
    return df, final_summary

# ==========================================
# 4. DASHBOARD LAYOUT
# ==========================================
def main():
    st.markdown('<div class="main-header">UIDAI Strategic Oversight Dashboard 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Data-Driven Governance: Saturation, Compliance & Operational Load</div>', unsafe_allow_html=True)
    
    # Load & Process
    with st.spinner("Integrating Datasets..."):
        df_raw, df_pop = load_and_merge_data()
        geojson = load_geojson()
        
    if df_raw.empty: return

    df_trans, df_dist_summary = calculate_metrics(df_raw, df_pop)

    # --- SIDEBAR ---
    st.sidebar.header("📍 Geographic Filters")
    selected_state = st.sidebar.selectbox("Select State", sorted(df_trans['state'].unique()))
    
    # Filter Data
    state_trans = df_trans[df_trans['state'] == selected_state]
    state_summary = df_dist_summary[df_dist_summary['state'] == selected_state]

    # --- KPI ROW ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    # KPIs
    total_ops = state_trans['total_enrolment'].sum() + state_trans['demo_age_17_'].sum()
    avg_saturation = state_summary['saturation'].mean()
    risk_districts = state_summary[state_summary['bio_age_5_17'] < state_summary['demo_age_5_17']].shape[0]
    
    with kpi1:
        st.markdown(f"""<div class="metric-box"><div class="metric-label">Total Transactions</div>
        <div class="metric-value">{total_ops:,.0f}</div></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="metric-box"><div class="metric-label">Avg Saturation</div>
        <div class="metric-value">{avg_saturation:.1f}%</div></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div class="metric-box"><div class="metric-label">Risk Districts</div>
        <div class="metric-value">{risk_districts}</div><div style="font-size:0.8rem; color:#9ca3af; margin-top:5px;">Low Bio Compliance</div></div>""", unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""<div class="metric-box"><div class="metric-label">New Births (0-5)</div>
        <div class="metric-value">{state_trans['age_0_5'].sum():,.0f}</div></div>""", unsafe_allow_html=True)

    # --- STORY 1: SATURATION ---
    st.markdown("### 1. Population Coverage (Saturation)")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        fig_sat = px.bar(
            state_summary.sort_values('saturation', ascending=False).head(10),
            x='district', y='saturation',
            title=f"Top 10 Districts by Saturation % in {selected_state}",
            color='saturation', 
            color_continuous_scale=[[0, '#667eea'], [0.5, '#764ba2'], [1, '#f093fb']],
            labels={'saturation': 'Saturation % (Enrolment / Pop)'}
        )
        # Add a reference line at 100%
        fig_sat.add_hline(y=100, line_dash="dot", line_color="#e5e7eb", 
                          annotation_text="100% Population", annotation_position="top right",
                          annotation_font_color="#000000")
        fig_sat.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='white',
            font=dict(family="Inter", color="#000000"),
            title_font=dict(size=18, color="#111827", family="Inter"),
            xaxis=dict(showgrid=False, showline=True, linecolor="#e5e7eb"),
            yaxis=dict(showgrid=True, gridcolor="#f3f4f6", showline=False)
        )
        st.plotly_chart(fig_sat, use_container_width=True)
    
    with c2:
        st.markdown("""
        <div class="insight-card">
        <b>What this means:</b><br>
        • <b>> 100%:</b> Indicates "Ghost Enrolments" (duplicates) or high migration IN.<br>
        • <b>< 80%:</b> Indicates "Exclusion Zones". People here likely lack access to schemes.<br><br>
        <b>Action:</b> Deploy mobile enrolment vans to districts below 85%.
        </div>
        """, unsafe_allow_html=True)

    # --- STORY 2: COMPLIANCE ---
    st.markdown("### 2. Child Welfare (Compliance Check)")
    c3, c4 = st.columns([2, 1])
    
    with c3:
        # Comparison Chart
        fig_comp = px.bar(
            state_summary.sort_values('bio_age_5_17', ascending=True).head(10),
            x='district', 
            y=['demo_age_5_17', 'bio_age_5_17'],
            barmode='group',
            title="Bottom 10 Districts: Biometric vs Demographic Updates",
            color_discrete_map={'demo_age_5_17': '#f093fb', 'bio_age_5_17': '#4ade80'},
            labels={'value': 'Count of Updates', 'variable': 'Update Type'}
        )
        fig_comp.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='white',
            font=dict(family="Inter", color="#1f2937"),
            title_font=dict(size=18, color="#111827", family="Inter"),
            xaxis=dict(showgrid=False, showline=True, linecolor="#e5e7eb"),
            yaxis=dict(showgrid=True, gridcolor="#f3f4f6", showline=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
    with c4:
        st.markdown("""
        <div class="risk-card">
        <b>What this means:</b><br>
        • <b>Red Bar > Green Bar:</b> Critical Failure. Children are fixing names/DOB but <b>missing</b> their Mandatory Biometric Update (Age 5/15).<br><br>
        <b>Hypothesis:</b> These districts likely have operators who are skipping the difficult biometric capture to save time.<br><br>
        <b>Action:</b> Audit operators in these districts immediately.
        </div>,
                       color_discrete_map={'demo_age_17_': '#667eea', 'age_0_5': '#f093fb'})
    fig_line.update_traces(line=dict(width=3))
    fig_line.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='white',
        font=dict(family="Inter", color="#1f2937"),
        title_font=dict(size=18, color="#111827", family="Inter"),
        xaxis=dict(showgrid=False, showline=True, linecolor="#e5e7eb"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", showline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    
        """, unsafe_allow_html=True)

    # --- STORY 3: TIME TRENDS ---
    st.markdown("### 3. Operational Timeline")
    # Group by Date
    daily_trend = state_trans.groupby('date')[['demo_age_17_', 'age_0_5']].sum().reset_index()
    fig_line = px.line(daily_trend, x='date', y=['demo_age_17_', 'age_0_5'], 
                       title="Daily Trend: Adult Updates vs New Births",
                       labels={'value': 'Count', 'variable': 'Metric'},
                       color_discrete_map={'demo_age_17_': '#667eea', 'age_0_5': '#f093fb'})
    fig_line.update_traces(line=dict(width=3))
    fig_line.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='white',
        font=dict(family="Inter", color="#000000"),
        title_font=dict(size=18, color="#111827", family="Inter"),
        xaxis=dict(showgrid=False, showline=True, linecolor="#e5e7eb"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", showline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- MAP SECTION ---
    if geojson:
        st.markdown(f"### 4. Hyper-Local Heatmap: {selected_state}")
        
        # Filter GeoJSON for this state only (Crucial for performance)
        active_pincodes = state_trans['pincode'].unique().tolist()
        filtered_features = [f for f in geojson['features'] if str(f['properties']['Pincode']) in active_pincodes]
        filtered_geojson = {'type': 'FeatureCollection', 'features': filtered_features}
        
        # Aggregate data by Pincode for the map
        map_data = state_trans.groupby('pincode')['total_enrolment'].sum().reset_index()
        
        if filtered_features:
            fig_map = px.choropleth_mapbox(
                map_data,
                geojson=filtered_geojson,
                locations='pincode',
                featureidkey="properties.Pincode",
                color='total_enrolment',
                color_continuous_scale=[[0, '#667eea'], [0.5, '#764ba2'], [1, '#f093fb']],
                mapbox_style="carto-positron",
                zoom=6,
                center={"lat": 22.0, "lon": 78.0}, # Dynamic centering can be added
                opacity=0.7,
                title="Pincode Level Enrolment Intensity"
            )
            fig_map.update_layout(
                margin={"r":0,"t":40,"l":0,"b":0},
                font=dict(family="Inter", color="#000000"),
                title_font=dict(size=18, color="#111827", family="Inter")
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No matching Pincode boundaries found in GeoJSON for this state.")

if __name__ == "__main__":
    main()