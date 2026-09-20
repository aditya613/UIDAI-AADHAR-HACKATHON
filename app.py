import streamlit as st
import pandas as pd
import plotly.express as px
import json
import numpy as np

# ==========================================
# 1. PAGE CONFIGURATION & PROFESSIONAL STYLING
# ==========================================
st.set_page_config(
    page_title="UIDAI Strategic Oversight Dashboard 2026",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean Light Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Force Light Theme */
    :root {
        color-scheme: light !important;
    }
    
    * {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    /* Pure White Background */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: #ffffff !important;
    }
    
    [data-testid="stAppViewContainer"] > section > div {
        background: #ffffff !important;
    }
    
    .block-container {
        padding: 2rem 3rem !important;
        max-width: 1400px !important;
        background: #ffffff !important;
    }
    
    /* Hero header */
    .main-header {
        font-size: 2.2rem; 
        color: #1a1a2e;
        font-weight: 700;
        text-align: left;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .sub-header {
        font-size: 1rem; 
        color: #6b7280; 
        text-align: left;
        margin-bottom: 32px;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    
    /* Metric cards - Clean & Modern */
    .metric-box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 24px 20px;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
    }
    .metric-box:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.12);
        border-color: #c7d2fe;
    }
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 10px;
        display: block;
    }
    .metric-value {
        font-size: 2.2rem; 
        font-weight: 700; 
        color: #1f2937;
        margin-bottom: 6px;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.75rem; 
        color: #6b7280; 
        text-transform: uppercase; 
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .metric-change {
        font-size: 0.85rem;
        color: #10b981;
        font-weight: 500;
    }
    
    /* Insight card - Soft Blue */
    .insight-card {
        background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
        border: 1px solid #bfdbfe;
        padding: 20px;
        border-radius: 12px;
        color: #1e40af;
        font-size: 0.9rem;
        line-height: 1.75;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.08);
    }
    .insight-card b { color: #1d4ed8; font-weight: 600; }
    
    /* Risk card - Soft Rose */
    .risk-card {
        background: linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%);
        border: 1px solid #fecaca;
        padding: 20px;
        border-radius: 12px;
        color: #991b1b;
        line-height: 1.75;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.08);
        font-size: 0.9rem;
    }
    .risk-card b { color: #b91c1c; font-weight: 600; }
    
    /* Charts - Clean White */
    .stPlotlyChart {
        background: #ffffff !important;
        border-radius: 12px !important;
        padding: 16px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid #f3f4f6 !important;
    }
    
    /* Section headings */
    h3, .stMarkdown h3 {
        font-weight: 600 !important;
        font-size: 1.35rem !important;
        margin-top: 40px !important;
        margin-bottom: 16px !important;
        padding-bottom: 12px !important;
        border-bottom: 2px solid #f3f4f6 !important;
        background: transparent !important;
    }
    
    /* Sidebar - Clean Light */
    [data-testid="stSidebar"] {
        background: #fafbfc !important;
        border-right: 1px solid #e5e7eb !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: #fafbfc !important;
    }
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] .stMarkdown h3 {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        border-bottom: none !important;
        margin-top: 16px !important;
    }
    
    /* Sidebar text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #4b5563 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox label { 
        color: #374151 !important; 
        font-weight: 500 !important; 
        font-size: 0.9rem !important; 
    }
    .stSelectbox > div > div {
        background: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #d1d5db !important;
        color: #1f2937 !important;
    }
    .stSelectbox [data-baseweb="select"] {
        background: #ffffff !important;
    }
    .stSelectbox [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #1f2937 !important;
    }
    
    /* Metric widget in sidebar */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: #ffffff !important;
        padding: 12px !important;
        border-radius: 8px !important;
        border: 1px solid #e5e7eb !important;
    }
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #1f2937 !important;
    }
    
    /* Force all text to be dark on light */
    p, span, div, label {
        color: #374151 !important;
    }
    
    /* Buttons - Modern Purple */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.4rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
        font-size: 0.9rem !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #6366f1 !important;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar - Subtle */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #f9fafb; }
    ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #9ca3af; }
    
    /* Divider */
    hr {
        border-color: #e5e7eb !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Warning/Info boxes */
    .stAlert {
        background: #fffbeb !important;
        border: 1px solid #fcd34d !important;
        color: #92400e !important;
        border-radius: 8px !important;
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
        df_bio = pd.read_csv('data/raw/combined biometrics.csv', parse_dates=['date'], dayfirst=True)
        df_demo = pd.read_csv('data/raw/combined demographic.csv', parse_dates=['date'], dayfirst=True)
        df_enrol = pd.read_csv('data/raw/combined enrolment.csv', parse_dates=['date'], dayfirst=True)
        
        # 2. Load Population Data
        df_pop = pd.read_csv('data/raw/population.csv')
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
        
        return df_master, df_pop

    except FileNotFoundError as e:
        st.error(f"❌ Critical Error: File {e.filename} not found.")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data
def load_geojson():
    try:
        with open('data/raw/All_India_pincode.geojson', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# ==========================================
# 3. ANALYTICAL LOGIC
# ==========================================
def calculate_metrics(df, df_pop):
    df.fillna(0, inplace=True)

    # 1. Total Enrolment Per Row
    df['total_enrolment'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
    
    # 2. Compliance Ratio
    df['child_compliance_ratio'] = df['bio_age_5_17'] / (df['demo_age_5_17'] + 1)
    
    # 3. District-Level Summary
    district_summary = df.groupby(['state', 'district']).agg({
        'total_enrolment': 'sum',
        'age_0_5': 'sum',
        'bio_age_5_17': 'sum',
        'demo_age_5_17': 'sum',
        'demo_age_17_': 'sum'
    }).reset_index()

    # 4. Merge Population
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
    # Header
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown('<div class="main-header">🇮🇳 UIDAI Strategic Oversight Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Data-Driven Governance · Real-Time Analytics · Compliance Monitoring</div>', unsafe_allow_html=True)
    with col_header2:
        st.markdown(f"<div style='text-align: right; padding-top: 16px;'><span style='color: #475569; font-size: 0.9rem;'>Last Updated</span><br><span style='color: #0b1324; font-weight: 700;'>Jan 20, 2026</span></div>", unsafe_allow_html=True)
    
    # Load & Process
    with st.spinner("Loading analytics data..."):
        df_raw, df_pop = load_and_merge_data()
        geojson = load_geojson()
        
    if df_raw.empty: 
        return

    df_trans, df_dist_summary = calculate_metrics(df_raw, df_pop)

    # --- SIDEBAR ---
    st.sidebar.markdown("### 📍 Geographic Filters")
    selected_state = st.sidebar.selectbox("Select State", sorted(df_trans['state'].unique()))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 National Overview")
    st.sidebar.metric("Total States", df_trans['state'].nunique())
    st.sidebar.metric("Total Districts", df_trans['district'].nunique())
    st.sidebar.metric("Active Pincodes", df_trans['pincode'].nunique())
    
    # Calculate national stats
    total_national_enrolment = df_trans['total_enrolment'].sum()
    total_biometric = df_trans['bio_age_5_17'].sum() if 'bio_age_5_17' in df_trans.columns else 0
    total_demographic = df_trans['demo_age_17_'].sum() if 'demo_age_17_' in df_trans.columns else 0
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 National Metrics")
    st.sidebar.metric("Total Enrollments", f"{total_national_enrolment:,.0f}")
    st.sidebar.metric("Biometric Updates", f"{total_biometric:,.0f}")
    st.sidebar.metric("Demographic Updates", f"{total_demographic:,.0f}")
    
    # Filter Data
    state_trans = df_trans[df_trans['state'] == selected_state]
    state_summary = df_dist_summary[df_dist_summary['state'] == selected_state]
    
    # State-specific sidebar stats
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### 🏛️ {selected_state} Stats")
    st.sidebar.metric("State Districts", state_trans['district'].nunique())
    st.sidebar.metric("State Pincodes", state_trans['pincode'].nunique())
    state_total_pop = state_summary['population'].sum() if 'population' in state_summary.columns else 0
    st.sidebar.metric("Est. Population", f"{state_total_pop:,.0f}")

    # --- KPI ROW ---
    st.markdown("### 🎯 Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    # KPIs
    total_ops = state_trans['total_enrolment'].sum() + state_trans['demo_age_17_'].sum()
    avg_saturation_val = state_summary['saturation'].dropna().mean()
    avg_saturation = 0 if np.isnan(avg_saturation_val) else avg_saturation_val
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
        <div class="metric-change" style="color:#dc2626;">⚠ Needs Attention</div>
        </div>""", unsafe_allow_html=True)
    
    with kpi4:
           st.markdown(f"""<div class="metric-box">
           <span class="metric-icon">👶</span>
           <div class="metric-label">New Births (0-5)</div>
           <div class="metric-value">{state_trans['age_0_5'].sum():,.0f}</div>
           <div class="metric-change">Future Citizens</div>
           </div>""", unsafe_allow_html=True)

    # --- SECOND ROW OF KPIs ---
    st.markdown("### 📋 Detailed Analytics")
    kpi5, kpi6, kpi7, kpi8 = st.columns(4)
    
    # Calculate additional metrics
    total_youth = state_trans['age_5_17'].sum() if 'age_5_17' in state_trans.columns else 0
    total_adults = state_trans['age_18_greater'].sum() if 'age_18_greater' in state_trans.columns else 0
    bio_updates = state_trans['bio_age_5_17'].sum() if 'bio_age_5_17' in state_trans.columns else 0
    demo_updates = state_trans['demo_age_17_'].sum() if 'demo_age_17_' in state_trans.columns else 0
    compliance_rate = (bio_updates / (demo_updates + 1)) * 100
    total_districts = state_trans['district'].nunique()
    high_coverage = state_summary[state_summary['saturation'] >= 80].shape[0] if 'saturation' in state_summary.columns else 0
    coverage_pct = (high_coverage / total_districts * 100) if total_districts > 0 else 0
    
    with kpi5:
        st.markdown(f"""<div class="metric-box" style="border-top: 3px solid #3b82f6;">
        <span class="metric-icon">🧑‍🎓</span>
        <div class="metric-label">Youth (5-17 years)</div>
        <div class="metric-value">{total_youth:,.0f}</div>
        <div class="metric-change">School-Age Population</div>
        </div>""", unsafe_allow_html=True)
    
    with kpi6:
        st.markdown(f"""<div class="metric-box" style="border-top: 3px solid #10b981;">
        <span class="metric-icon">👨‍💼</span>
        <div class="metric-label">Adults (18+)</div>
        <div class="metric-value">{total_adults:,.0f}</div>
        <div class="metric-change">Working Population</div>
        </div>""", unsafe_allow_html=True)
    
    with kpi7:
        compliance_color = "#10b981" if compliance_rate >= 80 else "#f59e0b" if compliance_rate >= 50 else "#ef4444"
        st.markdown(f"""<div class="metric-box" style="border-top: 3px solid {compliance_color};">
        <span class="metric-icon">✅</span>
        <div class="metric-label">Compliance Rate</div>
        <div class="metric-value">{compliance_rate:.1f}%</div>
        <div class="metric-change">Bio vs Demo Updates</div>
        </div>""", unsafe_allow_html=True)
    
    with kpi8:
        coverage_color = "#10b981" if coverage_pct >= 70 else "#f59e0b" if coverage_pct >= 50 else "#ef4444"
        st.markdown(f"""<div class="metric-box" style="border-top: 3px solid {coverage_color};">
        <span class="metric-icon">🎯</span>
        <div class="metric-label">Districts ≥80% Coverage</div>
        <div class="metric-value">{high_coverage}/{total_districts}</div>
        <div class="metric-change" style="color:{coverage_color}">{coverage_pct:.0f}% Meeting Target</div>
        </div>""", unsafe_allow_html=True)

    # --- SATURATION ANALYSIS ---
    st.markdown("### 📊 Population Coverage Analysis")
    c1, c2 = st.columns([2, 1])
    
    with c1:
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
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            font=dict(family="Inter", color="#1f2937", size=12),
            title_font=dict(size=16, color="#111827", family="Inter", weight=700),
            xaxis=dict(showgrid=False, showline=True, linecolor="#d1d5db", tickfont=dict(size=11, color="#374151")),
            yaxis=dict(showgrid=True, gridcolor="#9ca3af", gridwidth=1, showline=True, linecolor="#d1d5db", zeroline=False, tickfont=dict(size=11, color="#374151")),
            margin=dict(t=55, b=45, l=55, r=35),
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter", bordercolor="#6b7280")
        )
        st.plotly_chart(fig_sat, use_container_width=True)
    
    with c2:
        st.markdown("""
        <div class="insight-card">
        <b>What this means:</b><br>
        • <b>> 100%:</b> Indicates duplicate registrations or high migration influx.<br>
        • <b>< 80%:</b> Indicates exclusion zones where citizens lack scheme access.<br><br>
        <b>Recommended Action:</b> Deploy mobile enrollment units to districts below 85% coverage.
        </div>
        """, unsafe_allow_html=True)

    # --- COMPLIANCE MONITORING ---
    st.markdown("### 🛡️ Child Welfare Compliance Monitor")
    c3, c4 = st.columns([2, 1])
    
    with c3:
        fig_comp = px.bar(
            state_summary.sort_values('bio_age_5_17', ascending=True).head(10),
            x='district', 
            y=['demo_age_5_17', 'bio_age_5_17'],
            barmode='group',
            title="Priority Districts: Compliance Gap Analysis",
            color_discrete_map={'demo_age_5_17': '#f97316', 'bio_age_5_17': '#22c55e'},
            labels={'value': 'Updates Count', 'variable': 'Type', 'demo_age_5_17': 'Demographic', 'bio_age_5_17': 'Biometric', 'district': 'District'}
        )
        fig_comp.update_traces(marker=dict(line=dict(width=0)))
        fig_comp.update_layout(
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            font=dict(family="Inter", color="#1f2937", size=12),
            title_font=dict(size=16, color="#111827", family="Inter", weight=700),
            xaxis=dict(showgrid=False, showline=True, linecolor="#d1d5db", tickfont=dict(size=11, color="#374151")),
            yaxis=dict(showgrid=True, gridcolor="#9ca3af", gridwidth=1, showline=True, linecolor="#d1d5db", zeroline=False, tickfont=dict(size=11, color="#374151")),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                bgcolor="#ffffff", bordercolor="#6b7280", borderwidth=1,
                font=dict(size=11, color="#374151")
            ),
            margin=dict(t=55, b=45, l=55, r=35),
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter", bordercolor="#6b7280")
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
    with c4:
        st.markdown("""
        <div class="risk-card">
        <b>Critical Observation:</b><br>
        • <b>Red > Blue:</b> Children updating demographic info but missing mandatory biometric updates (Age 5/15).<br><br>
        <b>Root Cause Analysis:</b> Operators may be bypassing biometric capture to reduce processing time.<br><br>
        <b>Immediate Action:</b> Conduct operator audits in flagged districts.
        </div>
        """, unsafe_allow_html=True)

    # --- TIME TRENDS ---
    st.markdown("### 📅 Temporal Operations Analytics")
    daily_trend = state_trans.groupby('date')[['demo_age_17_', 'age_0_5']].sum().reset_index()
    fig_line = px.area(daily_trend, x='date', y=['demo_age_17_', 'age_0_5'], 
                       title="Activity Timeline: Updates & New Registrations",
                       labels={'value': 'Volume', 'variable': 'Category', 'demo_age_17_': 'Adult Updates', 'age_0_5': 'New Births', 'date': 'Date'},
                       color_discrete_map={'demo_age_17_': '#2563eb', 'age_0_5': '#7c3aed'})
    fig_line.update_traces(line=dict(width=2.5), opacity=0.85)
    fig_line.update_layout(
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        font=dict(family="Inter", color="#1f2937", size=12),
        title_font=dict(size=16, color="#111827", family="Inter", weight=700),
        xaxis=dict(showgrid=False, showline=True, linecolor="#d1d5db", tickfont=dict(size=11, color="#374151")),
        yaxis=dict(showgrid=True, gridcolor="#9ca3af", gridwidth=1, showline=True, linecolor="#d1d5db", zeroline=False, tickfont=dict(size=11, color="#374151")),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            bgcolor="#ffffff", bordercolor="#6b7280", borderwidth=1,
            font=dict(size=11, color="#374151")
        ),
        hovermode='x unified',
        margin=dict(t=55, b=45, l=55, r=35),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter", bordercolor="#6b7280")
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- MAP SECTION ---
    if geojson:
        st.markdown(f"### 🗺️ Geographic Intelligence: {selected_state}")
        
        # Map description card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); padding: 16px 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #bfdbfe;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 600; color: #1e40af;">📍 Pincode-Level Enrollment Density Map</span>
                    <p style="color: #475569; margin: 4px 0 0 0; font-size: 0.9rem;">Interactive visualization showing Aadhaar enrollment distribution across {selected_state}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 0.8rem; color: #6b7280;">Active Pincodes</span>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1e40af;">{state_trans['pincode'].nunique()}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        active_pincodes = state_trans['pincode'].unique().tolist()
        filtered_features = [f for f in geojson['features'] if str(f['properties']['Pincode']) in active_pincodes]
        filtered_geojson = {'type': 'FeatureCollection', 'features': filtered_features}
        
        # Enhanced map data with more details
        map_data = state_trans.groupby('pincode').agg({
            'total_enrolment': 'sum',
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum',
            'district': 'first'
        }).reset_index()
        
        # Calculate center based on state
        state_centers = {
            'MAHARASHTRA': {"lat": 19.7515, "lon": 75.7139, "zoom": 6},
            'GUJARAT': {"lat": 22.2587, "lon": 71.1924, "zoom": 6},
            'RAJASTHAN': {"lat": 27.0238, "lon": 74.2179, "zoom": 5.5},
            'KARNATAKA': {"lat": 15.3173, "lon": 75.7139, "zoom": 6},
            'TAMIL NADU': {"lat": 11.1271, "lon": 78.6569, "zoom": 6},
            'UTTAR PRADESH': {"lat": 26.8467, "lon": 80.9462, "zoom": 5.5},
            'MADHYA PRADESH': {"lat": 22.9734, "lon": 78.6569, "zoom": 5.5},
            'WEST BENGAL': {"lat": 22.9868, "lon": 87.8550, "zoom": 6},
            'ANDHRA PRADESH': {"lat": 15.9129, "lon": 79.7400, "zoom": 6},
            'TELANGANA': {"lat": 18.1124, "lon": 79.0193, "zoom": 7},
        }
        
        map_center = state_centers.get(selected_state.upper(), {"lat": 22.0, "lon": 78.0, "zoom": 5})
        
        if filtered_features:
            # Beautiful color scale - vibrant gradient
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
                margin={"r":10,"t":10,"l":10,"b":10},
                font=dict(family="Plus Jakarta Sans, Inter, sans-serif", color="#1f2937", size=12),
                paper_bgcolor='#ffffff',
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=13,
                    font_family="Plus Jakarta Sans, Inter",
                    bordercolor="#3b82f6",
                    font_color="#1f2937"
                ),
                coloraxis_colorbar=dict(
                    title=dict(text="Enrollments", font=dict(size=13, color="#374151")),
                    tickfont=dict(size=11, color="#4b5563"),
                    thickness=15,
                    len=0.7,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#e5e7eb",
                    borderwidth=1,
                    outlinecolor="#d1d5db",
                    outlinewidth=1
                )
            )
            
            # Add border/outline to polygons
            fig_map.update_traces(
                marker_line_width=1,
                marker_line_color='#1e40af'
            )
            
            # Update map height for better viewing
            fig_map.update_layout(height=700)
            
            # Enable fullscreen mode with enhanced controls
            st.plotly_chart(
                fig_map, 
                use_container_width=True, 
                config={
                    'displayModeBar': True,
                    'scrollZoom': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': [],
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': f'{selected_state}_enrollment_map',
                        'height': 1080,
                        'width': 1920,
                        'scale': 2
                    }
                }
            )
            
            # Map legend/stats below
            map_col1, map_col2, map_col3, map_col4 = st.columns(4)
            with map_col1:
                st.markdown(f"""
                <div style="background: #f0f9ff; padding: 14px; border-radius: 10px; text-align: center; border: 1px solid #bae6fd;">
                    <div style="font-size: 0.75rem; color: #0369a1; text-transform: uppercase; font-weight: 600;">Highest Enrollment</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #0c4a6e;">{map_data['total_enrolment'].max():,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with map_col2:
                st.markdown(f"""
                <div style="background: #f0fdf4; padding: 14px; border-radius: 10px; text-align: center; border: 1px solid #bbf7d0;">
                    <div style="font-size: 0.75rem; color: #15803d; text-transform: uppercase; font-weight: 600;">Avg per Pincode</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #14532d;">{map_data['total_enrolment'].mean():,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with map_col3:
                st.markdown(f"""
                <div style="background: #fef3c7; padding: 14px; border-radius: 10px; text-align: center; border: 1px solid #fcd34d;">
                    <div style="font-size: 0.75rem; color: #b45309; text-transform: uppercase; font-weight: 600;">Lowest Enrollment</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #78350f;">{map_data['total_enrolment'].min():,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with map_col4:
                st.markdown(f"""
                <div style="background: #faf5ff; padding: 14px; border-radius: 10px; text-align: center; border: 1px solid #e9d5ff;">
                    <div style="font-size: 0.75rem; color: #7e22ce; text-transform: uppercase; font-weight: 600;">Total Coverage</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #581c87;">{map_data['total_enrolment'].sum():,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ No matching pincode boundaries found in GeoJSON for this state.")

if __name__ == "__main__":
    main()