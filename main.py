import streamlit as st
import anthropic
import requests
import fitz  # PyMuPDF
import json

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="LicitA-IA | Intelligence Unit",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS GLOBAL ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Reset & Base ─────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
/* Herda o background do tema Streamlit — sem sobrescrever */
[data-testid="stHeader"] {
    background: linear-gradient(90deg, #001529 0%, #003a8c 60%, #096dd9 100%);
    height: 48px;
}
[data-testid="stSidebar"] { display: none; }

/* ── Tabs ─────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background: transparent;
    border-bottom: none;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    border-radius: 0;
    padding: 14px 20px;
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text-color);
    opacity: 0.6;
    transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #096dd9;
    opacity: 1;
    background: rgba(9,109,217,0.06);
}
.stTabs [aria-selected="true"] {
    color: #096dd9 !important;
    opacity: 1 !important;
    border-bottom: 3px solid #096dd9 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"]    { display: none; }

/* ── Cards ────────────────────────────────────────────── */
.pcard {
    background: var(--secondary-background-color);
    border-radius: 12px;
    border: 1px solid rgba(128,128,128,0.15);
    padding: 28px 32px;
    margin-bottom: 20px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.pcard-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-color);
    letter-spacing: 0.01em;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Field Labels ─────────────────────────────────────── */
.stTextInput label, .stNumberInput label,
.stTextArea label, .stSelectbox label,
.stMultiSelect label {
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--text-color) !important;
    opacity: 0.6;
    margin-bottom: 6px !important;
}

/* ── Inputs — deixa o Streamlit controlar fundo/texto,
      só personaliza borda e foco ──────────────────────── */
.stTextInput input,
.stNumberInput input {
    border: 1.5px solid rgba(128,128,128,0.25) !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: border 0.2s !important;
}
.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: #096dd9 !important;
    box-shadow: 0 0 0 3px rgba(9,109,217,0.12) !important;
}
.stTextArea textarea {
    border: 1.5px solid rgba(128,128,128,0.25) !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    transition: border 0.2s !important;
}
.stTextArea textarea:focus {
    border-color: #096dd9 !important;
    box-shadow: 0 0 0 3px rgba(9,109,217,0.12) !important;
}

/* ── Buttons ──────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1d6ff2 0%, #003a8c 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    padding: 10px 22px !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(9,109,217,0.25) !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(9,109,217,0.35) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Certification Pills (sempre azuis — marca) ───────── */
.cert-pill-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 4px;
}
.cert-pill {
    background: linear-gradient(135deg, #1d6ff2 0%, #003a8c 100%);
    color: #ffffff;
    font-size: 12.5px;
    font-weight: 600;
    padding: 7px 16px;
    border-radius: 20px;
    letter-spacing: 0.03em;
    box-shadow: 0 2px 6px rgba(9,109,217,0.2);
}
.cert-pill-empty {
    font-size: 13px;
    font-style: italic;
    padding: 6px 0;
    color: var(--text-color);
    opacity: 0.4;
}

/* ── Multiselect Tags (sempre azuis — marca) ──────────── */
.stMultiSelect [data-baseweb="tag"] {
    background: linear-gradient(135deg, #1d6ff2 0%, #003a8c 100%) !important;
    border-radius: 20px !important;
    padding: 2px 12px !important;
}
.stMultiSelect [data-baseweb="tag"] span { color: #fff !important; }
.stMultiSelect [data-baseweb="tag"] button svg { fill: #fff !important; }

/* ── Risk Cards ───────────────────────────────────────── */
.risk-card {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.15);
    border-left: 5px solid #096dd9;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.risk-card.critical { border-left-color: #ef4444; }
.risk-card.warning  { border-left-color: #f59e0b; }
.risk-card.success  { border-left-color: #22c55e; }
.risk-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.risk-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 8px;
}
.risk-body {
    font-size: 13.5px;
    color: var(--text-color);
    opacity: 0.75;
    line-height: 1.6;
}

/* ── Metrics ──────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 10px;
    padding: 18px 20px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
[data-testid="metric-container"] label {
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: var(--text-color) !important;
    opacity: 0.55;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: var(--text-color) !important;
}

/* ── Alerts ───────────────────────────────────────────── */
.stAlert { border-radius: 10px !important; font-size: 13.5px !important; }

/* ── Divider ──────────────────────────────────────────── */
hr { border-color: rgba(128,128,128,0.15) !important; margin: 20px 0 !important; }

/* ── Page header ──────────────────────────────────────── */
.page-header { margin-bottom: 24px; }
.page-header h2 {
    font-size: 22px;
    font-weight: 700;
    color: var(--text-color);
    margin: 0 0 4px 0;
}
.page-header p {
    font-size: 14px;
    color: var(--text-color);
    opacity: 0.55;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)


# --- 3. SESSION STATE ---
def init_state():
    defaults = {
        "empresa": {
            "cnpj": "", "razao_social": "", "capital_social": 0.0,
            "liquidez_corrente": 1.0, "certificacoes": [], "atestados": ""
        },
        "resultado_auditoria": None,
        "resultado_cacador":   None,
        "resultado_juridico":  None,
        "resultado_espiao":    None,
        "dados_concorrente":   None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# --- 4. HELPERS ---

def extrair_texto_pdf(file, max_chars: int = 80_000) -> str:
    file.seek(0)
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
    except Exception as e:
        st.error(f"Erro ao processar PDF: {e}")
        st.stop()
    texto = ""
    for i in range(len(doc)):
        texto += f"\n[PÁGINA {i+1}]\n{doc[i].get_text()}"
        if len(texto) >= max_chars:
            texto += "\n[... texto truncado ...]"
            break
    return texto


def get_claude(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def chamar_claude(client, system: str, user: str, max_tokens: int = 2048) -> str:
    try:
        r = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return r.content[0].text
    except anthropic.AuthenticationError:
        st.error("API Key inválida. Verifique na sidebar.")
        st.stop()
    except anthropic.RateLimitError:
        st.error("Limite de requisições atingido. Aguarde e tente novamente.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao chamar Claude: {e}")
        st.stop()


def parse_json(raw: str):
    try:
        clean = raw.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        st.error("Erro ao interpretar a resposta da IA. Tente novamente.")
        st.stop()


def perfil_str() -> str:
    e = st.session_state.empresa
    return (
        f"Razão Social: {e['razao_social']}\n"
        f"CNPJ: {e['cnpj']}\n"
        f"Capital Social: R$ {e['capital_social']:,.2f}\n"
        f"Liquidez Corrente: {e['liquidez_corrente']}\n"
        f"Certificações: {', '.join(e['certificacoes']) if e['certificacoes'] else 'Nenhuma'}"
    )


def risk_card(titulo: str, label: str, corpo: str, tipo: str = ""):
    cor_label = {"critical": "#ef4444", "warning": "#f59e0b",
                 "success": "#22c55e"}.get(tipo, "#096dd9")
    st.markdown(f"""
    <div class="risk-card {tipo}">
        <div class="risk-label" style="color:{cor_label};">{label}</div>
        <div class="risk-title">{titulo}</div>
        <div class="risk-body">{corpo.replace(chr(10), '<br>')}</div>
    </div>""", unsafe_allow_html=True)


def section(icon: str, title: str):
    st.markdown(f"""
    <div class="pcard-title"><span>{icon}</span> {title}</div>
    """, unsafe_allow_html=True)


# --- 5. HEADER ---
st.markdown("""
<div style="background:var(--secondary-background-color);
            border-bottom:1px solid rgba(128,128,128,0.15);
            padding:16px 32px; margin-bottom:8px;
            box-shadow:0 1px 4px rgba(0,0,0,0.06);
            display:flex; align-items:center; gap:12px;">
    <span style="font-size:20px;">🛡️</span>
    <div>
        <div style="font-size:17px; font-weight:700; color:#096dd9; line-height:1.2;">
            LicitA-IA: Intelligence Unit
        </div>
        <div style="font-size:12px; color:var(--text-color); opacity:0.45; font-weight:500;">
            Auditoria, Matching e Espionagem Competitiva em Tempo Real.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- API KEY (discreta, no topo direito) ---
api_col1, api_col2 = st.columns([4, 1])
with api_col2:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input("API Key", type="password", placeholder="sk-ant-...")
        if api_key:
            st.success("Motor ativo")
    else:
        st.success("Motor ativo")

# --- 6. ABAS ---
tabs = st.tabs([
    "🏢 Perfil da Empresa",
    "🔍 Auditoria de Editais",
    "🎯 Caçador (Matching)",
    "⚖️ Advogado AI",
    "🕵️ Espião de Concorrência",
    "🔐 The Vault (Certidões)",
])
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao, tab_vault = tabs


# ══════════════════════════════════════════
# ABA 1 — PERFIL DA EMPRESA
# ══════════════════════════════════════════
with tab_perfil:
    st.markdown("""
    <div class="page-header">
        <h2>🏢 Perfil da Empresa</h2>
        <p>Configure o DNA corporativo da sua empresa para auditorias personalizadas.</p>
    </div>""", unsafe_allow_html=True)

    # Card CNPJ
    st.markdown('<div class="pcard">', unsafe_allow_html=True)
    st.markdown("**Pesquisa Rápida por CNPJ**")
    cc1, cc2 = st.columns([4, 1])
    with cc1:
        cnpj_input = st.text_input(
            "CNPJ", label_visibility="collapsed",
            value=st.session_state.empresa["cnpj"],
            placeholder="00.000.000/0000-00"
        )
    with cc2:
        if st.button("Pesquisar CNPJ"):
            cnpj_limpo = "".join(filter(str.isdigit, cnpj_input))
            if len(cnpj_limpo) == 14:
                with st.spinner("Consultando Receita Federal..."):
                    try:
                        resp = requests.get(
                            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}",
                            timeout=10
                        )
                        if resp.status_code == 200:
                            dados = resp.json()
                            st.session_state.empresa.update({
                                "cnpj":          cnpj_limpo,
                                "razao_social":  dados.get("razao_social", ""),
                                "capital_social": float(dados.get("capital_social") or 0.0),
                            })
                            st.success(f"Empresa encontrada: {dados.get('razao_social')}")
                            st.rerun()
                        else:
                            st.error("CNPJ não encontrado.")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
            else:
                st.warning("Digite um CNPJ com 14 dígitos.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Card Dados
    st.markdown('<div class="pcard">', unsafe_allow_html=True)
    section("🏛️", "Verifique e Complete as Informações")
    f1, f2 = st.columns(2)
    with f1:
        razao = st.text_input("Razão Social",
                              value=st.session_state.empresa["razao_social"])
    with f2:
        capital = st.number_input("Capital Social Registrado (R$)",
                                  value=float(st.session_state.empresa["capital_social"]),
                                  min_value=0.0, step=1000.0, format="%.2f")

    f3, f4 = st.columns(2)
    with f3:
        liquidez = st.number_input("Índice de Liquidez Corrente",
                                   value=float(st.session_state.empresa["liquidez_corrente"]),
                                   min_value=0.0, step=0.1, format="%.2f")
    with f4:
        st.write("")  # espaço intencional

    # Certificações
    st.markdown("**CERTIFICAÇÕES ATIVAS**", help="Selecione todas as certificações vigentes da empresa")
    certif = st.multiselect(
        "Certificações", label_visibility="collapsed",
        options=["ISO 9001", "ISO 14001", "ISO 27001", "SASSMAQ", "PBQP-H", "OHSAS 18001"],
        default=st.session_state.empresa["certificacoes"]
    )

    # Pills de preview
    if certif:
        pills_html = '<div class="cert-pill-wrap">' + \
                     "".join(f'<span class="cert-pill">{c}</span>' for c in certif) + \
                     '</div>'
        st.markdown(pills_html, unsafe_allow_html=True)
    else:
        st.markdown('<div class="cert-pill-wrap"><span class="cert-pill-empty">Nenhuma certificação selecionada</span></div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    atestados = st.text_area(
        "Atestados e Contratos Relevantes",
        value=st.session_state.empresa.get("atestados", ""),
        placeholder="Ex: Fornecimento de EPI para Petrobras (2022-2024), contrato de R$ 1,2M...",
        height=110
    )

    if st.button("💾 Salvar e Validar Cadastro"):
        st.session_state.empresa.update({
            "cnpj":              "".join(filter(str.isdigit, cnpj_input)),
            "razao_social":      razao,
            "capital_social":    capital,
            "liquidez_corrente": liquidez,
            "certificacoes":     certif,
            "atestados":         atestados,
        })
        st.success("✅ Perfil salvo com sucesso! O motor de auditoria está calibrado.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
# ABA 2 — AUDITORIA DE EDITAIS
# ══════════════════════════════════════════
with tab_auditoria:
    st.markdown("""
    <div class="page-header">
        <h2>🔍 Auditoria de Editais</h2>
        <p>Identifique cláusulas abusivas, riscos de desclassificação e pegadinhas jurídicas.</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.empresa["razao_social"]:
        st.warning("Configure o Perfil da Empresa antes de auditar.")
    elif not api_key:
        st.warning("Insira sua API Key para ativar o motor de IA.")
    else:
        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        section("📄", "Upload do Edital")
        edital_file = st.file_uploader("Faça upload do edital em PDF",
                                       type="pdf", key="auditoria",
                                       label_visibility="collapsed")
        if edital_file:
            st.caption(f"Arquivo: {edital_file.name} • {edital_file.size/1024:.0f} KB")
            if st.button("Executar Auditoria Completa"):
                with st.status("Auditando com Claude...", expanded=True) as status:
                    st.write("Extraindo texto do edital...")
                    texto = extrair_texto_pdf(edital_file)
                    st.write(f"Analisando {len(texto):,} caracteres...")

                    client = get_claude(api_key)
                    system = """Você é um auditor sênior especialista na Lei 14.133/2021 e Lei 8.666/93.
Identifique TODAS as cláusulas que podem desclassificar ou prejudicar o licitante.
Responda APENAS com JSON válido, sem markdown:
{
  "riscos": [{
    "severidade": "CRITICO|ATENCAO|INFO",
    "categoria": "string",
    "pagina": "string",
    "titulo": "string",
    "descricao": "string",
    "acao": "string"
  }],
  "resumo": "string",
  "score_seguranca": 0
}"""
                    user = f"PERFIL:\n{perfil_str()}\n\nEDITAL:\n{texto}"
                    raw  = chamar_claude(client, system, user, max_tokens=4096)
                    st.session_state.resultado_auditoria = parse_json(raw)
                    status.update(label="Auditoria concluída!", state="complete", expanded=False)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.resultado_auditoria:
            res      = st.session_state.resultado_auditoria
            riscos   = res.get("riscos", [])
            score    = res.get("score_seguranca", 0)
            criticos = [r for r in riscos if r["severidade"] == "CRITICO"]
            atencoes = [r for r in riscos if r["severidade"] == "ATENCAO"]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Score de Segurança", f"{score}/100")
            m2.metric("Riscos Críticos",    len(criticos))
            m3.metric("Atenções",           len(atencoes))
            m4.metric("Total",              len(riscos))

            st.markdown("<br>", unsafe_allow_html=True)
            risk_card("Avaliação Geral", "RESUMO EXECUTIVO", res.get("resumo", ""))

            ordem = {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}
            for r in sorted(riscos, key=lambda x: ordem.get(x["severidade"], 3)):
                tipo  = "critical" if r["severidade"] == "CRITICO" else \
                        "warning"  if r["severidade"] == "ATENCAO"  else ""
                corpo = f"{r['descricao']}<br><br><b>Plano de Ação:</b> {r.get('acao','N/A')}"
                risk_card(
                    r["titulo"],
                    f"{r['severidade']} · {r.get('pagina','?')} · {r.get('categoria','')}",
                    corpo, tipo
                )


# ══════════════════════════════════════════
# ABA 3 — CAÇADOR (MATCHING)
# ══════════════════════════════════════════
with tab_cacador:
    st.markdown("""
    <div class="page-header">
        <h2>🎯 Caçador (Matching)</h2>
        <p>Mapeamento inteligente de oportunidades compatíveis com seu perfil.</p>
    </div>""", unsafe_allow_html=True)

    if not api_key:
        st.warning("Insira sua API Key para ativar o Caçador.")
    else:
        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        section("🔎", "Critérios de Busca")
        c1, c2 = st.columns(2)
        with c1:
            segmento = st.text_input("Segmento / Objeto",
                                     placeholder="Ex: fornecimento de uniformes, limpeza predial...")
            uf = st.selectbox("Estado", ["Todos","SP","RJ","MG","RS","PR","SC","BA",
                                         "GO","DF","PE","CE","AM","PA","MT","MS","ES",
                                         "RN","PB","AL","SE","PI","MA","TO","RO","AC","AP","RR"])
        with c2:
            v_min = st.number_input("Valor Mínimo (R$)", value=0.0, step=10000.0, format="%.2f")
            v_max = st.number_input("Valor Máximo (R$)", value=1_000_000.0, step=10000.0, format="%.2f")
            modal = st.multiselect("Modalidades", ["Pregão Eletrônico","Concorrência",
                                                   "Tomada de Preços","Convite","RDC"],
                                   default=["Pregão Eletrônico"])

        atst = st.text_area("Atestados e Experiências",
                            value=st.session_state.empresa.get("atestados",""),
                            placeholder="Ex: Fornecimento de 5.000 uniformes para Prefeitura de SP...",
                            height=90)
        if st.button("Ativar Caçador de Oportunidades"):
            with st.spinner("Mapeando oportunidades..."):
                client = get_claude(api_key)
                system = """Você é especialista em prospecção de licitações públicas no Brasil.
Responda SOMENTE com JSON válido:
{
  "compatibilidade_geral": 0,
  "analise": "string",
  "oportunidades": [{
    "titulo":"string","orgao_exemplo":"string","valor_estimado":"string",
    "compatibilidade":0,"pontos_fortes":["string"],"pontos_fracos":["string"],
    "proximos_passos":"string"
  }],
  "recomendacoes": ["string"]
}"""
                user = (f"PERFIL:\n{perfil_str()}\nAtestados: {atst}\n\n"
                        f"Segmento: {segmento}, Estado: {uf}, "
                        f"Valor: R${v_min:,.0f}-R${v_max:,.0f}, Modalidades: {', '.join(modal)}")
                st.session_state.resultado_cacador = parse_json(
                    chamar_claude(client, system, user, max_tokens=3000)
                )
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.resultado_cacador:
            res  = st.session_state.resultado_cacador
            opps = res.get("oportunidades", [])
            c1, c2 = st.columns(2)
            c1.metric("Compatibilidade Geral",  f"{res.get('compatibilidade_geral',0)}%")
            c2.metric("Oportunidades Mapeadas", len(opps))
            risk_card("Análise Estratégica", "DIAGNÓSTICO DE POTENCIAL", res.get("analise",""))
            for opp in sorted(opps, key=lambda x: x.get("compatibilidade",0), reverse=True):
                comp  = opp.get("compatibilidade", 0)
                tipo  = "success" if comp>=70 else ("warning" if comp>=40 else "critical")
                corpo = (f"<b>Órgão:</b> {opp.get('orgao_exemplo','N/A')}<br>"
                         f"<b>Valor:</b> {opp.get('valor_estimado','N/A')}<br>"
                         f"<b>Pontos Fortes:</b> {', '.join(opp.get('pontos_fortes',[]))}<br>"
                         f"<b>Pontos Fracos:</b> {', '.join(opp.get('pontos_fracos',[]))}<br>"
                         f"<b>Próximos Passos:</b> {opp.get('proximos_passos','N/A')}")
                risk_card(opp["titulo"], f"MATCH: {comp}%", corpo, tipo)
            st.markdown("**Recomendações Estratégicas**")
            for rec in res.get("recomendacoes", []):
                st.markdown(f"- {rec}")


# ══════════════════════════════════════════
# ABA 4 — ADVOGADO AI
# ══════════════════════════════════════════
with tab_juridico:
    st.markdown("""
    <div class="page-header">
        <h2>⚖️ Advogado AI</h2>
        <p>Redação automática de peças jurídicas fundamentadas na Lei 14.133/2021.</p>
    </div>""", unsafe_allow_html=True)

    if not api_key:
        st.warning("Insira sua API Key para usar o Advogado AI.")
    else:
        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        section("📝", "Configuração da Peça")
        tipo_peca = st.selectbox("Tipo de Peça", [
            "Impugnação de Edital",
            "Recurso Administrativo (pós-julgamento)",
            "Pedido de Esclarecimento",
            "Contrarrazões de Recurso",
            "Impugnação de Habilitação de Concorrente",
        ])
        j1, j2 = st.columns(2)
        with j1:
            orgao       = st.text_input("Órgão / Entidade Licitante",
                                        placeholder="Ex: Prefeitura Municipal de Campinas")
            num_edital  = st.text_input("Número do Edital",
                                        placeholder="Ex: Pregão Eletrônico 001/2025")
        with j2:
            objeto      = st.text_input("Objeto da Licitação",
                                        placeholder="Ex: Aquisição de uniformes profissionais")
            data_sessao = st.text_input("Data da Sessão / Prazo",
                                        placeholder="Ex: 20/01/2025")
        fundamento = st.text_area("Fundamento / O que deseja contestar",
                                  placeholder=(
                                      "Ex: O edital exige ISO 9001 no item 9.4.1 como requisito "
                                      "de habilitação técnica. Esta exigência restringe a "
                                      "competitividade sem justificativa, ferindo o Art. 9º da Lei 14.133..."
                                  ), height=140)
        if st.button("Redigir Peça Jurídica"):
            if not fundamento or not orgao:
                st.warning("Preencha ao menos o Órgão e o Fundamento.")
            else:
                with st.spinner(f"Redigindo {tipo_peca}..."):
                    client = get_claude(api_key)
                    system = """Você é advogado especialista em Direito Administrativo e Licitações com 20 anos de experiência.
Redija peças jurídicas formais fundamentadas na Lei 14.133/2021, Lei 8.666/93, jurisprudência do TCU.
Inclua: cabeçalho, qualificação das partes, dos fatos, fundamentos jurídicos com artigos e súmulas, pedido e fechamento."""
                    user = (f"Peça: {tipo_peca}\nEmpresa:\n{perfil_str()}\n\n"
                            f"Órgão: {orgao}\nEdital: {num_edital}\nObjeto: {objeto}\n"
                            f"Data: {data_sessao}\n\nFundamento:\n{fundamento}")
                    peca = chamar_claude(client, system, user, max_tokens=4096)
                    st.session_state.resultado_juridico = {"tipo": tipo_peca, "texto": peca}
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.resultado_juridico:
            res = st.session_state.resultado_juridico
            st.markdown(f"**{res['tipo']}**")
            st.markdown(
                f"<div style='background:var(--secondary-background-color); "
                f"border:1px solid rgba(128,128,128,0.15); border-radius:10px; "
                f"padding:32px; white-space:pre-wrap; font-family:Georgia,serif; "
                f"font-size:14px; line-height:1.9; color:var(--text-color);'>{res['texto']}</div>",
                unsafe_allow_html=True
            )
            st.download_button("⬇️ Baixar Peça (.txt)", data=res["texto"],
                               file_name=f"{tipo_peca.replace(' ','_').lower()}.txt",
                               mime="text/plain")


# ══════════════════════════════════════════
# ABA 5 — ESPIÃO DE CONCORRÊNCIA
# ══════════════════════════════════════════
with tab_espiao:
    st.markdown("""
    <div class="page-header">
        <h2>🕵️ Espião de Concorrência</h2>
        <p>Inteligência competitiva para identificar padrões e estratégias dos seus concorrentes.</p>
    </div>""", unsafe_allow_html=True)

    if not api_key:
        st.warning("Insira sua API Key para usar o Espião.")
    else:
        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        section("🔎", "Identificação do Concorrente")
        e1, e2 = st.columns([3, 1])
        with e1:
            cnpj_conc = st.text_input("CNPJ do Concorrente",
                                      placeholder="00.000.000/0000-00",
                                      label_visibility="collapsed")
        with e2:
            if st.button("Pesquisar Concorrente"):
                cnpj_c = "".join(filter(str.isdigit, cnpj_conc))
                if len(cnpj_c) == 14:
                    with st.spinner("Consultando..."):
                        try:
                            resp = requests.get(
                                f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_c}", timeout=10
                            )
                            if resp.status_code == 200:
                                st.session_state["dados_concorrente"] = resp.json()
                                st.rerun()
                            else:
                                st.error("CNPJ não encontrado.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
                else:
                    st.warning("CNPJ inválido.")

        if st.session_state["dados_concorrente"]:
            d = st.session_state["dados_concorrente"]
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("Razão Social",  d.get("razao_social","N/A")[:22]+"…" if len(d.get("razao_social",""))>22 else d.get("razao_social","N/A"))
            cc2.metric("Capital Social", f"R$ {float(d.get('capital_social') or 0):,.0f}")
            cc3.metric("Porte",          d.get("porte","N/A"))
            cc4.metric("Situação",       d.get("descricao_situacao_cadastral","N/A"))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        section("📋", "Inteligência Competitiva")
        historico = st.text_area("Histórico e comportamento do concorrente",
                                 placeholder=(
                                     "Ex: A empresa costuma praticar desconto de 15-20% no lance final. "
                                     "Ganhou os pregões 001/2024 e 005/2024 da Prefeitura de SP..."
                                 ), height=130)
        seg_esp = st.text_input("Segmento da disputa",
                                placeholder="Ex: Fornecimento de EPI, Limpeza Predial...")
        if st.button("Gerar Dossiê Competitivo"):
            if not historico:
                st.warning("Descreva o comportamento do concorrente.")
            else:
                with st.spinner("Montando dossiê..."):
                    client = get_claude(api_key)
                    d = st.session_state.get("dados_concorrente") or {}
                    dados_str = (
                        f"Razão Social: {d.get('razao_social','N/A')}\n"
                        f"Capital: R$ {float(d.get('capital_social') or 0):,.2f}\n"
                        f"Porte: {d.get('porte','N/A')}"
                    ) if d else "Dados não carregados."
                    system = """Você é estrategista de inteligência competitiva em licitações.
Responda SOMENTE com JSON válido:
{
  "perfil_competitivo":"string",
  "pontos_vulneraveis":["string"],
  "estrategias_vencer":[{"estrategia":"string","descricao":"string","risco":"BAIXO|MEDIO|ALTO"}],
  "alerta_dumping": false,
  "preco_referencia":"string",
  "recomendacao_final":"string"
}"""
                    user = (f"MINHA EMPRESA:\n{perfil_str()}\n\n"
                            f"CONCORRENTE:\n{dados_str}\n\nHistórico: {historico}\nSegmento: {seg_esp}")
                    st.session_state.resultado_espiao = parse_json(
                        chamar_claude(client, system, user, max_tokens=3000)
                    )
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.resultado_espiao:
            res = st.session_state.resultado_espiao
            if res.get("alerta_dumping"):
                risk_card("Risco de Dumping Detectado",
                          "ALERTA ESTRATÉGICO",
                          "Padrão de preços predatórios identificado. Prepare impugnação preventiva.",
                          "critical")
            risk_card("Perfil Competitivo", "DOSSIÊ DO CONCORRENTE",
                      res.get("perfil_competitivo",""))
            st.metric("Estimativa de Preço do Concorrente", res.get("preco_referencia","N/A"))
            for est in res.get("estrategias_vencer", []):
                risco = est.get("risco","BAIXO")
                tipo  = "critical" if risco=="ALTO" else ("warning" if risco=="MEDIO" else "success")
                risk_card(est["estrategia"], f"ESTRATÉGIA · RISCO {risco}",
                          est.get("descricao",""), tipo)
            st.markdown("**Pontos Vulneráveis do Concorrente**")
            for p in res.get("pontos_vulneraveis",[]):
                st.markdown(f"- {p}")
            risk_card("Recomendação Executiva", "PLANO FINAL",
                      res.get("recomendacao_final",""), "success")


# ══════════════════════════════════════════
# ABA 6 — THE VAULT (CERTIDÕES)
# ══════════════════════════════════════════
with tab_vault:
    st.markdown("""
    <div class="page-header">
        <h2>🔐 The Vault — Gestão de Certidões</h2>
        <p>Controle os vencimentos das certidões da sua empresa e receba alertas de renovação.</p>
    </div>""", unsafe_allow_html=True)

    if not api_key:
        st.warning("Insira sua API Key para usar o Vault.")
    else:
        CERTIDOES = [
            "CND Federal (Receita Federal + PGFN)",
            "CND Estadual",
            "CND Municipal",
            "CRF — FGTS (Caixa Econômica)",
            "CNDT — Débitos Trabalhistas (TST)",
            "Certidão de Falência e Concordata",
            "Balanço Patrimonial",
            "Registro no CREA / CRM / CRC (se aplicável)",
        ]

        if "vault" not in st.session_state:
            st.session_state.vault = {c: {"validade": "", "status": "Não cadastrada"} for c in CERTIDOES}

        st.markdown('<div class="pcard">', unsafe_allow_html=True)
        section("🗂️", "Painel de Certidões")

        v1, v2, v3 = st.columns(3)
        ok     = sum(1 for v in st.session_state.vault.values() if v["status"] == "Válida")
        alerta = sum(1 for v in st.session_state.vault.values() if v["status"] == "Vencendo")
        venc   = sum(1 for v in st.session_state.vault.values() if v["status"] == "Vencida")
        v1.metric("Certidões Válidas",   ok)
        v2.metric("Vencendo em Breve",   alerta)
        v3.metric("Vencidas / Ausentes", venc + sum(1 for v in st.session_state.vault.values() if v["status"] == "Não cadastrada"))

        st.markdown("<br>", unsafe_allow_html=True)

        for cert in CERTIDOES:
            dados = st.session_state.vault[cert]
            cor   = {"Válida":"#22c55e","Vencendo":"#f59e0b","Vencida":"#ef4444"}.get(dados["status"],"#94a3b8")
            with st.expander(f"{cert}  —  **{dados['status']}**"):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    nova_val = st.text_input("Validade (DD/MM/AAAA)",
                                             value=dados["validade"],
                                             key=f"vault_val_{cert}")
                with col_b:
                    novo_status = st.selectbox("Status", ["Não cadastrada","Válida","Vencendo","Vencida"],
                                               index=["Não cadastrada","Válida","Vencendo","Vencida"].index(dados["status"]),
                                               key=f"vault_st_{cert}")
                with col_c:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Salvar", key=f"vault_save_{cert}"):
                        st.session_state.vault[cert] = {"validade": nova_val, "status": novo_status}
                        st.success("Salvo!")
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Analisar Certidões com IA"):
            with st.spinner("Analisando situação documental..."):
                client  = get_claude(api_key)
                resumo  = "\n".join(f"- {c}: {v['status']} (validade: {v['validade'] or 'N/A'})"
                                    for c, v in st.session_state.vault.items())
                system  = "Você é especialista em habilitação jurídica em licitações públicas."
                user    = (f"Analise as certidões da empresa {st.session_state.empresa['razao_social']} "
                           f"e indique riscos de inabilitação, urgências de renovação e boas práticas:\n{resumo}")
                analise = chamar_claude(client, system, user, max_tokens=1500)
                risk_card("Análise Documental", "DIAGNÓSTICO DO VAULT", analise)

        st.markdown('</div>', unsafe_allow_html=True)
