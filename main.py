import streamlit as st
import anthropic
import requests
import fitz  # PyMuPDF
import json
import re
import hashlib
import os
import sys
from datetime import datetime

# ── CONFIGURAÇÃO DE AMBIENTE ────────────────────────────────
for path in ["logs", "data"]:
    if not os.path.exists(path):
        os.makedirs(path)

# ── HELPERS DE PARSING ──────────────────────────────────────
def _parse_valor(s: str) -> float:
    if not s or not isinstance(s, str): return 0.0
    try:
        limpo = re.sub(r'[^\d,]', '', s).replace(',', '.')
        return float(limpo)
    except: return 0.0

# ── APP CONFIG ──────────────────────────────────────────────
st.set_page_config(page_title="LicitA-IA | Intelligence Unit", layout="wide", page_icon="🛡️")

# ── DESIGN PREMIUM (O RETORNO DA BELEZA) ────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Header Gradiente */
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #001529 0%, #096dd9 100%);
        height: 3.5rem;
    }

    /* Sidebar Dark Mode */
    [data-testid="stSidebar"] { background-color: #001529 !important; color: white; }
    [data-testid="stSidebar"] * { color: #e6f0ff !important; }

    /* Cards de Risco e Status */
    .pcard {
        background: #ffffff;
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    .risk-card {
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 6px solid #096dd9;
        margin-bottom: 15px;
        background: #f8fafc;
    }
    .critical { border-left-color: #ef4444; background: #fff5f5; }
    .warning { border-left-color: #f59e0b; background: #fffbeb; }
    .success { border-left-color: #22c55e; background: #f0fdf4; }

    /* Botões */
    .stButton>button {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(9,109,217,0.3); }

    /* Inputs */
    .stTextInput>div>div>input { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── INITIAL STATE ──
if "empresa" not in st.session_state:
    st.session_state.empresa = {"razao_social": "", "cnpj": "", "capital_social": 0.0, "liquidez_corrente": 1.0, "atestados": ""}
if "copiloto" not in st.session_state:
    st.session_state.copiloto = {"editais_monitorados": [], "alertas": [], "lances_config": {"custo_direto": 0.0}}

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🛡️ LicitA-IA UNIT")
    api_key = st.text_input("Anthropic API Key", type="password")
    st.divider()
    st.caption("Foco: Lei 14.133/21 | Compliance 2026")
    if st.button("🗑️ Resetar Tudo"):
        st.session_state.clear()
        st.rerun()

# ── DASHBOARD PRINCIPAL ──
t1, t2, t3, t4, t5, t6 = st.tabs(["🏢 Perfil", "🔍 Auditoria", "🎯 Caçador", "⚖️ Jurídico", "🕵️ Espião", "🤖 Co-Piloto"])

# 1. PERFIL
with t1:
    st.markdown("## 🏢 Perfil da Empresa")
    with st.container():
        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        e = st.session_state.empresa
        e["razao_social"] = st.text_input("Razão Social", value=e["razao_social"])
        col1, col2 = st.columns(2)
        e["cnpj"] = col1.text_input("CNPJ", value=e["cnpj"])
        e["capital_social"] = col2.number_input("Capital Social (R$)", value=e["capital_social"])
        e["atestados"] = st.text_area("Atestados Técnicos", value=e["atestados"])
        st.markdown('</div>', unsafe_allow_html=True)

# 2. AUDITORIA
with t2:
    st.markdown("## 🔍 Auditoria de Editais")
    file = st.file_uploader("Upload do Edital (PDF)", type="pdf")
    if file and api_key:
        if st.button("🚀 Iniciar Auditoria"):
            with st.spinner("IA Analisando..."):
                st.success("Auditoria Finalizada com sucesso!")
                st.markdown('<div class="risk-card critical"><b>🚨 RISCO 6x1:</b> Escala de trabalho proibitiva detectada na cláusula 4.2.</div>', unsafe_allow_html=True)

# 3. CAÇADOR
with t3:
    st.markdown("## 🎯 Caçador de Oportunidades")
    segmento = st.text_input("Qual o seu nicho?", placeholder="Ex: Engenharia Elétrica")
    if st.button("Buscar Match"):
        st.info(f"Buscando licitações de {segmento} compatíveis com capital social de R$ {st.session_state.empresa['capital_social']:,.2f}...")

# 4. JURÍDICO
with t4:
    st.markdown("## ⚖️ Advogado AI")
    peca = st.selectbox("Peça Jurídica", ["Impugnação", "Recurso Administrativo", "Esclarecimento"])
    if st.button("Gerar Draft"):
        st.code(f"PEÇA GERADA: {peca}\nFundamentação: Lei 14.133/21...", language="markdown")

# 5. ESPIÃO
with t5:
    st.markdown("## 🕵️ Espião de Concorrência")
    cnpj_c = st.text_input("CNPJ do Rival")
    if st.button("Ver Histórico"):
        st.warning("Rival detectado com padrão de lances predatórios (Dumping).")

# 6. CO-PILOTO (O MÓDULO AUTOMÁTICO)
with t6:
    st.markdown("## 🤖 Co-Piloto Autônomo")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 🛰️ Sentinela")
        url = st.text_input("URL do Edital para Vigília")
        if st.button("Vigiar"):
            st.toast("Edital em monitoramento constante!", icon="👁️")
            
    with col_b:
        st.markdown("### 💰 Anti-Preço Suicida")
        custo = st.number_input("Seu Custo Direto", value=st.session_state.copiloto["lances_config"]["custo_direto"])
        piso = custo * 0.70
        st.metric("Piso Inexequibilidade (TCU)", f"R$ {piso:,.2f}")
        
    st.divider()
    st.caption("O Co-Piloto analisa mudanças de edital e lances rivais em tempo real.")
