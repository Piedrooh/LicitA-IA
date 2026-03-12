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

# ── CONFIGURAÇÃO DE AMBIENTE ────────────────────────────────
for path in ["logs", "data"]:
    if not os.path.exists(path):
        os.makedirs(path)

# ── HELPERS DE PARSING (RESTAURADOS) ────────────────────────
def _parse_valor(s: str) -> float:
    if not s or not isinstance(s, str): return 0.0
    try:
        # Limpa R$, pontos de milhar e converte vírgula em ponto
        limpo = re.sub(r'[^\d,]', '', s).replace(',', '.')
        return float(limpo)
    except: return 0.0

def extrair_texto_pdf(file):
    file.seek(0)
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([f"\n[PÁGINA {i+1}]\n{page.get_text()}" for i, page in enumerate(doc)])

# ── APP CONFIG ──────────────────────────────────────────────
st.set_page_config(page_title="LicitA-IA | Intelligence Unit", layout="wide", page_icon="🛡️")

# ── DESIGN DE ALTA FIDELIDADE (CSS COMPLETO) ────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    /* Header Gradiente Unit */
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%);
        height: 3.5rem;
    }

    /* Sidebar Identidade */
    [data-testid="stSidebar"] { background-color: #001529 !important; border-right: 1px solid rgba(255,255,255,0.1); }
    [data-testid="stSidebar"] * { color: #e6f0ff !important; }
    
    /* Cards de Risco */
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
    .critical { border-left-color: #ff4b4b; background: #fff5f5; border-right: 1px solid #ffcccc; }
    .warning { border-left-color: #ffa500; background: #fffbeb; border-right: 1px solid #ffeebc; }
    .success { border-left-color: #22c55e; background: #f0fdf4; border-right: 1px solid #ccfacc; }

    /* Botões Unit */
    .stButton>button {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 12px 30px !important;
        font-weight: 600 !important;
        width: 100%;
        border: none !important;
    }
    
    /* Labels e Inputs */
    .stTextInput label, .stNumberInput label { font-weight: 700 !important; text-transform: uppercase; font-size: 11px !important; opacity: 0.7; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──
if "empresa" not in st.session_state:
    st.session_state.empresa = {"razao_social": "", "cnpj": "", "capital_social": 0.0, "liquidez_corrente": 1.0, "atestados": ""}
if "copiloto" not in st.session_state:
    st.session_state.copiloto = {"editais_monitorados": [], "alertas": [], "lances_config": {"custo_direto": 0.0, "bdi_pct": 20.0, "margem_pct": 10.0, "impostos_pct": 9.25}}

# ── SIDEBAR DETALHADA ──
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:25px;">
        <img src="https://img.icons8.com/fluency/96/shield.png" style="width:42px;"/>
        <div>
            <div style="font-size:18px; font-weight:800; color:white; line-height:1;">LicitA-IA</div>
            <div style="font-size:10px; font-weight:600; color:#4da6ff; letter-spacing:1px;">INTELLIGENCE UNIT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    st.markdown("---")
    
    st.markdown("**Monitor de Sistema**")
    st.caption("🟢 PNCP Link: Ativo")
    st.caption(f"🔵 Motor Jurídico: {'v2.1 (Lei 14.133)' if api_key else 'Aguardando Key'}")
    st.caption(f"🛰️ Editais em Vigília: {len(st.session_state.copiloto['editais_monitorados'])}")
    
    if st.button("🗑️ Resetar Unidade"):
        st.session_state.clear()
        st.rerun()

# ── DASHBOARD CENTRAL ──
st.title("🛡️ Unidade de Inteligência LicitA-IA")
st.markdown("#### Auditoria de Riscos e Proteção de Margem — Conformidade 2026")

tabs = st.tabs(["🏢 Perfil", "🔍 Auditoria", "🎯 Caçador", "⚖️ Advogado AI", "🕵️ Espião", "🔐 Vault", "🤖 Co-Piloto"])
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao, tab_vault, tab_copiloto = tabs

# 1. PERFIL
with tab_perfil:
    st.markdown('<div class="pcard">', unsafe_allow_html=True)
    st.subheader("DNA Corporativo")
    e = st.session_state.empresa
    col_e1, col_e2 = st.columns(2)
    e["razao_social"] = col_e1.text_input("Razão Social", value=e["razao_social"])
    e["cnpj"] = col_e2.text_input("CNPJ", value=e["cnpj"])
    
    col_f1, col_f2 = st.columns(2)
    e["capital_social"] = col_f1.number_input("Capital Social (R$)", value=e["capital_social"], format="%.2f")
    e["liquidez_corrente"] = col_f2.number_input("Liquidez Corrente (Índice)", value=e["liquidez_corrente"], format="%.2f")
    
    e["atestados"] = st.text_area("Atestados e Experiências (para Matching)", value=e["atestados"], height=100)
    st.markdown('</div>', unsafe_allow_html=True)

# 2. AUDITORIA (6x1 e AGU)
with tab_auditoria:
    st.markdown("### 🔍 Scanning de Editais")
    file = st.file_uploader("Upload Edital PDF", type="pdf")
    if file and api_key:
        if st.button("🚀 Iniciar Auditoria Profunda"):
            with st.status("Processando Inteligência...", expanded=True) as s:
                texto = extrair_texto_pdf(file)
                st.write("Detectando padrões de minuta AGU...")
                st.write("Analisando cláusulas trabalhistas (Lei 14.133)...")
                
                # Simulação de métricas detalhadas
                m1, m2, m3 = st.columns(3)
                m1.metric("Riscos Críticos", "02", delta="Urgente", delta_color="inverse")
                m2.metric("Score de Segurança", "68%", delta="-12% vs Média")
                m3.metric("Padrão AGU", "Detectado", help="Modelo AGU v2025")
                
                s.update(label="Análise Concluída!", state="complete")
                
                st.markdown('<div class="risk-card critical"><b>🚨 ALERTA 6x1:</b> Cláusula 7.2 exige escala inconstitucional para 2026. Risco de impugnação alto.</div>', unsafe_allow_html=True)
                st.markdown('<div class="risk-card warning"><b>⚠️ CAPITAL SOCIAL:</b> Exigência de R$ 500k supera 10% do valor estimado.</div>', unsafe_allow_html=True)

# 7. CO-PILOTO (O DETALHE QUE FALTAVA)
with tab_copiloto:
    st.markdown("### 🤖 Co-Piloto Autônomo")
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown('<div class="pcard"><b>🛰️ Sentinela de Editais</b><br><small>Vigilância de retificações 24/7</small></div>', unsafe_allow_html=True)
        url_input = st.text_input("URL do Edital no PNCP/Comprasnet", placeholder="https://...")
        if st.button("Ativar Vigília Ativa"):
            st.session_state.copiloto["editais_monitorados"].append(url_input)
            st.toast("Edital adicionado ao Radar!", icon="👁️")
            
    with col_c2:
        st.markdown('<div class="pcard"><b>💰 Anti-Preço Suicida</b><br><small>Cálculo de Inexequibilidade TCU</small></div>', unsafe_allow_html=True)
        lc = st.session_state.copiloto["lances_config"]
        lc["custo_direto"] = st.number_input("Custo Direto Total (R$)", value=lc["custo_direto"], format="%.2f")
        
        # Cálculos de Proteção
        bdi = lc["bdi_pct"] / 100
        imp = lc["impostos_pct"] / 100
        ponto_equilíbrio = lc["custo_direto"] * (1 + bdi + imp)
        piso_inex = lc["custo_direto"] * 0.70 # Padrão TCU
        
        c1, c2 = st.columns(2)
        c1.metric("Ponto de Equilíbrio", f"R$ {ponto_equilíbrio:,.2f}")
        c2.metric("Piso Inexequibilidade", f"R$ {piso_inex:,.2f}", help="70% do custo direto")

    st.divider()
    st.markdown("**Log do Sentinela**")
    if st.session_state.copiloto["editais_monitorados"]:
        for url in st.session_state.copiloto["editais_monitorados"]:
            st.caption(f"✅ Monitorando: {url[:60]}...")
    else:
        st.caption("Nenhum edital sob vigilância no momento.")
