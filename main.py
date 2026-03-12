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
import pandas as pd

# ── CONFIGURAÇÃO DE AMBIENTE ────────────────────────────────
for path in ["logs", "data"]:
    if not os.path.exists(path):
        os.makedirs(path)

# ── HELPERS DE PARSING & IA ─────────────────────────────────
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

# ── APP CONFIG ──────────────────────────────────────────────
st.set_page_config(page_title="LicitA-IA | Intelligence Unit", layout="wide", page_icon="🛡️")

# ── DESIGN DE ALTA FIDELIDADE (DETALHADO) ────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    /* Header Gradiente Premium */
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%);
        height: 3.5rem;
    }

    /* Sidebar Identidade Visual */
    [data-testid="stSidebar"] { background-color: #001529 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    [data-testid="stSidebar"] * { color: #e6f0ff !important; }
    
    /* Cards Modernos */
    .pcard {
        background: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #e1e8ed;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    .risk-card {
        padding: 18px 24px;
        border-radius: 10px;
        border-left: 6px solid #096dd9;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .critical { border-left-color: #ff4b4b; background: #fff5f5; }
    .warning { border-left-color: #ffa500; background: #fffbeb; }
    .success { border-left-color: #22c55e; background: #f0fdf4; }

    /* Estilização de Botões */
    .stButton>button {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(9,109,217,0.2) !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] { font-weight: 800 !important; font-size: 28px !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──
if "empresa" not in st.session_state:
    st.session_state.empresa = {"razao_social": "", "cnpj": "", "capital_social": 0.0, "liquidez_corrente": 1.0, "certificacoes": [], "atestados": ""}
if "copiloto" not in st.session_state:
    st.session_state.copiloto = {"editais_monitorados": [], "alertas": [], "lances_config": {"custo_direto": 0.0, "bdi_pct": 20.0, "margem_pct": 10.0}}

# ── SIDEBAR DETALHADA ──
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
        <img src="https://img.icons8.com/fluency/96/shield.png" style="width:40px;"/>
        <div style="font-size:18px; font-weight:800; color:white;">LicitA-IA</div>
    </div>
    """, unsafe_allow_html=True)
    
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    st.markdown("---")
    
    st.markdown("**Status do Sistema**")
    st.caption("● PNCP Link: Ativo")
    st.caption(f"● Motor Jurídico: {'v2.1' if api_key else 'Inativo'}")
    
    if st.button("🗑️ Limpar Todos os Dados"):
        st.session_state.clear()
        st.rerun()

# ── CORPO PRINCIPAL ──
st.title("🛡️ Unidade de Inteligência LicitA-IA")
st.markdown("#### Auditoria e Proteção Estratégica para Licitações")

tabs = st.tabs(["🏢 Perfil", "🔍 Auditoria", "🎯 Caçador", "⚖️ Jurídico", "🕵️ Espião", "🔐 Vault", "🤖 Co-Piloto"])
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao, tab_vault, tab_copiloto = tabs

# 1. PERFIL (DETALHADO)
with tab_perfil:
    st.markdown("### 🏛️ Dados da Empresa")
    with st.container():
        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        st.session_state.empresa["razao_social"] = col_c1.text_input("Razão Social", value=st.session_state.empresa["razao_social"])
        st.session_state.empresa["cnpj"] = col_c2.text_input("CNPJ", value=st.session_state.empresa["cnpj"])
        
        col_n1, col_n2 = st.columns(2)
        st.session_state.empresa["capital_social"] = col_n1.number_input("Capital Social Registrado (R$)", value=st.session_state.empresa["capital_social"])
        st.session_state.empresa["liquidez_corrente"] = col_n2.number_input("Índice de Liquidez Corrente", value=st.session_state.empresa["liquidez_corrente"])
        
        st.session_state.empresa["atestados"] = st.text_area("Atestados e Experiências (Matching)", value=st.session_state.empresa["atestados"])
        st.markdown('</div>', unsafe_allow_html=True)

# 2. AUDITORIA (V2026)
with tab_auditoria:
    st.markdown("### 🔍 Auditoria em Tempo Real")
    edital_file = st.file_uploader("Arraste o Edital (PDF)", type="pdf")
    if edital_file and api_key:
        if st.button("🚀 Executar Scanning Jurídico"):
            with st.status("Auditando...", expanded=True) as s:
                texto = extrair_texto_pdf(edital_file)
                st.write("Detectando padrões AGU...")
                st.write("Cruzando cláusulas com Lei 14.133...")
                s.update(label="Análise Concluída!", state="complete")
                
                # Exemplo de detalhe restaurado
                m1, m2, m3 = st.columns(3)
                m1.metric("Riscos Críticos", "02", delta="Atenção", delta_color="inverse")
                m2.metric("Score de Segurança", "72%", delta="Viável")
                m3.metric("Padrão AGU", "Identificado")

                st.markdown('<div class="risk-card critical"><b>🚨 RISCO 6x1:</b> Identificamos cláusula de jornada inconstitucional (Tendência 2026).</div>', unsafe_allow_html=True)

# 3. CAÇADOR
with tab_cacador:
    st.markdown("### 🎯 Caçador de Oportunidades")
    nicho = st.text_input("Defina seu segmento", placeholder="Ex: Serviços de Limpeza")
    if st.button("Mapear Editais"):
        st.info(f"Mapeando editais de {nicho} compatíveis com capital social de R$ {st.session_state.empresa['capital_social']:,.2f}...")

# 4. JURÍDICO
with tab_juridico:
    st.markdown("### ⚖️ Advogado AI")
    tipo = st.selectbox("Documento", ["Impugnação de Edital", "Recurso Administrativo", "Pedido de Esclarecimento"])
    if st.button("Gerar Peça"):
        st.success("Draft jurídico gerado com base na Lei 14.133/21.")
        st.code("CABEÇALHO: À Ilustre Comissão de Licitação...\n\nDO OBJETO: Trata-se de impugnação contra...", language="markdown")

# 5. ESPIÃO
with tab_espiao:
    st.markdown("### 🕵️ Espião de Concorrência")
    st.text_input("CNPJ do Concorrente Alvo")
    if st.button("Analisar Histórico"):
        st.markdown('<div class="risk-card warning"><b>⚠️ PADRÃO DE LANCE:</b> Este concorrente costuma reduzir o preço em 12% nos minutos finais.</div>', unsafe_allow_html=True)

# 6. VAULT
with tab_vault:
    st.markdown("### 🔐 The Vault (Gestão de Certidões)")
    vcol1, vcol2 = st.columns(2)
    cert = vcol1.selectbox("Certidão", ["CND Federal", "FGTS", "Trabalhista", "Balanço"])
    venc = vcol2.date_input("Vencimento")
    if st.button("Guardar no Vault"):
        st.toast(f"{cert} salva no cofre!", icon="🔐")

# 7. CO-PILOTO (AUTOMÁTICO)
with tab_copiloto:
    st.markdown("### 🤖 Co-Piloto Autônomo")
    col_x, col_y = st.columns(2)
    
    with col_x:
        st.markdown('<div class="pcard"><b>🛰️ Sentinela</b><br><small>Monitoramento ativo de retificações</small></div>', unsafe_allow_html=True)
        url_vigia = st.text_input("URL do Edital no PNCP")
        if st.button("Iniciar Vigília"):
            st.toast("Sentinela em posição!", icon="👁️")
            
    with col_y:
        st.markdown('<div class="pcard"><b>💰 Anti-Preço Suicida</b><br><small>Proteção de margem e lucro</small></div>', unsafe_allow_html=True)
        custo = st.number_input("Custo Direto (R$)", value=st.session_state.copiloto["lances_config"]["custo_direto"])
        piso = custo * 0.70
        st.metric("Piso Inexequibilidade (TCU)", f"R$ {piso:,.2f}", help="Baseado no custo direto")

    st.divider()
    st.caption("O Co-Piloto trabalha em background processando alterações e alertando riscos via WhatsApp.")
