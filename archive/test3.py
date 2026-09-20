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

# Stunning Modern Dashboard CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Beautiful Gradient Background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding: 2rem 3rem !important;
        max-width: 1400px !important;
    }
    
    /* Glassmorphism Header */
    .main-header {
        font-size: 3.5rem; 
        background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-align: center;
        margin-bottom: 15px;
        letter-spacing: -2px;
        text-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
        animation: fadeInDown 0.8s ease;
    }
    
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .sub-header {
        font-size: 1.15rem; 
        color: #e0e7ff; 
        text-align: center;
        margin-bottom: 50px;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    
    /* Premium Glassmorphic Cards */
    .metric-box {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 32px 28px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 5px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-box::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.4s;
    }
    
    .metric-box:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px 0 rgba(102, 126, 234, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    .metric-box:hover::after {
        opacity: 1;
    }
    
    .metric-icon {
        font-size: 2.5rem;
        margin-bottom: 15px;
        display: block;
    }
    
    .metric-value {
        font-size: 3rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.8rem; 
        color: #6b7280; 
        text-transform: uppercase; 
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    .metric-change {
        font-size: 0.85rem;
        color: #10b981;
        font-weight: 600;
        margin-top: 8px;
    }
    
    /* Beautiful Insight Cards */
    .insight-card {
        background: linear-gradient(135deg, rgba(219, 234, 254, 0.9) 0%, rgba(239, 246, 255, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(147, 197, 253, 0.3);
        padding: 28px;
        border-radius: 20px;
        color: #1e40af;
        font-size: 0.95rem;
        line-height: 1.8;
        box-shadow: 0 8px 32px 0 rgba(59, 130, 246, 0.15);
    }
    
    .insight-card b {
        color: #1e3a8a;
        font-weight: 700;
    }
    
    /* Elegant Risk Cards */
    .risk-card {
        background: linear-gradient(135deg, rgba(254, 226, 226, 0.9) 0%, rgba(254, 242, 242, 0.9) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(252, 165, 165, 0.3);
        padding: 28px;
        border-radius: 20px;
        color: #991b1b;
        line-height: 1.8;
        box-shadow: 0 8px 32px 0 rgba(239, 68, 68, 0.15);
    }
    
    .risk-card b {
        color: #7f1d1d;
        font-weight: 700;
    }
    
    /* Chart Containers with Glassmorphism */
    .stPlotlyChart {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        padding: 25px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Stylish Section Headers */
    h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        margin-top: 60px !important;
        margin-bottom: 30px !important;
        padding: 15px 0 !important;
        position: relative !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border: none !important;
    }
    
    h3::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 80px;
        height: 4px;
        background: linear-gradient(90deg, #ffffff 0%, transparent 100%);
        border-radius: 2px;
    }
    
    /* Premium Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(226, 232, 240, 0.5) !important;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    
    .stSelectbox label {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* Beautiful Select Box */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    
    /* Premium Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px 0 rgba(102, 126, 234, 0.6);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
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
    st.markdown('<div class="main-header">🇮🇳 UIDAI Strategic Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">✨ Data-Driven Governance · Real-Time Analytics · Compliance Monitoring ✨</div>', unsafe_allow_html=True)
    
    # Load & Process
    with st.spinner("🔄 Loading analytics data..."):
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
        st.markdown(f"""<div class="metric-box">
        <span class="metric-icon">📊</span>
        <div class="metric-label">Total Transactions</div>
        <div class="metric-value">{total_ops:,.0f}</div>
        <div class="metric-change">↗ Active Operations</div>
        </div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="metric-box">
        <span class="metric-icon">📈</span>
        <div class="metric-label">Avg Saturation</div>
        <div class="metric-value">{avg_saturation:.1f}%</div>
        <div class="metric-change">Population Coverage</div>
        </div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div class="metric-box">
        <span class="metric-icon">⚠️</span>
        <div class="metric-label">Risk Districts</div>
        <div class="metric-value">{risk_districts}</div>
        <div class="metric-change" style="color:#ef4444;">⚡ Needs Attention</div>
        </div>""", unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""<div class="metric-box">
        <span class="metric-icon">👶</span>
        <div class="metric-label">New Births (0-5)</div>
        <div class="metric-value">{state_trans['age_0_5'].sum():,.0f}</div>
        <div class="metric-change">Future Citizens</div>
        </div>""", unsafe_allow_html=True)

    # --- STORY 1: SATURATION ---
    st.markdown("### 📊 Population Coverage Analysis")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        fig_sat = px.bar(
            state_summary.sort_values('saturation', ascending=False).head(10),
            x='district', y='saturation',
            title=f"🏆 Top 10 High-Coverage Districts in {selected_state}",
            color='saturation', 
            color_continuous_scale=[
                [0, '#fbbf24'], [0.3, '#f59e0b'], [0.6, '#10b981'], [0.8, '#059669'], [1, '#047857']
            ],
            labels={'saturation': 'Coverage %'}
        )
        fig_sat.add_hline(y=100, line_dash="dash", line_color="#ffffff", line_width=2,
                          annotation_text="🎯 100% Target", annotation_position="top right",
                          annotation_font=dict(size=12, color="#ffffff", family="Poppins"))
        fig_sat.update_traces(marker=dict(line=dict(width=0)))
        fig_sat.update_layout(
            plot_bgcolor='rgba(255,255,255,0.05)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(family="Poppins", color="#1f2937", size=11),
            title_font=dict(size=16, color="#111827", family="Poppins", weight=600),
            xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", showline=False, zeroline=False),
            margin=dict(t=60, b=60, l=60, r=40),
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Poppins")
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
    st.markdown("### 🛡️ Child Welfare Compliance Monitor")
    c3, c4 = st.columns([2, 1])
    
    with c3:
        # Comparison Chart
        fig_comp = px.bar(
            state_summary.sort_values('bio_age_5_17', ascending=True).head(10),
            x='district', 
            y=['demo_age_5_17', 'bio_age_5_17'],
            barmode='group',
            title="⚠️ Priority Districts: Compliance Gap Analysis",
            color_discrete_map={'demo_age_5_17': '#f43f5e', 'bio_age_5_17': '#06b6d4'},
            labels={'value': 'Updates Count', 'variable': 'Type', 'demo_age_5_17': '📝 Demographic', 'bio_age_5_17': '🔒 Biometric'}
        )
        fig_comp.update_traces(marker=dict(line=dict(width=0)))
        fig_comp.update_layout(
            plot_bgcolor='rgba(255,255,255,0.05)',
            paper_bgcolor='rgba(255,255,255,0)',
            font=dict(family="Poppins", color="#1f2937", size=11),
            title_font=dict(size=16, color="#111827", family="Poppins", weight=600),
            xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", showline=False, zeroline=False),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                bgcolor="rgba(255,255,255,0.8)", bordercolor="rgba(0,0,0,0.1)", borderwidth=1
            ),
            margin=dict(t=60, b=60, l=60, r=40),
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Poppins")
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
    with c4:
        st.markdown("""
        <div class="risk-card">
        <b>What this means:</b><br>
        • <b>Red Bar > Green Bar:</b> Critical Failure. Children are fixing names/DOB but <b>missing</b> their Mandatory Biometric Update (Age 5/15).<br><br>
        <b>Hypothesis:</b> These districts likely have operators who are skipping the difficult biometric capture to save time.<br><br>
        <b>Action:</b> Audit operators in these districts immediately.
        </div>
        """, unsafe_allow_html=True)

    # --- STORY 3: TIME TRENDS ---
    st.markdown("### 📅 Temporal Operations Analytics")
    # Group by Date
    daily_trend = state_trans.groupby('date')[['demo_age_17_', 'age_0_5']].sum().reset_index()
    fig_line = px.area(daily_trend, x='date', y=['demo_age_17_', 'age_0_5'], 
                       title="📈 Activity Timeline: Updates & New Registrations",
                       labels={'value': 'Volume', 'variable': 'Category', 'demo_age_17_': '👥 Adult Updates', 'age_0_5': '👶 New Births'},
                       color_discrete_map={'demo_age_17_': '#667eea', 'age_0_5': '#f093fb'})
    fig_line.update_traces(
        line=dict(width=3),
        fillpattern=dict(shape=""),
        opacity=0.7
    )
    fig_line.update_layout(
        plot_bgcolor='rgba(255,255,255,0.05)',
        paper_bgcolor='rgba(255,255,255,0)',
        font=dict(family="Poppins", color="#1f2937", size=11),
        title_font=dict(size=16, color="#111827", family="Poppins", weight=600),
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", showline=False, zeroline=False),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0.8)", bordercolor="rgba(0,0,0,0.1)", borderwidth=1
        ),
        hovermode='x unified',
        margin=dict(t=60, b=60, l=60, r=40),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Poppins")
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- MAP SECTION ---
    if geojson:
        st.markdown(f"### 🗺️ Geographic Intelligence: {selected_state}")
        
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
                color_continuous_scale=[
                    [0, '#dbeafe'], [0.2, '#93c5fd'], [0.4, '#60a5fa'], 
                    [0.6, '#3b82f6'], [0.8, '#2563eb'], [1, '#1d4ed8']
                ],
                mapbox_style="carto-positron",
                zoom=6,
                center={"lat": 22.0, "lon": 78.0},
                opacity=0.8,
                title="🎯 Pincode-Level Enrolment Density Heatmap",
                labels={'total_enrolment': 'Enrolments'}
            )
            fig_map.update_layout(
                margin={"r":0,"t":50,"l":0,"b":0},
                font=dict(family="Poppins", color="#1f2937", size=11),
                title_font=dict(size=16, color="#111827", family="Poppins", weight=600),
                hoverlabel=dict(bgcolor="white", font_size=12, font_family="Poppins")
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No matching Pincode boundaries found in GeoJSON for this state.")

if __name__ == "__main__":
    main()