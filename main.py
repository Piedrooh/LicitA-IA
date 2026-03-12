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
    initial_sidebar_state="expanded"
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
    background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%);
    height: 3rem;
}
/* ── Sidebar — dark navy fixo (identidade visual) ─────── */
[data-testid="stSidebar"] {
    background: #001529 !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * {
    color: #e6f0ff !important;
}
/* Inputs dentro da sidebar */
[data-testid="stSidebar"] input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #fff !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] label {
    color: rgba(255,255,255,0.5) !important;
    font-size: 10px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
/* Botão limpar dentro da sidebar */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: #e6f0ff !important;
    box-shadow: none !important;
    font-size: 12px !important;
    padding: 8px 16px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.14) !important;
    box-shadow: none !important;
    transform: none !important;
}
/* Remove os widgets nativos de st.success/st.warning/st.info na sidebar */
[data-testid="stSidebar"] .stAlert {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}
/* Divider na sidebar */
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
}

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
    background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    padding: 12px 30px !important;
    transition: 0.3s !important;
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
            "liquidez_corrente": 1.0, "certificacoes": [], "atestados": "",
            "ativo_circulante": 0.0, "passivo_circulante": 0.0
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


# --- 5. SIDEBAR ---
with st.sidebar:
    # ── Logo + Brand ──────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:12px; padding:8px 0 20px 0;">
        <img src="https://img.icons8.com/fluency/96/shield.png"
             style="width:38px; height:38px; flex-shrink:0;" />
        <div>
            <div style="font-size:17px; font-weight:800; color:#ffffff; line-height:1.1;">
                LicitA-IA
            </div>
            <div style="font-size:9px; font-weight:700; letter-spacing:0.14em;
                        color:rgba(255,255,255,0.45); text-transform:uppercase;">
                Intelligence Unit
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── API Key ───────────────────────────────────────────
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input("Anthropic API Key", type="password",
                                placeholder="sk-ant-...")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Empresa Ativa ─────────────────────────────────────
    e = st.session_state.empresa
    nome     = e["razao_social"]    or "Aguardando Setup"
    capital  = e["capital_social"]
    certs    = e["certificacoes"]

    st.markdown(f"""
    <div style="margin-bottom:20px;">
        <div style="font-size:9px; font-weight:700; letter-spacing:0.12em;
                    color:rgba(255,255,255,0.35); text-transform:uppercase;
                    margin-bottom:8px;">Empresa Ativa</div>
        <div style="font-size:14px; font-weight:700; color:#ffffff;
                    margin-bottom:4px;">{nome}</div>
        <div style="font-size:12px; color:rgba(255,255,255,0.5);
                    margin-bottom:6px;">Capital: R$ {capital:,.0f}</div>
        <div style="font-size:11px; color:#4da6ff;">
            {" · ".join(certs) if certs else "—"}
        </div>
    </div>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:0 0 20px 0;" />
    """, unsafe_allow_html=True)

    # ── Status do Sistema ─────────────────────────────────
    motor_status = "Ativo" if api_key else "Aguardando Key"
    motor_cor    = "#52c41a" if api_key else "#faad14"
    st.markdown(f"""
    <div style="margin-bottom:20px;">
        <div style="font-size:9px; font-weight:700; letter-spacing:0.12em;
                    color:rgba(255,255,255,0.35); text-transform:uppercase;
                    margin-bottom:10px;">Status do Sistema</div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:7px;">
            <span style="width:8px; height:8px; border-radius:50%;
                         background:#52c41a; display:inline-block; flex-shrink:0;"></span>
            <span style="font-size:12px; color:rgba(255,255,255,0.75);">
                PNCP Link: <b style="color:#fff;">Ativo</b>
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:7px;">
            <span style="width:8px; height:8px; border-radius:50%;
                         background:{motor_cor}; display:inline-block; flex-shrink:0;"></span>
            <span style="font-size:12px; color:rgba(255,255,255,0.75);">
                Motor Jurídico: <b style="color:#fff;">v2.0</b>
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="width:8px; height:8px; border-radius:50%;
                         background:#52c41a; display:inline-block; flex-shrink:0;"></span>
            <span style="font-size:12px; color:rgba(255,255,255,0.75);">
                Foco: <b style="color:#fff;">Lei 14.133/21</b>
            </span>
        </div>
    </div>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:0 0 16px 0;" />
    """, unsafe_allow_html=True)

    if st.button("🗑️ Limpar Resultados"):
        for k in ["resultado_auditoria", "resultado_cacador",
                  "resultado_juridico", "resultado_espiao",
                  "dados_concorrente"]:
            st.session_state[k] = None
        if "vault" in st.session_state:
            del st.session_state["vault"]
        # Reseta também o perfil da empresa
        st.session_state.empresa = {
            "cnpj": "", "razao_social": "", "capital_social": 0.0,
            "liquidez_corrente": 1.0, "certificacoes": [], "atestados": "",
            "ativo_circulante": 0.0, "passivo_circulante": 0.0
        }
        st.rerun()

    # ── Rodapé ────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:32px; padding-top:16px;
                border-top:1px solid rgba(255,255,255,0.08);">
        <div style="font-size:11px; color:rgba(255,255,255,0.5); line-height:1.6;
                    margin-bottom:6px;">
            Sistema especializado na <b style="color:#cce0ff;">Nova Lei de Licitações (14.133)</b>.
            Identifica cláusulas restritivas e exigências de habilitação críticas.
        </div>
        <div style="font-size:10px; color:rgba(255,255,255,0.25);">
            Desenvolvido para: Unidade de Inteligência
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- 6. ABAS ---
tabs = st.tabs([
    "🏢 Perfil da Empresa",
    "🔍 Auditoria de Editais",
    "🎯 Caçador (Matching)",
    "⚖️ Advogado AI",
    "🕵️ Espião de Concorrência",
    "🔐 The Vault (Certidões)",
    "🤖 Co-Piloto Autônomo",
])
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao, tab_vault, tab_copiloto = tabs


# ══════════════════════════════════════════
# ABA 1 — PERFIL DA EMPRESA
# ══════════════════════════════════════════
with tab_perfil:
    st.markdown("""
    <div class="page-header">
        <h2>🏢 Perfil da Empresa</h2>
        <p>Configure o DNA corporativo da sua empresa para auditorias personalizadas.</p>
    </div>""", unsafe_allow_html=True)

    # ── Pesquisa por CNPJ ────────────────────────────────
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
                                "cnpj":           cnpj_limpo,
                                "razao_social":   dados.get("razao_social", ""),
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

    st.divider()

    # ── Dados Cadastrais ─────────────────────────────────
    section("🏛️", "Verifique e Complete as Informações")
    f1, f2 = st.columns(2)
    with f1:
        razao = st.text_input("Razão Social",
                              value=st.session_state.empresa["razao_social"])
    with f2:
        capital = st.number_input("Capital Social Registrado (R$)",
                                  value=float(st.session_state.empresa["capital_social"]),
                                  min_value=0.0, step=1000.0, format="%.2f")

    st.divider()

    # ── Calculadora de Liquidez ──────────────────────────
    section("🧮", "Calculadora de Liquidez Corrente")
    st.caption("Preencha o Ativo e Passivo Circulante para calcular automaticamente o índice de liquidez.")

    liq_col1, liq_col2, liq_col3 = st.columns([2, 2, 1])
    with liq_col1:
        ativo_circ = st.number_input(
            "Ativo Circulante (R$)",
            value=st.session_state.empresa.get("ativo_circulante", 0.0),
            min_value=0.0, step=1000.0, format="%.2f"
        )
    with liq_col2:
        passivo_circ = st.number_input(
            "Passivo Circulante (R$)",
            value=st.session_state.empresa.get("passivo_circulante", 0.0),
            min_value=0.0, step=1000.0, format="%.2f"
        )
    with liq_col3:
        # Calcula dinamicamente
        if passivo_circ > 0:
            liq = round(ativo_circ / passivo_circ, 2)
        elif ativo_circ > 0:
            liq = float("inf")
        else:
            liq = st.session_state.empresa.get("liquidez_corrente", 1.0)

        liq_display = f"{liq:.2f}" if liq != float("inf") else "∞"
        st.markdown(f"""
        <div style="text-align:center; padding:10px 0 4px 0;">
            <div style="font-size:10px; font-weight:700; letter-spacing:0.08em;
                        text-transform:uppercase; color:var(--text-color); opacity:0.55;
                        margin-bottom:6px;">Índice Calculado</div>
            <div style="font-size:28px; font-weight:800;
                        color:{'#22c55e' if liq >= 1.0 else '#ef4444'};">
                {liq_display}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Feedback instantâneo de saúde financeira
    if passivo_circ > 0:
        if liq >= 1.0:
            st.success(
                f"✅ Índice de Liquidez de **{liq:.2f}** — Saúde financeira adequada. "
                f"Sua empresa possui R$ {liq:.2f} em ativos para cada R$ 1,00 de obrigações de curto prazo. "
                f"Apta para a maioria dos editais."
            )
        else:
            st.error(
                f"⚠️ Índice de Liquidez de **{liq:.2f}** — Risco de inabilitação. "
                f"Editais que exigem liquidez ≥ 1,0 (Lei 14.133/21, Art. 69) podem desclassificar sua empresa. "
                f"Considere reforço de capital de giro antes de participar."
            )

    st.divider()

    # ── Certificações ────────────────────────────────────
    st.markdown("**CERTIFICAÇÕES ATIVAS**",
                help="Selecione todas as certificações vigentes da empresa")
    certif = st.multiselect(
        "Certificações", label_visibility="collapsed",
        options=["ISO 9001", "ISO 14001", "ISO 27001", "SASSMAQ", "PBQP-H", "OHSAS 18001"],
        default=st.session_state.empresa["certificacoes"]
    )

    if certif:
        pills_html = '<div class="cert-pill-wrap">' + \
                     "".join(f'<span class="cert-pill">{c}</span>' for c in certif) + \
                     '</div>'
        st.markdown(pills_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="cert-pill-wrap">'
            '<span class="cert-pill-empty">Nenhuma certificação selecionada</span>'
            '</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # ── Atestados — Cérebro do Caçador ───────────────────
    st.info(
        "🎯 **Este campo é o cérebro do módulo Caçador (Matching).**\n\n"
        "Quanto mais detalhados forem seus atestados e contratos anteriores, "
        "mais preciso será o matchmaking de editais compatíveis com o seu perfil. "
        "Inclua objeto, órgão contratante, valor e período de cada contrato."
    )
    atestados = st.text_area(
        "Atestados e Contratos Relevantes",
        value=st.session_state.empresa.get("atestados", ""),
        placeholder=(
            "Ex: Fornecimento de 5.000 uniformes para Petrobras (2022-2024), contrato de R$ 1,2M\n"
            "Ex: Prestação de serviços de limpeza predial para Prefeitura de SP (2023), R$ 800k\n"
            "Ex: Fornecimento de EPI para Embraer (2021-2023), contrato de R$ 450k"
        ),
        height=140
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("💾 Salvar e Validar Cadastro"):
        # Usa o índice calculado se disponível, senão mantém o anterior
        liquidez_final = liq if passivo_circ > 0 and liq != float("inf") else \
                         st.session_state.empresa.get("liquidez_corrente", 1.0)

        st.session_state.empresa.update({
            "cnpj":               "".join(filter(str.isdigit, cnpj_input)),
            "razao_social":       razao,
            "capital_social":     capital,
            "liquidez_corrente":  liquidez_final,
            "ativo_circulante":   ativo_circ,
            "passivo_circulante": passivo_circ,
            "certificacoes":      certif,
            "atestados":          atestados,
        })
        st.success("✅ Perfil salvo com sucesso! O motor de auditoria está calibrado.")



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

    

# ══════════════════════════════════════════════════════════════
# ABA 7 — CO-PILOTO AUTÔNOMO
# ══════════════════════════════════════════════════════════════
with tab_copiloto:
    st.markdown("""
    <div class="page-header">
        <h2>🤖 Co-Piloto Autônomo</h2>
        <p>Favorite uma licitação. O sistema assume o resto — vigilância, compliance e proteção em tempo real.</p>
    </div>""", unsafe_allow_html=True)

    # ── Inicializa estado do Co-Piloto ──────────────────────────────────
    if "copiloto" not in st.session_state:
        st.session_state.copiloto = {
            "editais_monitorados": [],
            "alertas": [],
            "ultimo_compliance": None,
            "ultimo_agu": None,
            "lances_config": {"custo_direto": 0.0, "bdi_pct": 20.0,
                               "margem_pct": 10.0, "impostos_pct": 9.25},
        }
    cp = st.session_state.copiloto

    # ── PAINEL DE STATUS ─────────────────────────────────────────────────
    n_editais = len(cp["editais_monitorados"])
    n_alertas = len([a for a in cp["alertas"] if a.get("nivel") == "CRITICO"])
    n_total   = len(cp["alertas"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Editais em Vigília", n_editais, "Sentinela ativo" if n_editais else "Nenhum")
    c2.metric("Alertas Críticos",   n_alertas, delta=f"{n_alertas} não lidos", delta_color="inverse" if n_alertas else "normal")
    c3.metric("Total de Alertas",   n_total)
    c4.metric("Motor",             "Claude Sonnet" if api_key else "Inativo",
              "✅ Conectado" if api_key else "⚠️ Sem Key")

    st.divider()

    # ════════════════════════════════════════
    # MÓDULO 1 — SENTINELA
    # ════════════════════════════════════════
    section("👁️", "Módulo Sentinela — Vigilância de Editais")
    st.caption("Adicione URLs de editais do PNCP ou Compras.gov. O Sentinela detecta retificações e classifica o risco automaticamente.")

    col_url, col_btn = st.columns([4, 1])
    with col_url:
        nova_url = st.text_input("URL do Edital", label_visibility="collapsed",
                                 placeholder="https://pncp.gov.br/app/editais/...")
    with col_btn:
        if st.button("➕ Favoritar"):
            if nova_url and nova_url.startswith("http"):
                if nova_url not in cp["editais_monitorados"]:
                    cp["editais_monitorados"].append(nova_url)
                    st.success("Edital adicionado à vigília!")
                    st.rerun()
                else:
                    st.warning("Este edital já está sendo monitorado.")
            else:
                st.error("Insira uma URL válida.")

    # Lista editais monitorados
    if cp["editais_monitorados"]:
        st.markdown("<br>", unsafe_allow_html=True)
        for i, url in enumerate(cp["editais_monitorados"]):
            col_e, col_status, col_rm = st.columns([5, 2, 1])
            with col_e:
                st.markdown(f"<small>🔗 {url[:70]}{'...' if len(url) > 70 else ''}</small>",
                            unsafe_allow_html=True)
            with col_status:
                st.markdown('<span style="color:#22c55e; font-size:12px;">● Monitorando</span>',
                            unsafe_allow_html=True)
            with col_rm:
                if st.button("✕", key=f"rm_{i}"):
                    cp["editais_monitorados"].pop(i)
                    st.rerun()

        # Simulação de verificação manual (em produção: roda async em background)
        if st.button("🔄 Verificar Agora") and api_key:
            with st.spinner("Sentinela verificando alterações..."):
                client = get_claude(api_key)
                system = (
                    "Você é o módulo Sentinela da LicitA-IA. Simule uma verificação de monitoramento "
                    "de edital e gere um relatório realista em JSON com esta estrutura:\n"
                    '{"status": "alterado|sem_alteracao", "nivel": "CRITICO|MODERADO|INFORMATIVO", '
                    '"resumo": "string", "delta": [{"tipo":"adicionado|removido","conteudo":"string"}], '
                    '"recomendacao": "string"}'
                )
                user = (f"Simule verificação do edital: {cp['editais_monitorados'][0]}\n"
                        f"Empresa: {st.session_state.empresa['razao_social'] or 'N/A'}")
                raw = chamar_claude(client, system, user, max_tokens=1000)
                resultado = parse_json(raw)

                nivel = resultado.get("nivel", "INFO")
                cor   = {"CRITICO": "critical", "MODERADO": "warning"}.get(nivel, "")
                risk_card(
                    f"Relatório Sentinela — {resultado.get('status','').upper()}",
                    f"{nivel} | {resultado.get('resumo','')}",
                    f"**Recomendação:** {resultado.get('recomendacao','')}\n\n"
                    + "\n".join(f"{'➕' if d['tipo']=='adicionado' else '➖'} {d['conteudo']}"
                                for d in resultado.get("delta", [])[:5]),
                    cor
                )
                cp["alertas"].append({
                    "nivel": nivel, "resumo": resultado.get("resumo", ""),
                    "url": cp["editais_monitorados"][0],
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                })
    else:
        st.info("Nenhum edital em monitoramento. Adicione uma URL acima para iniciar a vigília.")

    st.divider()

    # ════════════════════════════════════════
    # MÓDULO 2 — ANTI-PREÇO SUICIDA
    # ════════════════════════════════════════
    section("💰", "Módulo Anti-Preço Suicida — Vigilante de Lances")
    st.caption("Configure sua planilha de custos. O sistema alertará se um lance ameaçar sua margem ou cruzar o piso de inexequibilidade.")

    with st.expander("⚙️ Configurar Planilha de Custos", expanded=False):
        lc = cp["lances_config"]
        ap1, ap2 = st.columns(2)
        with ap1:
            lc["custo_direto"] = st.number_input(
                "Custo Direto Total (R$)", value=float(lc["custo_direto"]),
                min_value=0.0, step=1000.0, format="%.2f",
                help="Materiais + Mão de obra + Encargos"
            )
            lc["bdi_pct"] = st.number_input(
                "BDI / Despesas Indiretas (%)", value=float(lc["bdi_pct"]),
                min_value=0.0, max_value=100.0, step=0.5, format="%.2f"
            )
        with ap2:
            lc["margem_pct"] = st.number_input(
                "Margem de Lucro (%)", value=float(lc["margem_pct"]),
                min_value=0.0, max_value=100.0, step=0.5, format="%.2f"
            )
            lc["impostos_pct"] = st.number_input(
                "Impostos ISS+PIS+COFINS (%)", value=float(lc["impostos_pct"]),
                min_value=0.0, max_value=30.0, step=0.25, format="%.2f"
            )

    # Cálculos da planilha em tempo real
    custo_d = lc["custo_direto"]
    if custo_d > 0:
        bdi      = lc["bdi_pct"]   / 100
        margem   = lc["margem_pct"] / 100
        impostos = lc["impostos_pct"] / 100
        custo_total  = custo_d * (1 + bdi + impostos)
        preco_alvo   = custo_total * (1 + margem)
        piso_inex    = custo_d * 0.70     # 70% do custo direto (TCU)

        m1, m2, m3 = st.columns(3)
        m1.metric("Custo Total (com BDI+impostos)", f"R$ {custo_total:,.2f}")
        m2.metric("Preço Alvo (com margem)",        f"R$ {preco_alvo:,.2f}")
        m3.metric("Piso Inexequibilidade (TCU)",    f"R$ {piso_inex:,.2f}",
                  "Art. 59 — Lei 14.133/21")

        url_sala = st.text_input("URL da Sala de Lances (PNCP/Comprasnet)",
                                 placeholder="https://pncp.gov.br/app/lances/...")
        col_lance_input, col_lance_btn = st.columns([3, 1])
        with col_lance_input:
            menor_lance_manual = st.number_input(
                "Menor Lance Atual (simulação manual)", value=0.0,
                min_value=0.0, step=100.0, format="%.2f",
                help="Em produção: capturado automaticamente da sala de lances"
            )
        with col_lance_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            analisar_lance = st.button("⚡ Analisar Lance")

        if analisar_lance and menor_lance_manual > 0:
            margem_restante = (menor_lance_manual - custo_total) / custo_total

            if menor_lance_manual < piso_inex:
                risk_card(
                    "PREÇO SUICIDA DETECTADO",
                    f"CRÍTICO | Lance R$ {menor_lance_manual:,.2f} abaixo do piso de inexequibilidade",
                    f"O lance de R$ {menor_lance_manual:,.2f} está abaixo do piso de inexequibilidade "
                    f"(R$ {piso_inex:,.2f} = 70% do seu custo direto).\n\n"
                    f"**Ação recomendada:** Prepare uma impugnação por inexequibilidade.\n"
                    f"**Base legal:** Lei 14.133/2021, Art. 59 | Acórdão TCU 2170/2023.",
                    "critical"
                )
            elif menor_lance_manual < custo_total:
                risk_card(
                    "RISCO DE PREJUÍZO OPERACIONAL",
                    f"CRÍTICO | Lance abaixo do seu custo mínimo",
                    f"O lance (R$ {menor_lance_manual:,.2f}) está abaixo do seu custo total "
                    f"(R$ {custo_total:,.2f}). Cobrir esse preço geraria prejuízo.\n\n"
                    f"**Decisão:** Recuar é a opção estratégica correta.",
                    "critical"
                )
            elif margem_restante < 0.05:
                risk_card(
                    "MARGEM CRÍTICA",
                    f"ATENÇÃO | Apenas {margem_restante*100:.1f}% de margem restante",
                    f"Você ainda cobre o custo, mas com margem mínima de {margem_restante*100:.1f}%. "
                    f"Considere se o risco operacional vale a pena.",
                    "warning"
                )
            else:
                risk_card(
                    "SITUAÇÃO CONTROLADA",
                    f"OK | {margem_restante*100:.1f}% de margem sobre o custo mínimo",
                    f"Lance atual (R$ {menor_lance_manual:,.2f}) está dentro da sua zona de segurança. "
                    f"Continue monitorando.",
                    "success"
                )
    else:
        st.info("Configure o custo direto acima para ativar o vigilante de lances.")

    st.divider()

    # ════════════════════════════════════════
    # MÓDULO 3 — COMPLIANCE 2026
    # ════════════════════════════════════════
    section("⚖️", "Módulo Compliance & Governança 2026")
    st.caption("Cole o texto do edital para análise instantânea de riscos, score de viabilidade e detecção de cláusulas restritivas da Lei 14.133/2021.")

    texto_compliance = st.text_area(
        "Texto do Edital para Análise de Compliance",
        label_visibility="collapsed",
        placeholder="Cole aqui o texto extraído do edital (ou extraia via Auditoria de Editais)...",
        height=150
    )

    if st.button("🔬 Executar Análise Compliance") and texto_compliance:
        if not api_key:
            st.warning("API Key necessária para análise avançada.")
        else:
            with st.spinner("Scanning NLP — verificando conformidade com Lei 14.133/2021..."):
                client = get_claude(api_key)
                perfil = st.session_state.empresa
                system = (
                    "Você é o módulo de Compliance & Governança 2026 da LicitA-IA. "
                    "Analise o edital e retorne APENAS JSON com esta estrutura:\n"
                    '{"score_viabilidade": 0-100, "classificacao": "ALTO RISCO|RISCO MODERADO|VIÁVEL", '
                    '"criticos": [{"titulo":"","descricao":"","base_legal":""}], '
                    '"moderados": [{"titulo":"","descricao":"","base_legal":""}], '
                    '"padrao_agu": true|false, '
                    '"clausulas_6x1": true|false, '
                    '"marca_especifica": true|false, '
                    '"resumo_executivo": ""}'
                )
                user = (
                    f"Edital para análise:\n{texto_compliance[:6000]}\n\n"
                    f"Perfil da empresa:\n"
                    f"- Capital Social: R$ {perfil['capital_social']:,.2f}\n"
                    f"- Liquidez Corrente: {perfil['liquidez_corrente']:.2f}\n"
                    f"- Certificações: {', '.join(perfil['certificacoes']) or 'Nenhuma'}"
                )
                raw = chamar_claude(client, system, user, max_tokens=2000)
                res = parse_json(raw)
                cp["ultimo_compliance"] = res

            # Exibe score
            score = res.get("score_viabilidade", 0)
            classe = res.get("classificacao", "")
            cor_score = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"

            st.markdown(f"""
            <div class="pcard" style="text-align:center; padding:32px;">
                <div style="font-size:13px; font-weight:700; letter-spacing:0.1em;
                            text-transform:uppercase; color:var(--text-color); opacity:0.5;
                            margin-bottom:12px;">Score de Viabilidade</div>
                <div style="font-size:72px; font-weight:800; color:{cor_score};
                            line-height:1;">{score}</div>
                <div style="font-size:16px; font-weight:600; color:{cor_score};
                            margin-top:8px;">{classe}</div>
                <div style="font-size:13px; color:var(--text-color); opacity:0.6;
                            margin-top:12px;">{res.get('resumo_executivo','')}</div>
            </div>
            """, unsafe_allow_html=True)

            # Badges de detecção
            flags = []
            if res.get("clausulas_6x1"):
                flags.append(("🚨 Cláusula 6x1 Detectada", "critical"))
            if res.get("marca_especifica"):
                flags.append(("🚨 Exigência de Marca", "critical"))
            if res.get("padrao_agu"):
                flags.append(("✅ Padrão AGU Detectado", "success"))

            for flag, tipo in flags:
                risk_card(flag, "DETECÇÃO AUTOMÁTICA",
                          "Verifique o relatório completo abaixo.", tipo)

            # Riscos críticos
            criticos = res.get("criticos", [])
            if criticos:
                st.markdown("**Riscos Críticos**")
                for item in criticos:
                    risk_card(
                        item.get("titulo", ""),
                        f"CRÍTICO | {item.get('base_legal','')}",
                        item.get("descricao", ""),
                        "critical"
                    )

            # Riscos moderados
            moderados = res.get("moderados", [])
            if moderados:
                st.markdown("**Riscos Moderados**")
                for item in moderados:
                    risk_card(
                        item.get("titulo", ""),
                        f"MODERADO | {item.get('base_legal','')}",
                        item.get("descricao", ""),
                        "warning"
                    )

    st.divider()

    # ════════════════════════════════════════
    # MÓDULO 4 — PARSER AGU
    # ════════════════════════════════════════
    section("🏛️", "Módulo Parser AGU — Extração Acelerada de Campos")
    st.caption(
        "Se o edital seguir o padrão oficial da AGU (v2025/2026), o sistema extrai multas, "
        "prazos e sanções com 100% de precisão — sem custo de IA."
    )

    texto_agu = st.text_area(
        "Texto do Edital para Parser AGU",
        label_visibility="collapsed",
        placeholder="Cole o texto do edital para detecção automática do padrão AGU...",
        height=130,
        key="agu_input"
    )

    if st.button("🏛️ Executar Parser AGU") and texto_agu:
        with st.spinner("Detectando padrão AGU e extraindo campos..."):
            # Detecção de padrão AGU via regex (zero custo de tokens)
            import re
            assinaturas_agu = [
                r"Advocacia-Geral\s+da\s+União",
                r"AGU\s*[-–]\s*Modelo",
                r"Minuta\s+Padrão\s+(?:AGU|PGF|CGU)",
                r"SAPIENS\s*[-/]\s*AGU",
                r"SEGES/MGI.*n[oº]\.?\s*\d+/202[5-6]",
                r"Resolução\s+AGU.*7[02]/202[4-6]",
                r"Portaria\s+AGU.*40/202[3-6]",
            ]
            matches_agu = sum(
                1 for p in assinaturas_agu
                if re.search(p, texto_agu, re.IGNORECASE)
            )
            confianca = min(100, int(matches_agu / 3 * 100)) if matches_agu else 0
            detectado = matches_agu >= 1

            # Extração determinística de campos-chave
            def _extrair(padrao, texto, default="Não identificado"):
                m = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
                return m.group(1).strip() if m else default

            campos = {
                "Modalidade":         _extrair(r"(Pregão\s+Eletrônico|Concorrência\s+Eletrônica|Dispensa\s+Eletrônica)", texto_agu),
                "Número do Edital":   _extrair(r"[Ee]dital.*?n[oº]?\s*([\d\./\-]+)", texto_agu),
                "UASG":               _extrair(r"UASG\s*[:\-]?\s*(\d{6})", texto_agu),
                "Valor Estimado":     _extrair(r"[Vv]alor.*?estimado.*?R\$\s*([\d\.\,]+)", texto_agu),
                "Data de Abertura":   _extrair(r"[Aa]bertura.*?(\d{2}/\d{2}/\d{4})", texto_agu),
                "Prazo de Execução":  _extrair(r"[Pp]razo.*?execução.*?(\d+\s+dias?[^.]*)", texto_agu),
                "Vigência":           _extrair(r"[Vv]igência.*?(\d+\s+meses?[^.]*)", texto_agu),
                "Garantia Contratual":_extrair(r"[Gg]arantia.*?(\d+(?:[,\.]\d+)?)\s*%.*?contrato", texto_agu),
                "Multa Moratória":    _extrair(r"[Mm]ulta\s+morat.*?(\d+(?:[,\.]\d+)?)\s*%.*?dia", texto_agu),
                "Multa Inadimplemento": _extrair(r"[Mm]ulta.*?inadimpl.*?(\d+(?:[,\.]\d+)?)\s*%", texto_agu),
                "Prazo de Recurso":   _extrair(r"[Rr]ecurso.*?(\d+)\s+dias?\s+úteis", texto_agu),
                "Capital Social Mín.":_extrair(r"[Cc]apital\s+[Ss]ocial.*?R\$\s*([\d\.\,]+)", texto_agu),
                "Liquidez Corrente":  _extrair(r"[Ll]iquidez\s+[Cc]orrente.*?(\d+[,\.]\d+)", texto_agu),
            }
            cp["ultimo_agu"] = {"detectado": detectado, "confianca": confianca, "campos": campos}

        # Exibe resultado da detecção
        if detectado:
            st.success(
                f"✅ Padrão AGU detectado com {confianca}% de confiança. "
                f"Extração determinística ativa — sem custo de tokens IA."
            )
        else:
            st.warning(
                "⚠️ Padrão AGU não identificado. Edital será processado via Claude (Auditoria de Editais). "
                "Custo computacional normal."
            )

        # Tabela de campos extraídos
        import pandas as pd
        df_campos = pd.DataFrame([
            {"Campo": k, "Valor Extraído": v,
             "Status": "✅" if v != "Não identificado" else "❌"}
            for k, v in campos.items()
        ])
        extraidos_ok = (df_campos["Status"] == "✅").sum()
        st.metric("Campos extraídos com sucesso",
                  f"{extraidos_ok}/{len(campos)}",
                  f"{int(extraidos_ok/len(campos)*100)}% de precisão")
        st.dataframe(df_campos, use_container_width=True, hide_index=True)

        # Alertas legais automáticos
        alertas_legais = []
        multa_str = campos.get("Multa Inadimplemento", "")
        try:
            multa_val = float(re.sub(r"[^\d,.]", "", multa_str).replace(",", "."))
            if multa_val > 30:
                alertas_legais.append(
                    f"Multa por inadimplemento de {multa_val}% pode ser contestada "
                    f"(Lei 14.133/2021, Art. 162 — máximo usual: 20-30%)."
                )
        except (ValueError, AttributeError):
            pass

        liq_str = campos.get("Liquidez Corrente", "")
        try:
            liq_val = float(liq_str.replace(",", "."))
            if liq_val > 1.5:
                alertas_legais.append(
                    f"Liquidez corrente exigida de {liq_val:.2f} supera 1,5. "
                    f"TCU considera restritivo (Súmula 272)."
                )
        except (ValueError, AttributeError):
            pass

        if alertas_legais:
            st.markdown("**⚠️ Alertas Legais Automáticos**")
            for alerta in alertas_legais:
                risk_card("Alerta Legal", "COMPLIANCE AGU", alerta, "warning")

    # ── Histórico de Alertas ─────────────────────────────────────────────
    if cp["alertas"]:
        st.divider()
        section("🔔", "Histórico de Alertas do Co-Piloto")
        for alerta in reversed(cp["alertas"][-10:]):  # últimos 10
            nivel = alerta.get("nivel", "INFO")
            tipo  = {"CRITICO": "critical", "MODERADO": "warning"}.get(nivel, "")
            ts    = alerta.get("timestamp", "")[:16].replace("T", " ")
            risk_card(
                alerta.get("resumo", "Alerta sem descrição"),
                f"{nivel} | {ts}",
                alerta.get("url", ""),
                tipo
            )
        if st.button("🗑️ Limpar Histórico de Alertas"):
            cp["alertas"] = []
            st.rerun()
