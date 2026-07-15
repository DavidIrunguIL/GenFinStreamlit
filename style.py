import streamlit as st

def load_css():
    """Load all CSS styles including existing and new sidebar/header colors"""
    st.markdown("""
    <style>
    /* ===== EXISTING STYLES FROM YOUR CSS FILE ===== */
    .main, .stApp { background-color: #f4f6f9; padding: 20px; font-family: "Segoe UI", "Arial", sans-serif; color: #2c3e50; }
    h1, h2, h3 { color: #2c3e50; font-weight: 600; margin-bottom: 12px; }
    [data-testid="stMetric"] { background: #ffffff; padding: 18px 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; transition: transform 0.2s ease, box-shadow 0.2s ease; }
    [data-testid="stMetric"]:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
    [data-testid="stMetricLabel"] { color: #555; font-weight: 600; font-size: 14px; }
    [data-testid="stMetricValue"] { color: #1976d2; font-size: 22px; font-weight: bold; }
    hr { border: 0; height: 1px; background: #dfe6e9; margin: 20px 0; }
    .stDataFrame { background-color: #ffffff; border-radius: 10px; padding: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
    .stDataFrame th { background-color: #1976d2 !important; color: #fff !important; font-weight: bold !important; text-align: center !important; }
    .stDataFrame td { font-size: 14px; padding: 6px; }
    .stButton>button { background-color: #1976d2; color: white; border-radius: 8px; border: none; padding: 8px 16px; font-weight: 500; transition: background 0.2s ease; }
    .stButton>button:hover { background-color: #1565c0; cursor: pointer; }

    /* ===== NEW SIDEBAR STYLING ===== */
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
        border-right: 2px solid #1976d2;
    }
    [data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    [data-testid="stSidebar"] .stSelectbox, 
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stNumberInput { 
        background-color: rgba(52, 73, 94, 0.7) !important; 
        border: 1px solid #7f8c8d !important; 
    }
    [data-testid="stSidebar"] .stButton>button { background-color: #1976d2; color: white; }
    [data-testid="stSidebar"] .stButton>button:hover { background-color: #1565c0; }

    /* ===== NEW HEADER STYLING ===== */
    header[data-testid="stHeader"] { 
        background: linear-gradient(90deg, #1976d2 0%, #1565c0 100%) !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    header[data-testid="stHeader"] * { color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

