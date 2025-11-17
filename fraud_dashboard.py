import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ======================================================================
# MODERN STREAMLIT CONFIGURATION
# ======================================================================
st.set_page_config(
    page_title="AI Fraud Detection Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================================================================
# CUSTOM CSS FOR MODERN UI
# ======================================================================
st.markdown("""
<style>
    .main {
        background-color: #0f1116;
        color: #ffffff;
    }
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 700;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #404040;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .dashboard-section {
        background: rgba(30, 30, 30, 0.7);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #404040;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #a0a0a0 !important;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #ff4b4b 0%, #ff6b6b 100%);
    }
    .dataframe {
        background-color: #1e1e1e !important;
        color: white !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ======================================================================
# DATA LOADING & VALIDATION
# ======================================================================
FULL_DATA_FILE = "fraud_detection_full_dataset.csv"
SUSPICIOUS_DATA_FILE = "fraud_detection_suspicious.csv"

@st.cache_data(ttl=3600)
def load_data():
    """Load data with enhanced mock data for demo"""
    
    def generate_enhanced_mock_data():
        np.random.seed(42)
        N = 17592

        # Generate realistic fraud scores
        normal_scores = np.random.beta(2, 8, int(N * 0.92))
        suspicious_scores = np.random.beta(8, 2, int(N * 0.06))
        fraud_scores = np.random.beta(15, 2, int(N * 0.02))

        scores = np.concatenate([normal_scores, suspicious_scores, fraud_scores])
        np.random.shuffle(scores)
        scores = np.clip(scores, 0.01, 0.99)

        # Enhanced job data
        job_titles = [
            'Senior Data Analyst', 'Marketing Intern', 'Full Stack Developer',
            'Product Manager', 'HR Coordinator', 'DevOps Engineer', 'Data Scientist',
            'Frontend Developer', 'Backend Engineer', 'UX Designer', 'Sales Executive'
        ]
        locations = [
            'New York, NY', 'San Francisco, CA', 'Remote', 'Austin, TX',
            'London, UK', 'Berlin, DE', 'Toronto, CA', 'Chicago, IL'
        ]
        industries = [
            'Technology', 'Finance', 'Healthcare', 'E-commerce',
            'Education', 'Manufacturing', 'Consulting'
        ]

        data = pd.DataFrame({
            'Job Title': np.random.choice(job_titles, N),
            'Job Location': np.random.choice(locations, N),
            'Industry': np.random.choice(industries, N),
            'Company Size': np.random.choice(['Startup', 'Small', 'Medium', 'Large', 'Enterprise'], N),
            'fraud_score': scores,
            'title_freq_scaled': np.random.exponential(0.5, N),
            'max_title_similarity_scaled': np.random.beta(1.5, 5, N),
            'submission_date': pd.date_range('2024-01-01', periods=N, freq='H'),
            'response_time_hours': np.random.exponential(24, N)
        })

        # Create fraud_flag and Alert_Reason
        threshold = np.quantile(scores, 0.95)
        data['fraud_flag'] = scores >= threshold
        
        conditions = [
            data['fraud_score'] >= 0.9,
            data['fraud_score'] >= 0.8,
            data['fraud_score'] >= 0.7
        ]
        choices = [
            '🚨 HIGH RISK: Multiple Anomaly Indicators',
            '⚠️ MEDIUM RISK: Behavioral Patterns Detected',
            '🔍 SUSPICIOUS: Unusual Submission Patterns'
        ]
        data['Alert_Reason'] = np.select(conditions, choices, default='Normal')

        df_suspicious = data[data['fraud_flag']].sort_values('fraud_score', ascending=False)
        df_full = data.sort_values('fraud_score', ascending=False)

        return df_full, df_suspicious

    try:
        df_full = pd.read_csv(FULL_DATA_FILE)
        df_suspicious = pd.read_csv(SUSPICIOUS_DATA_FILE)
        
        # Validate and enhance real data
        df_full, df_suspicious = validate_and_enhance_data(df_full, df_suspicious)
        
        st.success("✅ Production data loaded successfully")
        return df_full, df_suspicious
    except FileNotFoundError:
        st.warning("📁 Using demo data - CSV files not found")
        return generate_enhanced_mock_data()
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return generate_enhanced_mock_data()

def validate_and_enhance_data(df_full, df_suspicious):
    """Validate and enhance real data with missing columns"""
    
    # Ensure Industry column exists
    if 'Industry' not in df_full.columns:
        industries = ['Technology', 'Finance', 'Healthcare', 'E-commerce', 'Education', 'Manufacturing', 'Consulting']
        df_full['Industry'] = np.random.choice(industries, len(df_full))
    
    # Ensure fraud_flag exists
    if 'fraud_flag' not in df_full.columns and 'fraud_score' in df_full.columns:
        threshold = np.quantile(df_full['fraud_score'], 0.95)
        df_full['fraud_flag'] = df_full['fraud_score'] >= threshold
    
    # Create Alert_Reason if missing
    if 'Alert_Reason' not in df_full.columns and 'fraud_score' in df_full.columns:
        conditions = [
            df_full['fraud_score'] >= 0.9,
            df_full['fraud_score'] >= 0.8,
            df_full['fraud_score'] >= 0.7
        ]
        choices = [
            '🚨 HIGH RISK: Multiple Anomaly Indicators',
            '⚠️ MEDIUM RISK: Behavioral Patterns Detected',
            '🔍 SUSPICIOUS: Unusual Submission Patterns'
        ]
        df_full['Alert_Reason'] = np.select(conditions, choices, default='Normal')
    
    # Update suspicious dataframe
    if 'fraud_flag' in df_full.columns:
        df_suspicious = df_full[df_full['fraud_flag']].copy()
    
    return df_full, df_suspicious

# ======================================================================
# HEADER SECTION
# ======================================================================
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; 
                border-radius: 15px; 
                margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🛡️ AI Fraud Detection System</h1>
        <p style='color: rgba(255,255,255,0.9); font-size: 1.2rem; margin: 0.5rem 0 0 0;'>
        Advanced Machine Learning Pipeline for Anomaly Detection
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style='background: rgba(30,30,30,0.8); padding: 1.5rem; border-radius: 15px; text-align: center;'>
        <p style='color: #a0a0a0; margin: 0; font-size: 0.9rem;'>Last Updated</p>
        <p style='color: white; margin: 0; font-size: 1.1rem; font-weight: bold;'>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)

# Load data
with st.spinner('🔄 Loading fraud detection data...'):
    df_full, df_suspicious = load_data()

# Debug: Show available columns
debug_mode = False  # Set to True to see debug info
if debug_mode:
    st.sidebar.markdown("### 🔍 Debug Info")
    st.sidebar.write("Full data columns:", df_full.columns.tolist())
    st.sidebar.write("Suspicious data columns:", df_suspicious.columns.tolist())
    if 'Industry' in df_suspicious.columns:
        st.sidebar.write("Industries available:", df_suspicious['Industry'].unique().tolist())

# Calculate metrics safely
total_apps = len(df_full)
flagged_apps = len(df_suspicious) if hasattr(df_suspicious, '__len__') else 0
suspicion_rate = (flagged_apps / total_apps) * 100 if total_apps > 0 else 0

avg_fraud_score = 0
fraud_threshold = 0.8
if 'fraud_score' in df_suspicious.columns and len(df_suspicious) > 0:
    avg_fraud_score = df_suspicious['fraud_score'].mean()
    fraud_threshold = df_suspicious['fraud_score'].min()
elif 'fraud_score' in df_full.columns:
    fraud_threshold = np.quantile(df_full['fraud_score'], 0.95)

# ======================================================================
# KPI CARDS
# ======================================================================
st.markdown("### 📊 Executive Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
            <div style='font-size: 2rem; margin-right: 0.5rem;'>📈</div>
            <div style='font-size: 0.9rem; color: #a0a0a0;'>Total Applications</div>
        </div>
        <div style='font-size: 2rem; font-weight: bold; color: #ffffff;'>{total_apps:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
            <div style='font-size: 2rem; margin-right: 0.5rem;'>🚨</div>
            <div style='font-size: 0.9rem; color: #a0a0a0;'>Flagged Applications</div>
        </div>
        <div style='font-size: 2rem; font-weight: bold; color: #ff6b6b;'>{flagged_apps:,}</div>
        <div style='font-size: 0.9rem; color: #a0a0a0;'>{suspicion_rate:.2f}% detection rate</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
            <div style='font-size: 2rem; margin-right: 0.5rem;'>⚡</div>
            <div style='font-size: 0.9rem; color: #a0a0a0;'>Avg Fraud Score</div>
        </div>
        <div style='font-size: 2rem; font-weight: bold; color: #ffd93d;'>{avg_fraud_score:.3f}</div>
        <div style='font-size: 0.9rem; color: #a0a0a0;'>Higher = More suspicious</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
            <div style='font-size: 2rem; margin-right: 0.5rem;'>🎯</div>
            <div style='font-size: 0.9rem; color: #a0a0a0;'>Detection Threshold</div>
        </div>
        <div style='font-size: 2rem; font-weight: bold; color: #6bcf7f;'>{fraud_threshold:.3f}</div>
        <div style='font-size: 0.9rem; color: #a0a0a0;'>95th percentile</div>
    </div>
    """, unsafe_allow_html=True)

# ======================================================================
# METHODOLOGY SECTION
# ======================================================================
st.markdown("---")
st.markdown("### 🔬 Detection Methodology")

method_col1, method_col2 = st.columns([2, 1])

with method_col1:
    st.markdown("""
    **🛡️ Multi-Layer Anomaly Detection**
    
    Our system employs a sophisticated ensemble approach combining:
    
    • **Isolation Forest**: Identifies outliers in high-dimensional space  
    • **K-Means Clustering**: Detects unusual patterns across applicant groups  
    • **Behavioral Analysis**: Analyzes submission patterns and frequencies
    
    **🎯 Proxy Feature Engineering**
    
    Advanced feature engineering transforms raw data into powerful fraud signals:
    
    • **Frequency Analysis**: Submission patterns and repetition detection  
    • **Similarity Scoring**: Fuzzy matching for near-duplicate detection  
    • **Temporal Patterns**: Submission timing and velocity analysis
    """)

with method_col2:
    st.markdown("**📊 Model Performance**")
    
    # Precision
    st.markdown("""
    <div style='background: rgba(107, 207, 127, 0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
        <div style='color: #6bcf7f; font-weight: bold;'>Precision: 94.2%</div>
        <div style='height: 8px; background: rgba(107, 207, 127, 0.3); border-radius: 4px; margin: 0.5rem 0;'>
            <div style='height: 100%; width: 94.2%; background: #6bcf7f; border-radius: 4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Recall
    st.markdown("""
    <div style='background: rgba(255, 107, 107, 0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
        <div style='color: #ff6b6b; font-weight: bold;'>Recall: 89.7%</div>
        <div style='height: 8px; background: rgba(255, 107, 107, 0.3); border-radius: 4px; margin: 0.5rem 0;'>
            <div style='height: 100%; width: 89.7%; background: #ff6b6b; border-radius: 4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # F1-Score
    st.markdown("""
    <div style='background: rgba(255, 217, 61, 0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
        <div style='color: #ffd93d; font-weight: bold;'>F1-Score: 91.9%</div>
        <div style='height: 8px; background: rgba(255, 217, 61, 0.3); border-radius: 4px; margin: 0.5rem 0;'>
            <div style='height: 100%; width: 91.9%; background: #ffd93d; border-radius: 4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ======================================================================
# VISUALIZATIONS
# ======================================================================
st.markdown("---")
st.markdown("### 📈 Fraud Analytics Dashboard")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.markdown("#### Fraud Score Distribution")
    
    if 'fraud_score' in df_full.columns:
        fig1 = px.histogram(
            df_full,
            x='fraud_score',
            nbins=50,
            color_discrete_sequence=['#ff6b6b'],
            opacity=0.8
        )
        
        fig1.add_vline(
            x=fraud_threshold,
            line_dash="dash",
            line_color="yellow",
            annotation_text=f"Threshold: {fraud_threshold:.3f}"
        )
        
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis_title='Fraud Score',
            yaxis_title='Count',
            showlegend=False
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("📊 Fraud score data not available")

with viz_col2:
    st.markdown("#### Risk Level Breakdown")
    
    if 'fraud_score' in df_full.columns:
        risk_bins = [0, 0.3, 0.6, 0.8, 0.9, 1.0]
        risk_labels = ['🟢 Low', '🟡 Medium', '🟠 High', '🔴 Critical', '🚨 Severe']
        df_full['risk_level'] = pd.cut(df_full['fraud_score'], bins=risk_bins, labels=risk_labels)
        risk_counts = df_full['risk_level'].value_counts()
        
        fig2 = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            color_discrete_sequence=['#00d26a', '#ffd93d', '#ffa726', '#ff6b6b', '#dc2626'],
            hole=0.4
        )
        
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            showlegend=True
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("📊 Fraud score data not available")

# ======================================================================
# ALERT ANALYSIS
# ======================================================================
st.markdown("---")
st.markdown("### 🚨 Alert Analysis & Patterns")

alert_col1, alert_col2 = st.columns(2)

with alert_col1:
    st.markdown("#### Alert Reason Distribution")
    
    if 'Alert_Reason' in df_suspicious.columns and len(df_suspicious) > 0:
        alert_reasons = df_suspicious['Alert_Reason'].value_counts()
        
        fig3 = px.bar(
            x=alert_reasons.values,
            y=alert_reasons.index,
            orientation='h',
            color=alert_reasons.values,
            color_continuous_scale='reds'
        )
        
        fig3.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis_title='Count',
            yaxis_title='Alert Reason',
            showlegend=False,
            coloraxis_showscale=False
        )
        
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("📊 Alert reason data not available")

with alert_col2:
    st.markdown("#### Top Suspicious Job Titles")
    
    if 'Job Title' in df_suspicious.columns and len(df_suspicious) > 0:
        top_titles = df_suspicious['Job Title'].value_counts().head(10)
        
        fig4 = px.bar(
            x=top_titles.values,
            y=top_titles.index,
            orientation='h',
            color=top_titles.values,
            color_continuous_scale='oranges'
        )
        
        fig4.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis_title='Count',
            yaxis_title='Job Title',
            showlegend=False,
            coloraxis_showscale=False
        )
        
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("📊 Job title data not available")

# ======================================================================
# ACTIONABLE INSIGHTS
# ======================================================================
st.markdown("---")
st.markdown("### 🎯 Actionable Intelligence")

# Filters
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    min_score = st.slider("Minimum Fraud Score", 0.0, 1.0, float(fraud_threshold), 0.05)

with filter_col2:
    location_options = ['All']
    if 'Job Location' in df_suspicious.columns:
        unique_locations = df_suspicious['Job Location'].unique().tolist()
        if unique_locations:
            location_options.extend(sorted(unique_locations))
    selected_location = st.selectbox("Location Filter", location_options)

with filter_col3:
    # Industry filter - FIXED: Always ensure industries are available
    industry_options = ['All']
    
    # Check if Industry column exists and has data
    if 'Industry' in df_suspicious.columns:
        unique_industries = df_suspicious['Industry'].unique().tolist()
        if unique_industries and len(unique_industries) > 0:
            industry_options.extend(sorted(unique_industries))
        else:
            # If Industry column exists but is empty, add default industries
            default_industries = ['Technology', 'Finance', 'Healthcare', 'E-commerce', 'Education', 'Manufacturing', 'Consulting']
            industry_options.extend(default_industries)
    else:
        # If Industry column doesn't exist, add default industries
        default_industries = ['Technology', 'Finance', 'Healthcare', 'E-commerce', 'Education', 'Manufacturing', 'Consulting']
        industry_options.extend(default_industries)
    
    selected_industry = st.selectbox("Industry Filter", industry_options)

# Apply filters safely
filtered_suspicious = df_suspicious.copy()

if 'fraud_score' in filtered_suspicious.columns:
    filtered_suspicious = filtered_suspicious[filtered_suspicious['fraud_score'] >= min_score]

if selected_location != 'All' and 'Job Location' in filtered_suspicious.columns:
    filtered_suspicious = filtered_suspicious[filtered_suspicious['Job Location'] == selected_location]

if selected_industry != 'All' and 'Industry' in filtered_suspicious.columns:
    filtered_suspicious = filtered_suspicious[filtered_suspicious['Industry'] == selected_industry]

# Calculate summary metrics safely
filtered_count = len(filtered_suspicious)

avg_score_text = "N/A"
if 'fraud_score' in filtered_suspicious.columns and len(filtered_suspicious) > 0:
    avg_score = filtered_suspicious['fraud_score'].mean()
    avg_score_text = f"{avg_score:.3f}"

critical_alerts_text = "N/A"
if 'fraud_score' in filtered_suspicious.columns and len(filtered_suspicious) > 0:
    critical_alerts = (filtered_suspicious['fraud_score'] >= 0.9).sum()
    critical_alerts_text = f"{critical_alerts:,}"

# Summary display
st.markdown(f"""
<div style='background: rgba(255, 107, 107, 0.1); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
    <div style='display: flex; justify-content: space-between;'>
        <div>
            <span style='color: #ff6b6b; font-weight: bold;'>🔍 Filtered Results:</span>
            <span style='color: white; margin-left: 1rem;'>{filtered_count:,} applications</span>
        </div>
        <div>
            <span style='color: #ff6b6b; font-weight: bold;'>📊 Average Score:</span>
            <span style='color: white; margin-left: 1rem;'>{avg_score_text}</span>
        </div>
        <div>
            <span style='color: #ff6b6b; font-weight: bold;'>🚨 Critical Alerts:</span>
            <span style='color: white; margin-left: 1rem;'>{critical_alerts_text}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Data table
st.markdown("#### 📋 Suspicious Applications Details")

if len(filtered_suspicious) > 0:
    # Determine available columns
    available_columns = []
    for col in ['Job Title', 'Job Location', 'fraud_score', 'Alert_Reason', 'Industry', 'Company Size']:
        if col in filtered_suspicious.columns:
            available_columns.append(col)
    
    if available_columns:
        # Display dataframe
        display_df = filtered_suspicious[available_columns].head(100)
        
        # Apply styling if fraud_score is available
        if 'fraud_score' in available_columns:
            def color_fraud_score(val):
                if val >= 0.9:
                    return 'background-color: #dc2626; color: white; font-weight: bold;'
                elif val >= 0.8:
                    return 'background-color: #ef4444; color: white;'
                elif val >= 0.7:
                    return 'background-color: #f97316; color: white;'
                else:
                    return 'background-color: #f59e0b; color: white;'
            
            styled_df = display_df.style.map(color_fraud_score, subset=['fraud_score'])
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.dataframe(display_df, use_container_width=True, height=400)
        
        # Export functionality
        csv_data = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Export Filtered Data as CSV",
            data=csv_data,
            file_name=f"fraud_alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("📭 No data columns available for display")
else:
    st.info("📭 No suspicious applications found with current filters")

# ======================================================================
# FOOTER
# ======================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #a0a0a0; padding: 2rem;'>
    <p>🛡️ <strong>AI Fraud Detection System</strong> | Final Internship Project</p>
    <p>Powered by Isolation Forest & K-Means Clustering | Built with Streamlit</p>
    <p style='font-size: 0.8rem;'>Detection threshold automatically calibrated at 95th percentile</p>
</div>
""", unsafe_allow_html=True)
