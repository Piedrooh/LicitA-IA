import streamlit as st
import anthropic
import requests
import fitz  # PyMuPDF
import json
import re
import hashlib
import logging
import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import pandas as pd

# ── CONFIGURAÇÃO DE AMBIENTE ────────────────────────────────
if not os.path.exists("logs"):
    os.makedirs("logs")

if not os.path.exists("data"):
    os.makedirs("data")

# Ajuste de Logging para Streamlit Cloud
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LicitA-IA] %(levelname)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
)
logger = logging.getLogger("LicitA-IA")

# ── HELPERS DE PARSING (FUNDAMENTAIS) ───────────────────────

def _parse_valor(s: str) -> float:
    """Converte 'R$ 1.234.567,89' → 1234567.89"""
    if not s or not isinstance(s, str): return 0.0
    try:
        limpo = re.sub(r'[^\d,]', '', s).replace(',', '.')
        return float(limpo)
    except (ValueError, AttributeError):
        return 0.0

def _parse_pct(s: str) -> float:
    """Converte '5,5' → 5.5"""
    if not s: return 0.0
    try:
        return float(str(s).replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0

# ── MÓDULO AGU_PARSER (DETERMINÍSTICO) ──────────────────────

CAMPOS_AGU = {
    "numero_edital": (r"Edital\s+(?:de\s+)?(?:Licitação\s+)?n[oº]?\s*([\d\./\-]+)", 1, str),
    "modalidade": (r"(Pregão\s+Eletrônico|Concorrência\s+Eletrônica|Dispensa\s+Eletrônica)", 1, str),
    "uasg": (r"UASG\s*[:\-]?\s*(\d{6})", 1, str),
    "valor_estimado": (r"[Vv]alor\s+(?:global\s+)?(?:estimado|total\s+estimado)[:\s]+R\$\s*([\d\.\,]+)", 1, _parse_valor),
    "data_abertura": (r"(?:Data\s+(?:abertura|sessão))[:\s]+(\d{2}/\d{2}/\d{4})", 1, str),
    "prazo_entrega": (r"[Pp]razo\s+(?:entrega|execução)[:\s]+(\d+)\s+dias?", 1, int),
    "garantia_pct": (r"[Gg]arantia.*?(\d+(?:[,\.]\d+)?)\s*%\s+", 1, _parse_pct),
    "multa_mora": (r"[Mm]ulta\s+morat.*?(\d+(?:[,\.]\d+)?)\s*%\s+", 1, _parse_pct),
}

class ParserAGU:
    def extrair(self, texto: str):
        resultados = {"detectado": False, "campos": {}, "alertas": []}
        # Detecção de padrão
        if re.search(r"Advocacia-Geral\s+da\s+União|Minuta\s+Padrão\s+AGU", texto, re.I):
            resultados["detectado"] = True
            for nome, (padrao, grupo, transform) in CAMPOS_AGU.items():
                match = re.search(padrao, texto, re.I | re.S)
                if match:
                    resultados["campos"][nome] = transform(match.group(grupo))
        return resultados

# ── APP PRINCIPAL ───────────────────────────────────────────

st.set_page_config(page_title="LicitA-IA | 2026 Edition", layout="wide", page_icon="🛡️")

# --- CSS INTEGRADO ---
st.markdown("""
<style>
    .risk-card { background: #f9f9f9; border-left: 5px solid #096dd9; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .critical { border-left-color: #ef4444; }
    .warning { border-left-color: #f59e0b; }
    .success { border-left-color: #22c55e; }
    .stMetric { background: #ffffff; border: 1px solid #eee; border-radius: 8px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if "empresa" not in st.session_state:
    st.session_state.empresa = {"razao_social": "", "capital_social": 0.0, "liquidez_corrente": 1.0, "certificacoes": []}
if "copiloto" not in st.session_state:
    st.session_state.copiloto = {"editais_monitorados": [], "alertas": [], "lances_config": {"custo_direto": 0.0, "bdi_pct": 20.0, "margem_pct": 10.0, "impostos_pct": 9.25}}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ LicitA-IA")
    api_key = st.text_input("Anthropic API Key", type="password")
    st.divider()
    if st.button("🗑️ Limpar Tudo"):
        st.session_state.clear()
        st.rerun()

# --- TABS ---
tab_perfil, tab_auditoria, tab_copiloto = st.tabs(["🏢 Perfil", "🔍 Auditoria", "🤖 Co-Piloto Autônomo"])

# ── ABA PERFIL ──
with tab_perfil:
    st.subheader("Configuração da Empresa")
    st.session_state.empresa["razao_social"] = st.text_input("Razão Social", value=st.session_state.empresa["razao_social"])
    st.session_state.empresa["capital_social"] = st.number_input("Capital Social (R$)", value=st.session_state.empresa["capital_social"])
    st.session_state.empresa["liquidez_corrente"] = st.number_input("Liquidez Corrente", value=st.session_state.empresa["liquidez_corrente"])

# ── ABA AUDITORIA ──
with tab_auditoria:
    st.subheader("Análise de Edital")
    file = st.file_uploader("Upload Edital PDF", type="pdf")
    if file and api_key:
        if st.button("Executar Auditoria"):
            # Extração de texto simplificada
            doc = fitz.open(stream=file.read(), filetype="pdf")
            texto_edital = "".join([page.get_text() for page in doc])
            
            # 1. Tenta AGU Parser primeiro (Grátis)
            parser = ParserAGU()
            res_agu = parser.extrair(texto_edital)
            
            if res_agu["detectado"]:
                st.success("✅ Padrão AGU Detectado! Extração determinística realizada.")
                st.json(res_agu["campos"])
            
            # 2. Chama Claude para Compliance 2026
            client = anthropic.Anthropic(api_key=api_key)
            prompt_auditoria = f"""
            Você é o Módulo de Compliance 2026 da LicitA-IA. Analise o edital sob a Lei 14.133/2021.
            FOCO 2026: Identifique se há jornada 6x1 (Risco Crítico) e barreiras de competitividade.
            Retorne APENAS JSON:
            {{ "score": 0-100, "riscos": [{{ "titulo": "", "severidade": "CRITICO|ATENCAO", "descricao": "" }}], "clausulas_6x1": true/false }}
            EDIVAL: {texto_edital[:10000]}
            """
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt_auditoria}]
            )
            st.write("### Análise de Risco IA")
            st.json(response.content[0].text)

# ── ABA CO-PILOTO (O CORAÇÃO DO SISTEMA) ──
with tab_copiloto:
    st.subheader("🤖 Co-Piloto Autônomo")
    
    # Módulo Sentinela Automático
    col1, col2 = st.columns([4, 1])
    with col1:
        nova_url = st.text_input("URL para Monitoramento Ativo (PNCP/Comprasnet)")
    with col2:
        if st.button("➕ Monitorar"):
            st.session_state.copiloto["editais_monitorados"].append(nova_url)
            st.toast("Edital em vigília!", icon="🛰️")

    # Módulo Anti-Preço Suicida
    st.divider()
    st.markdown("### 💰 Vigilante de Lances (Automático)")
    lc = st.session_state.copiloto["lances_config"]
    
    # Cálculos Automáticos
    bdi = lc["bdi_pct"] / 100
    margem = lc["margem_pct"] / 100
    impostos = lc["impostos_pct"] / 100
    custo_total = lc["custo_direto"] * (1 + bdi + impostos)
    piso_inex = lc["custo_direto"] * 0.70
    
    st.write(f"**Seu custo mínimo viável:** R$ {custo_total:,.2f} | **Piso Inexequibilidade (TCU):** R$ {piso_inex:,.2f}")
    
    lance_atual = st.number_input("Lance Atual na Sala (Simulação API)", value=0.0)
    
    if lance_atual > 0:
        if lance_atual < piso_inex:
            st.error(f"🚨 ALERTA: Lance de R$ {lance_atual:,.2f} é INEXEQUÍVEL! Prepare o recurso.")
        elif lance_atual < custo_total:
            st.warning(f"⚠️ ATENÇÃO: Lance abaixo do seu custo mínimo (R$ {custo_total:,.2f}). Recuar é sugerido.")
        else:
            st.success("✅ Margem de segurança preservada.")

# Rodapé de Status
st.sidebar.markdown("---")
st.sidebar.caption(f"Status: {'🟢 Online' if api_key else '🔴 Offline'}")
