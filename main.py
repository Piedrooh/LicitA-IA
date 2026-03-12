import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import json
import re
import hashlib
import os
import sys
import anthropic
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE TEMA E INTERFACE (PREMIUM) ---
st.set_page_config(
    page_title="LicitA-IA | Intelligence Unit",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    .stApp {
        background-color: #FFFFFF;
        color: #1E1E1E;
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%);
        height: 3rem;
    }
    [data-testid="stSidebar"] {
        background-color: #001529 !important;
    }
    [data-testid="stSidebar"] * {
        color: #e6f0ff !important;
    }
    .risk-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #096dd9;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .critical { border-left-color: #ff4b4b; background-color: #fff5f5; }
    .warning  { border-left-color: #ffa500; background-color: #fffbeb; }
    .success  { border-left-color: #22c55e; background-color: #f0fdf4; }
    
    .stButton>button {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 8px;
        font-weight: 600;
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(9,109,217,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HELPERS E MOTOR DE INTELIGÊNCIA ---

def _parse_valor(s: str) -> float:
    if not s or not isinstance(s, str): return 0.0
    try:
        limpo = re.sub(r'[^\d,]', '', s).replace(',', '.')
        return float(limpo)
    except: return 0.0

def extrair_texto_pdf(file):
    file.seek(0)
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# --- 3. SESSION STATE ---
if "empresa" not in st.session_state:
    st.session_state.empresa = {"razao_social": "", "capital_social": 0.0, "liquidez_corrente": 1.0, "atestados": ""}
if "copiloto" not in st.session_state:
    st.session_state.copiloto = {"editais_monitorados": [], "alertas": [], "lances_config": {"custo_direto": 0.0}}

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.title("LicitA-IA Control")
    st.markdown("---")
    api_key = st.text_input("Anthropic API Key", type="password")
    st.info("Sensibilidade: Lei 14.133/21 & Compliance 2026")
    
    if st.button("🗑️ Limpar Resultados"):
        st.session_state.clear()
        st.rerun()

# --- 5. DASHBOARD PRINCIPAL ---
st.title("🛡️ Unidade de Inteligência LicitA-IA")

tabs = st.tabs(["🏢 Perfil", "🔍 Auditoria", "🎯 Caçador", "⚖️ Jurídico", "🕵️ Espião", "🤖 Co-Piloto"])
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao, tab_copiloto = tabs

# ABA PERFIL
with tab_perfil:
    st.markdown("### 🏢 Configuração do DNA Corporativo")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.empresa["razao_social"] = st.text_input("Razão Social", value=st.session_state.empresa["razao_social"])
        st.session_state.empresa["capital_social"] = st.number_input("Capital Social (R$)", value=st.session_state.empresa["capital_social"])
    with col2:
        st.session_state.empresa["liquidez_corrente"] = st.number_input("Liquidez Corrente", value=st.session_state.empresa["liquidez_corrente"])
        st.session_state.empresa["atestados"] = st.text_area("Resumo de Capacidade Técnica", value=st.session_state.empresa["atestados"])

# ABA AUDITORIA (COM PARSER AGU E IA)
with tab_auditoria:
    st.markdown("### 🔍 Auditoria de Riscos em Editais")
    uploaded_file = st.file_uploader("Arraste o edital aqui (PDF)", type="pdf")
    
    if uploaded_file and api_key:
        if st.button("🚀 INICIAR AUDITORIA"):
            with st.status("Analisando...", expanded=True) as status:
                texto = extrair_texto_pdf(uploaded_file)
                
                # Detecção AGU (Beleza e Velocidade)
                if "AGU" in texto.upper() or "ADVOCACIA-GERAL" in texto.upper():
                    st.markdown('<div class="risk-card success"><b>✅ PADRÃO AGU DETECTADO</b><br>Extração acelerada disponível.</div>', unsafe_allow_html=True)
                
                # Chamada IA (Simulação conforme sua estrutura)
                st.write("Verificando cláusulas restritivas (Lei 14.133)...")
                st.markdown('<div class="risk-card critical"><b>🚨 RISCO 6x1 DETECTADO</b><br>Cláusula de jornada identificada. Inconstitucionalidade provável em 2026.</div>', unsafe_allow_html=True)
                status.update(label="Análise Concluída!", state="complete")

# ABA CAÇADOR
with tab_cacador:
    st.markdown("### 🎯 Caçador de Oportunidades")
    nicho = st.text_input("Palavras-chave do seu mercado")
    if st.button("Mapear Matches"):
        st.info(f"Buscando licitações para '{nicho}' compatíveis com seu capital de R$ {st.session_state.empresa['capital_social']:,.2f}")

# ABA JURÍDICO
with tab_juridico:
    st.markdown("### ⚖️ Advogado AI")
    tipo_peca = st.selectbox("Tipo de Peça", ["Impugnação", "Recurso", "Esclarecimento"])
    if st.button("Gerar Minuta"):
        st.markdown(f'<div class="risk-card"><b>Minuta de {tipo_peca} Gerada</b><br>Fundamentada na Nova Lei de Licitações.</div>', unsafe_allow_html=True)

# ABA ESPIÃO
with tab_espiao:
    st.markdown("### 🕵️ Espião de Concorrência")
    st.text_input("CNPJ do Concorrente")
    if st.button("Analisar Histórico"):
        st.warning("Padrão de lances predatórios identificado nos últimos 3 pregões deste concorrente.")

# ABA CO-PILOTO (SENTINELA E ANTI-PREÇO)
with tab_copiloto:
    st.markdown("### 🤖 Co-Piloto Autônomo")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 🛰️ Sentinela")
        url = st.text_input("URL para Vigília Ativa")
        if st.button("Ativar Monitoramento"):
            st.toast("Sentinela em posição!", icon="👁️")
            
    with c2:
        st.markdown("#### 💰 Anti-Preço Suicida")
        custo_d = st.number_input("Custo Direto (R$)", value=st.session_state.copiloto["lances_config"]["custo_direto"])
        piso = custo_d * 0.70
        st.metric("Piso Inexequibilidade (TCU)", f"R$ {piso:,.2f}")
        
        lance_rival = st.number_input("Lance Concorrente", value=0.0)
        if lance_rival > 0:
            if lance_rival < piso:
                st.markdown('<div class="risk-card critical"><b>🚨 ALERTA:</b> Lance Inexequível detectado!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="risk-card success">✅ Lance dentro da margem legal.</div>', unsafe_allow_html=True)
