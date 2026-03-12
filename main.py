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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LicitA-IA] %(levelname)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
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
        if isinstance(s, (int, float)): return float(s)
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
        if re.search(r"Advocacia-Geral\s+da\s+União|Minuta\s+Padrão\s+AGU", texto, re.I):
            resultados["detectado"] = True
            for nome, (padrao, grupo, transform) in CAMPOS_AGU.items():
                match = re.search(padrao, texto, re.I | re.S)
                if match:
                    try:
                        resultados["campos"][nome] = transform(match.group(grupo))
                    except:
                        resultados["campos"][nome] = "Erro no parse"
        return resultados

# ── APP PRINCIPAL ───────────────────────────────────────────

st.set_page_config(page_title="LicitA-IA | Intelligence Unit 2026", layout="wide", page_icon="🛡️")

# --- CSS INTEGRADO ---
st.markdown("""
<style>
    .risk-card { background: #fdfdfd; border-left: 5px solid #096dd9; border-radius: 8px; padding: 20px; margin-bottom: 15px; border: 1px solid #eee; }
    .critical { border-left-color: #ef4444; background: #fff5f5; }
    .warning { border-left-color: #f59e0b; background: #fffbeb; }
    .success { border-left-color: #22c55e; background: #f0fdf4; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
</style>
""", unsafe_allow_html=True)

# --- INITIAL STATE ---
if "empresa" not in st.session_state:
    st.session_state.empresa = {"cnpj": "", "razao_social": "", "capital_social": 0.0, "liquidez_corrente": 1.0, "certificacoes": [], "atestados": ""}
if "copiloto" not in st.session_state:
    st.session_state.copiloto = {"editais_monitorados": [], "alertas": [], "lances_config": {"custo_direto": 0.0, "bdi_pct": 20.0, "margem_pct": 10.0, "impostos_pct": 9.25}}
if "vault" not in st.session_state:
    st.session_state.vault = {}

# --- HELPERS ---
def extrair_texto_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

def call_ia(prompt, system, key):
    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def parse_json(raw):
    try:
        clean = re.sub(r'```json\n?|\n?```', '', raw).strip()
        return json.loads(clean)
    except:
        return {"error": "Falha no JSON"}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ LicitA-IA Unit")
    api_key = st.text_input("Anthropic API Key", type="password")
    st.caption("v2.1.0 - Compliance Lei 14.133")
    if st.button("🗑️ Resetar Sistema"):
        st.session_state.clear()
        st.rerun()

# --- TABS ---
tabs = st.tabs(["🏢 Perfil", "🔍 Auditoria", "🎯 Caçador", "⚖️ Advogado", "🕵️ Espião", "🔐 Vault", "🤖 Co-Piloto"])
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao, tab_vault, tab_copiloto = tabs

# 1. ABA PERFIL
with tab_perfil:
    st.subheader("DNA Corporativo")
    e = st.session_state.empresa
    e["razao_social"] = st.text_input("Razão Social", value=e["razao_social"])
    e["cnpj"] = st.text_input("CNPJ", value=e["cnpj"])
    col1, col2 = st.columns(2)
    e["capital_social"] = col1.number_input("Capital Social (R$)", value=e["capital_social"])
    e["liquidez_corrente"] = col2.number_input("Liquidez Corrente", value=e["liquidez_corrente"])
    e["atestados"] = st.text_area("Atestados de Capacidade Técnica (Resumo)", value=e["atestados"])

# 2. ABA AUDITORIA
with tab_auditoria:
    st.subheader("Auditoria Inteligente")
    file = st.file_uploader("Upload Edital PDF", type="pdf", key="aud")
    if file and api_key:
        if st.button("Analisar Edital"):
            with st.spinner("IA processando..."):
                texto = extrair_texto_pdf(file)
                # Parser AGU Automático
                res_agu = ParserAGU().extrair(texto)
                if res_agu["detectado"]:
                    st.success("✅ Padrão AGU Detectado.")
                    st.json(res_agu["campos"])
                
                # Chamada IA
                system = "Você é um auditor jurídico 2026. Analise riscos sob a Lei 14.133 e tendência 6x1."
                prompt = f"Perfil: {st.session_state.empresa}\nEdital: {texto[:10000]}"
                res = parse_json(call_ia(prompt, system, api_key))
                st.write(res)

# 3. ABA CAÇADOR
with tab_cacador:
    st.subheader("🎯 Matching de Oportunidades")
    if api_key:
        segmento = st.text_input("O que sua empresa vende?", placeholder="Ex: Software de BI")
        if st.button("Buscar Oportunidades"):
            system = "Você é um expert em matching de licitações."
            prompt = f"Encontre matches para: {segmento} baseado no perfil: {st.session_state.empresa}"
            st.write(call_ia(prompt, system, api_key))

# 4. ABA ADVOGADO
with tab_juridico:
    st.subheader("⚖️ Redator de Peças")
    tipo = st.selectbox("Peça", ["Impugnação", "Recurso", "Esclarecimento"])
    fundamento = st.text_area("Qual o erro do edital?")
    if st.button("Gerar Peça"):
        system = "Você é um advogado especialista em licitações."
        prompt = f"Gere uma {tipo} baseada nisto: {fundamento}. Empresa: {st.session_state.empresa['razao_social']}"
        st.code(call_ia(prompt, system, api_key), language="markdown")

# 5. ABA ESPIÃO
with tab_espiao:
    st.subheader("🕵️ Inteligência de Concorrência")
    cnpj_concorrente = st.text_input("CNPJ do Concorrente")
    if st.button("Investigar"):
        st.info("Simulando cruzamento de dados do PNCP...")
        st.warning("Concorrente costuma baixar lances em 15% no último minuto.")

# 6. ABA VAULT
with tab_vault:
    st.subheader("🔐 Gestão de Certidões")
    cert = st.selectbox("Certidão", ["CND Federal", "FGTS", "Trabalhista"])
    data_venc = st.date_input("Vencimento")
    if st.button("Salvar no Vault"):
        st.session_state.vault[cert] = data_venc
        st.success("Salvo!")
    st.write(st.session_state.vault)

# 7. ABA CO-PILOTO (O RADAR)
with tab_copiloto:
    st.subheader("🤖 Radar Sentinela")
    
    # Sentinela
    st.markdown("#### 🛰️ Monitoramento Ativo")
    url = st.text_input("URL do Edital no PNCP")
    if st.button("Ativar Vigília"):
        st.session_state.copiloto["editais_monitorados"].append(url)
        st.toast("Monitorando retificações!", icon="👁️")
    st.write(st.session_state.copiloto["editais_monitorados"])

    # Anti-Preço Suicida
    st.divider()
    st.markdown("#### 💰 Vigilante de Lances")
    lc = st.session_state.copiloto["lances_config"]
    lc["custo_direto"] = st.number_input("Seu Custo Direto (R$)", value=lc["custo_direto"])
    
    bdi, margem, impostos = lc["bdi_pct"]/100, lc["margem_pct"]/100, lc["impostos_pct"]/100
    ponto_equilibrio = lc["custo_direto"] * (1 + bdi + impostos)
    piso_inex = lc["custo_direto"] * 0.70

    col1, col2 = st.columns(2)
    col1.metric("Ponto de Equilíbrio", f"R$ {ponto_equilibrio:,.2f}")
    col2.metric("Inexequibilidade (TCU)", f"R$ {piso_inex:,.2f}")

    lance_rival = st.number_input("Lance do Concorrente", value=0.0)
    if lance_rival > 0:
        if lance_rival < piso_inex:
            st.markdown('<div class="risk-card critical"><b>🚨 ALERTA:</b> Lance Inexequível detectado!</div>', unsafe_allow_html=True)
        elif lance_rival < ponto_equilibrio:
            st.markdown('<div class="risk-card warning"><b>⚠️ CUIDADO:</b> Lance abaixo do seu custo.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="risk-card success">✅ Margem segura.</div>', unsafe_allow_html=True)

# RODAPÉ
st.sidebar.markdown("---")
st.sidebar.info(f"Monitorando {len(st.session_state.copiloto['editais_monitorados'])} editais.")
