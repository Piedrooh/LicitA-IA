import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import json
import requests
import time
import anthropic

# --- 1. CONFIGURAÇÃO DE TEMA E INTERFACE ---
st.set_page_config(
    page_title="LicitA-IA | Intelligence Unit",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🛡️"
)

st.markdown("""
    <style>
    /* Fundo Absoluto e Clean */
    .stApp { background-color: #FFFFFF; color: #1E1E1E; }
    
    /* Header Premium */
    [data-testid="stHeader"] { 
        background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%); 
        height: 3rem; 
    }
    
    /* Abas Estilo Software Desktop */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent; border-radius: 6px 6px 0 0;
        padding: 10px 16px; font-weight: 600; color: #595959;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important;
        color: white !important;
    }

    /* Cards de Risco e Insights (Design Base Restaurado) */
    .risk-card {
        background-color: #f8f9fa; padding: 20px; border-radius: 12px;
        border-left: 6px solid #096dd9; margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #1E1E1E;
    }
    .critical { border-left-color: #ff4b4b; }
    .warning  { border-left-color: #ffa500; }
    .success  { border-left-color: #52c41a; }
    
    /* Certificações Visuais */
    .cert-card {
        background: linear-gradient(90deg, #f0f8ff 0%, #e6f7ff 100%);
        padding: 12px 18px; border-radius: 8px; margin-bottom: 10px;
        display: flex; align-items: center; border: 1px solid #bae0ff;
        color: #003a8c; font-weight: 600; font-size: 15px;
    }
    
    /* Botões de Conversão */
    .stButton>button {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%);
        color: white; border: none; padding: 12px 30px;
        border-radius: 8px; font-weight: 600; transition: 0.3s; width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,58,140,0.3); color: white;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. SESSION STATE ---
if 'empresa' not in st.session_state:
    st.session_state.empresa = {
        "cnpj": "", "razao_social": "", "capital_social": 0.0,
        "liquidez_corrente": 1.0, "certificacoes": [], "atestados": ""
    }

# --- 3. UTILITÁRIOS ---
def extrair_texto_pdf(file) -> str:
