import streamlit as st
import pandas as pd
import anthropic
import requests
import fitz  # PyMuPDF
import json

# --- 1. CONFIGURAÇÕES E TEMA ---
st.set_page_config(
    page_title="LicitA-IA | Intelligence Unit",
    layout="wide",
    page_icon="🛡️"
)

st.markdown("""
    <style>
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px 6px 0 0;
        padding: 10px 16px;
        font-weight: 600;
        color: #434343;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important;
        color: white !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
        padding: 12px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,58,140,0.3);
        color: white;
    }

    /* FIX: Degradê nas tags do multiselect */
    .stMultiSelect div[data-baseweb="tag"] {
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important;
        color: white !important;
        border-radius: 4px;
    }
    .stMultiSelect div[data-baseweb="tag"] span {
        color: white !important;
    }

    /* Cards padrão */
    .card {
        background-color: var(--secondary-background-color);
        color: var(--text-color);
        padding: 25px;
        border-radius: 12px;
        border-left: 8px solid #096dd9;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    .critical     { border-left-color: #ff4b4b; }
    .warning-card { border-left-color: #ffa500; }
    .success-card { border-left-color: #52c41a; }

    /* FIX: cert-card usa variáveis CSS para funcionar em dark mode também */
    .cert-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(9, 109, 217, 0.25);
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .cert-icon {
        font-size: 22px;
        margin-right: 12px;
    }
    .cert-text {
        font-weight: 600;
        font-size: 15px;
        color: var(--text-color);
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. SESSION STATE ---
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# --- 3. UTILITÁRIOS ---

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
            texto += "\n[... texto truncado para análise ...]"
            break
    return texto


def get_claude(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def chamar_claude(client: anthropic.Anthropic, system: str, user: str,
                  max_tokens: int = 2048) -> str:
    try:
        resposta = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return resposta.content[0].text
    except anthropic.AuthenticationError:
        st.error("API Key inválida. Verifique na sidebar.")
        st.stop()
    except anthropic.RateLimitError:
        st.error("Limite de requisições atingido. Aguarde e tente novamente.")
        st.stop()
    except Exception as e:
        st.error(f"Erro na chamada ao Claude: {e}")
        st.stop()


def perfil_empresa_str() -> str:
    e = st.session_state.empresa
    return (
        f"Razão Social: {e['razao_social']}\n"
        f"CNPJ: {e['cnpj']}\n"
        f"Capital Social: R$ {e['capital_social']:,.2f}\n"
        f"Liquidez Corrente: {e['liquidez_corrente']}\n"
        f"Certificações: {', '.join(e['certificacoes']) if e['certificacoes'] else 'Nenhuma cadastrada'}"
    )


def render_card(titulo: str, subtitulo: str, corpo: str, classe: str = ""):
    cor = {
        "critical":     "#ff4b4b",
        "warning-card": "#ffa500",
        "success-card": "#52c41a",
        "":             "#096dd9",
    }.get(classe, "#096dd9")
    st.markdown(f"""
    <div class="card {classe}">
        <small style="color:{cor}; font-weight:bold;">{subtitulo}</small>
        <h3 style="margin:6px 0 10px 0;">{titulo}</h3>
        <p style="margin:0;">{corpo.replace(chr(10), '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)


def render_certificacao(cert: str):
    """Renderiza uma certificação como card com ícone."""
    icon_map = {
        "ISO 9001":   "✅",
        "ISO 14001":  "🌱",
        "ISO 27001":  "🔒",
        "SASSMAQ":    "🚒",
        "PBQP-H":     "🏗️",
        "OHSAS 18001":"⛑️",
    }
    icon = icon_map.get(cert, "📄")
    st.markdown(f"""
    <div class="cert-card">
        <span class="cert-icon">{icon}</span>
        <span class="cert-text">{cert}</span>
    </div>
    """, unsafe_allow_html=True)


# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
    st.title("LicitA-IA Suite")

    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input(
            "Anthropic API Key (Claude)",
            type="password",
            help="Sua chave da Anthropic para ativar o motor de IA"
        )

    st.divider()
    st.markdown("### Status do Sistema")
    if api_key:
        st.success("✅ Motor: Claude Sonnet ativo")
    else:
        st.warning("⚠️ Insira a API Key para ativar o motor")

    empresa_nome = st.session_state.empresa["razao_social"] or "Aguardando Setup"
    st.info(f"🏢 Empresa Ativa:\n{empresa_nome}")

    if st.button("🗑️ Limpar Todos os Resultados"):
        for k in ["resultado_auditoria", "resultado_cacador",
                  "resultado_juridico", "resultado_espiao"]:
            st.session_state[k] = None
        st.rerun()


# --- CABEÇALHO ---
st.markdown('<h1 style="font-size:38px; margin-bottom:0;">🛡️ LicitA-IA: Intelligence Unit</h1>',
            unsafe_allow_html=True)
st.markdown("<p style='font-size:18px; color:#808080; margin-bottom:30px;'>"
            "Auditoria, Matching e Espionagem Competitiva em Tempo Real para Licitantes de Elite.</p>",
            unsafe_allow_html=True)

# --- 5. ABAS ---
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao = st.tabs([
    "🏢 1. Perfil (DNA)", "🔍 2. Auditoria de Editais",
    "🎯 3. Caçador (Match)", "⚖️ 4. Advogado AI", "🕵️ 5. Espião"
])


# ==========================================
# ABA 1: PERFIL / DNA CORPORATIVO
# ==========================================
with tab_perfil:
    st.subheader("Configuração do DNA Corporativo")
    st.write("A IA usará este perfil para mapear restrições ocultas em editais de centenas de páginas.")

    col_busca1, col_busca2 = st.columns([3, 1])
    with col_busca1:
        cnpj_input = st.text_input(
            "Busca Automática por CNPJ (apenas números):",
            value=st.session_state.empresa["cnpj"]
        )
    with col_busca2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Extrair da Receita Federal"):
            cnpj_limpo = "".join(filter(str.isdigit, cnpj_input))
            if len(cnpj_limpo) == 14:
                with st.spinner("Conectando aos servidores do Governo..."):
                    try:
                        url  = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
                        resp = requests.get(url, timeout=10)
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
                            st.error("CNPJ não encontrado na Receita Federal.")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")
            else:
                st.warning("O CNPJ deve ter exatamente 14 dígitos.")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        razao   = st.text_input("Razão Social", value=st.session_state.empresa["razao_social"])
        capital = st.number_input("Capital Social Registrado (R$)",
                                  value=float(st.session_state.empresa["capital_social"]),
                                  min_value=0.0, step=1000.0, format="%.2f")
    with c2:
        liquidez = st.number_input("Índice de Liquidez Corrente",
                                   value=float(st.session_state.empresa["liquidez_corrente"]),
                                   min_value=0.0, step=0.1, format="%.2f")

    # --- Módulo de Certificações ---
    st.markdown("---")
    st.markdown("### Certificações Ativas")
    certif = st.multiselect(
        "Selecione suas certificações",
        ["ISO 9001", "ISO 14001", "ISO 27001", "SASSMAQ", "PBQP-H", "OHSAS 18001"],
        default=st.session_state.empresa["certificacoes"],
        label_visibility="collapsed"
    )

    if certif:
        col_cert1, col_cert2, col_cert3 = st.columns(3)
        cols = [col_cert1, col_cert2, col_cert3]
        for i, cert in enumerate(sorted(certif)):
            with cols[i % 3]:
                render_certificacao(cert)
    else:
        st.info("Nenhuma certificação ativa cadastrada.")

    atestados = st.text_area(
        "Descreva brevemente os principais contratos/atestados da empresa:",
        value=st.session_state.empresa.get("atestados", ""),
        placeholder="Ex: Fornecimento de EPI para Petrobras (2022-2024), contrato de R$ 1,2M...",
        height=120
    )

    if st.button("💾 Blindar Perfil e Salvar"):
        st.session_state.empresa.update({
            "cnpj":              "".join(filter(str.isdigit, cnpj_input)),
            "razao_social":      razao,
            "capital_social":    capital,
            "liquidez_corrente": liquidez,
            "certificacoes":     certif,
            "atestados":         atestados,
        })
        st.success("✅ DNA salvo! O Motor de Auditoria está calibrado para a sua empresa.")


# ==========================================
# ABA 2: AUDITORIA DE EDITAIS
# ==========================================
with tab_auditoria:
    st.subheader("Auditoria de Conformidade e Riscos com IA")

    if not st.session_state.empresa["razao_social"]:
        st.warning("⚠️ Configure o Perfil na Aba 1 antes de auditar.")
    elif not api_key:
        st.warning("⚠️ Insira sua API Key na sidebar para ativar a auditoria com IA.")
    else:
        edital_file = st.file_uploader("Upload do Edital (PDF)", type="pdf", key="auditoria")

        if edital_file and st.button("🔍 Executar Pente-Fino com IA"):
            with st.status("Auditando edital com Claude...", expanded=True) as status:
                st.write("📄 Extraindo texto do PDF...")
                texto_edital = extrair_texto_pdf(edital_file)

                st.write(f"🧠 Analisando {len(texto_edital):,} caracteres com Claude...")
                client = get_claude(api_key)

                # FIX: system prompt sem replace() que corrompia aspas e quebras de linha
                system = """Você é um auditor sênior de licitações especialista na Lei 14.133/2021 e Lei 8.666/93.
Sua função é identificar TODAS as cláusulas que podem desclassificar ou prejudicar o licitante descrito.
Responda SOMENTE com um JSON válido no formato abaixo, sem markdown, sem texto extra:
{
  "riscos": [
    {
      "severidade": "CRITICO | ATENCAO | INFO",
      "categoria": "ex: Capacidade Técnica, Habilitação Financeira, Prazo",
      "pagina": "ex: Pág. 14 ou Desconhecida",
      "titulo": "string curta",
      "descricao": "string detalhada explicando o risco e o artigo de lei violado",
      "acao": "string com plano de ação recomendado"
    }
  ],
  "resumo": "avaliação geral do edital em 3-4 linhas",
  "score_seguranca": 0
}"""

                user = f"""PERFIL DA EMPRESA LICITANTE:
{perfil_empresa_str()}

TEXTO DO EDITAL:
{texto_edital}

Analise o edital completo, cruze com o perfil da empresa e retorne o JSON com todos os riscos encontrados."""

                raw = chamar_claude(client, system, user, max_tokens=4096)

                try:
                    clean = raw.strip().replace("```json", "").replace("```", "")
                    st.session_state.resultado_auditoria = json.loads(clean)
                except json.JSONDecodeError:
                    st.error("Erro ao interpretar resposta da IA. Tente novamente.")
                    st.session_state.resultado_auditoria = None
                    st.stop()

                status.update(label="✅ Auditoria Concluída!", state="complete", expanded=False)

        if st.session_state.resultado_auditoria:
            resultado = st.session_state.resultado_auditoria
            riscos    = resultado.get("riscos", [])
            score     = resultado.get("score_seguranca", 0)
            criticos  = [r for r in riscos if r["severidade"] == "CRITICO"]
            atencoes  = [r for r in riscos if r["severidade"] == "ATENCAO"]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Score de Segurança", f"{score}/100",
                      delta_color="inverse" if score < 60 else "normal")
            m2.metric("Riscos Críticos",    len(criticos), delta_color="inverse")
            m3.metric("Pontos de Atenção",  len(atencoes), delta_color="off")
            m4.metric("Total de Riscos",    len(riscos))

            st.markdown("---")
            render_card("Avaliação Geral do Edital", "📋 RESUMO EXECUTIVO",
                        resultado.get("resumo", ""))

            st.markdown("### Riscos Identificados")
            ordem = {"CRITICO": 0, "ATENCAO": 1, "INFO": 2}
            for r in sorted(riscos, key=lambda x: ordem.get(x["severidade"], 3)):
                classe = "critical" if r["severidade"] == "CRITICO" else \
                         "warning-card" if r["severidade"] == "ATENCAO" else ""
                corpo  = f"{r['descricao']}\n\n💡 <b>Plano de Ação:</b> {r.get('acao', 'N/A')}"
                render_card(
                    r["titulo"],
                    f"{'🚨' if r['severidade'] == 'CRITICO' else '⚠️'} {r['severidade']} | {r['pagina']} | {r['categoria']}",
                    corpo, classe
                )


# ==========================================
# ABA 3: CAÇADOR DE OPORTUNIDADES
# ==========================================
with tab_cacador:
    st.subheader("🎯 Caçador: Matching Inteligente de Oportunidades")
    st.write("Descreva o perfil de licitações que deseja e a IA encontra e avalia as melhores oportunidades.")

    if not api_key:
        st.warning("⚠️ Insira sua API Key na sidebar.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            segmento = st.text_input(
                "Segmento / Objeto de interesse:",
                placeholder="Ex: fornecimento de uniformes, limpeza predial, TI..."
            )
            uf = st.selectbox("Estado de interesse:", [
                "Todos", "SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO", "DF",
                "PE", "CE", "AM", "PA", "MT", "MS", "ES", "RN", "PB", "AL",
                "SE", "PI", "MA", "TO", "RO", "AC", "AP", "RR"
            ])
        with col2:
            valor_min  = st.number_input("Valor mínimo estimado (R$)", value=0.0,
                                         step=10000.0, format="%.2f")
            valor_max  = st.number_input("Valor máximo estimado (R$)", value=1_000_000.0,
                                         step=10000.0, format="%.2f")
            modalidade = st.multiselect(
                "Modalidades aceitas:",
                ["Pregão Eletrônico", "Concorrência", "Tomada de Preços", "Convite", "RDC"],
                default=["Pregão Eletrônico"]
            )

        atestados_cacador = st.text_area(
            "Descreva seus atestados e experiências relevantes:",
            value=st.session_state.empresa.get("atestados", ""),
            placeholder="Ex: Fornecimento de 5.000 uniformes para Prefeitura de SP (2023)...",
            height=100
        )

        if st.button("🚀 Ativar Caçador de Oportunidades"):
            with st.spinner("A IA está mapeando oportunidades e calculando compatibilidade..."):
                client = get_claude(api_key)

                system = """Você é um especialista em prospecção de licitações públicas no Brasil.
Avalie a compatibilidade do perfil da empresa com o segmento e gere relatório estratégico de oportunidades.
Responda SOMENTE com JSON válido no formato:
{
  "compatibilidade_geral": 0,
  "analise": "string com análise detalhada do potencial competitivo",
  "oportunidades": [
    {
      "titulo": "string",
      "orgao_exemplo": "string",
      "valor_estimado": "string",
      "compatibilidade": 0,
      "pontos_fortes": ["string"],
      "pontos_fracos": ["string"],
      "proximos_passos": "string"
    }
  ],
  "recomendacoes": ["string"]
}"""

                user = f"""PERFIL DA EMPRESA:
{perfil_empresa_str()}
Atestados/Experiências: {atestados_cacador}

CRITÉRIOS DE BUSCA:
Segmento: {segmento}
Estado: {uf}
Faixa de valor: R$ {valor_min:,.2f} a R$ {valor_max:,.2f}
Modalidades: {', '.join(modalidade)}

Avalie a compatibilidade e gere análise estratégica de oportunidades."""

                raw = chamar_claude(client, system, user, max_tokens=3000)
                try:
                    clean = raw.strip().replace("```json", "").replace("```", "")
                    st.session_state.resultado_cacador = json.loads(clean)
                except json.JSONDecodeError:
                    st.error("Erro ao interpretar resposta. Tente novamente.")
                    st.stop()

        if st.session_state.resultado_cacador:
            res  = st.session_state.resultado_cacador
            opps = res.get("oportunidades", [])

            st.markdown("---")
            m1, m2 = st.columns(2)
            m1.metric("Compatibilidade Geral",  f"{res.get('compatibilidade_geral', 0)}%")
            m2.metric("Oportunidades Mapeadas", len(opps))

            render_card("Análise Estratégica", "🎯 DIAGNÓSTICO DE POTENCIAL",
                        res.get("analise", ""))

            for opp in sorted(opps, key=lambda x: x.get("compatibilidade", 0), reverse=True):
                comp   = opp.get("compatibilidade", 0)
                classe = "success-card" if comp >= 70 else ("warning-card" if comp >= 40 else "critical")
                corpo  = (
                    f"<b>Órgão Típico:</b> {opp.get('orgao_exemplo', 'N/A')}<br>"
                    f"<b>Valor Estimado:</b> {opp.get('valor_estimado', 'N/A')}<br>"
                    f"<b>✅ Pontos Fortes:</b> {', '.join(opp.get('pontos_fortes', []))}<br>"
                    f"<b>⚠️ Pontos Fracos:</b> {', '.join(opp.get('pontos_fracos', []))}<br>"
                    f"<b>🚀 Próximos Passos:</b> {opp.get('proximos_passos', 'N/A')}"
                )
                render_card(opp["titulo"], f"🎯 MATCH: {comp}%", corpo, classe)

            st.markdown("### 📋 Recomendações Estratégicas")
            for rec in res.get("recomendacoes", []):
                st.markdown(f"- {rec}")


# ==========================================
# ABA 4: ADVOGADO AI
# ==========================================
with tab_juridico:
    st.subheader("⚖️ Advogado AI: Redação de Peças Jurídicas")
    st.write("Gere impugnações, recursos administrativos e pedidos de esclarecimento com base na Lei 14.133/2021.")

    if not api_key:
        st.warning("⚠️ Insira sua API Key na sidebar.")
    else:
        tipo_peca = st.selectbox("Tipo de Peça Jurídica:", [
            "Impugnação de Edital",
            "Recurso Administrativo (pós-julgamento)",
            "Pedido de Esclarecimento",
            "Contrarrazões de Recurso",
            "Impugnação de Habilitação de Concorrente",
        ])

        col1, col2 = st.columns(2)
        with col1:
            orgao       = st.text_input("Órgão / Entidade Licitante:",
                                        placeholder="Ex: Prefeitura Municipal de Campinas")
            num_edital  = st.text_input("Número do Edital / Pregão:",
                                        placeholder="Ex: Pregão Eletrônico 001/2025")
        with col2:
            objeto       = st.text_input("Objeto da Licitação:",
                                         placeholder="Ex: Aquisição de uniformes profissionais")
            data_sessao  = st.text_input("Data da Sessão/Prazo:",
                                         placeholder="Ex: 20/01/2025")

        fundamento = st.text_area(
            "Descreva o problema / fundamento da peça (o que quer contestar ou esclarecer):",
            placeholder=(
                "Ex: O edital exige ISO 9001 no item 9.4.1 como requisito de habilitação técnica "
                "para fornecimento de uniformes. Esta exigência é ilegal pois restringe a "
                "competitividade sem justificativa técnica, ferindo o Art. 9º da Lei 14.133/2021..."
            ),
            height=150
        )

        if st.button("⚖️ Redigir Peça Jurídica com IA"):
            if not fundamento or not orgao:
                st.warning("Preencha ao menos o Órgão e o Fundamento.")
            else:
                with st.spinner(f"Redigindo {tipo_peca}..."):
                    client = get_claude(api_key)

                    system = """Você é um advogado especialista em Direito Administrativo e Licitações Públicas com 20 anos de experiência.
Redija peças jurídicas formais, fundamentadas na Lei 14.133/2021, Lei 8.666/93, jurisprudência do TCU e princípios do Direito Administrativo.
A peça deve ser profissional, bem estruturada, com linguagem técnica e argumentação sólida.
Inclua: cabeçalho formal, qualificação das partes, dos fatos, fundamentos jurídicos (com artigos de lei e súmulas), pedido e fechamento."""

                    user = f"""Redija uma peça de {tipo_peca} com os seguintes dados:

EMPRESA RECORRENTE:
{perfil_empresa_str()}

DADOS DO PROCESSO:
Órgão/Entidade: {orgao}
Número do Edital: {num_edital}
Objeto: {objeto}
Data da Sessão/Prazo: {data_sessao}

FUNDAMENTO / PROBLEMA A SER CONTESTADO:
{fundamento}

Redija a peça completa, formal e fundamentada."""

                    peca = chamar_claude(client, system, user, max_tokens=4096)
                    st.session_state.resultado_juridico = {"tipo": tipo_peca, "texto": peca}

        if st.session_state.resultado_juridico:
            res = st.session_state.resultado_juridico
            st.markdown("---")
            st.markdown(f"### 📄 {res['tipo']}")
            st.markdown(
                f"<div style='background:var(--secondary-background-color); padding:30px; "
                f"border-radius:12px; white-space:pre-wrap; font-family:serif; line-height:1.8;'>"
                f"{res['texto']}</div>",
                unsafe_allow_html=True
            )
            st.download_button(
                label="⬇️ Baixar Peça em .txt",
                data=res["texto"],
                file_name=f"{res['tipo'].replace(' ', '_').lower()}.txt",
                mime="text/plain"
            )


# ==========================================
# ABA 5: ESPIÃO (INTELIGÊNCIA COMPETITIVA)
# ==========================================
with tab_espiao:
    st.subheader("🕵️ Espião: Inteligência Competitiva em Licitações")
    st.write("Analise o histórico de um concorrente, identifique padrões e descubra como vencê-lo.")

    if not api_key:
        st.warning("⚠️ Insira sua API Key na sidebar.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            cnpj_concorrente = st.text_input("CNPJ do Concorrente (apenas números):",
                                             placeholder="00000000000000")
            if st.button("🔍 Buscar Dados do Concorrente"):
                cnpj_c = "".join(filter(str.isdigit, cnpj_concorrente))
                if len(cnpj_c) == 14:
                    with st.spinner("Consultando Receita Federal..."):
                        try:
                            resp = requests.get(
                                f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_c}", timeout=10
                            )
                            if resp.status_code == 200:
                                st.session_state["dados_concorrente"] = resp.json()
                                st.success(f"Encontrado: {resp.json().get('razao_social')}")
                            else:
                                st.error("CNPJ não encontrado.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
                else:
                    st.warning("CNPJ inválido.")

        with col2:
            if "dados_concorrente" in st.session_state:
                d = st.session_state["dados_concorrente"]
                st.markdown(f"**Empresa:** {d.get('razao_social', 'N/A')}")
                st.markdown(f"**Capital Social:** R$ {float(d.get('capital_social') or 0):,.2f}")
                st.markdown(f"**Porte:** {d.get('porte', 'N/A')}")
                st.markdown(f"**Situação:** {d.get('descricao_situacao_cadastral', 'N/A')}")

        st.divider()

        historico_concorrente = st.text_area(
            "Cole aqui informações sobre o concorrente (contratos anteriores, estratégias conhecidas, licitações ganhas):",
            placeholder=(
                "Ex: A empresa XYZ Ltda costuma praticar desconto de 15-20% no lance final. "
                "Ganhou os pregões 001/2024 e 005/2024 da Prefeitura de SP. "
                "Possui certificação ISO 9001 e contrato vigente com o Estado de SP..."
            ),
            height=150
        )

        segmento_espiao = st.text_input(
            "Segmento da disputa:",
            placeholder="Ex: Fornecimento de EPI, Limpeza Predial..."
        )

        if st.button("🕵️ Gerar Dossiê Competitivo"):
            if not historico_concorrente:
                st.warning("Insira informações sobre o concorrente.")
            else:
                with st.spinner("A IA está analisando padrões e montando o dossiê..."):
                    client = get_claude(api_key)

                    dados_concorrente_str = ""
                    if "dados_concorrente" in st.session_state:
                        d = st.session_state["dados_concorrente"]
                        dados_concorrente_str = (
                            f"Razão Social: {d.get('razao_social')}\n"
                            f"Capital Social: R$ {float(d.get('capital_social') or 0):,.2f}\n"
                            f"Porte: {d.get('porte')}\n"
                            f"Situação: {d.get('descricao_situacao_cadastral')}\n"
                            f"CNAEs: {', '.join([c.get('descricao', '') for c in d.get('cnaes_secundarios', [])[:3]])}"
                        )

                    system = """Você é um estrategista de inteligência competitiva especializado em licitações públicas.
Analise os dados do concorrente e gere um dossiê estratégico para ajudar a empresa cliente a vencer a disputa.
Responda SOMENTE com JSON válido no formato:
{
  "perfil_competitivo": "string",
  "pontos_vulneraveis": ["string"],
  "estrategias_vencer": [
    {
      "estrategia": "string",
      "descricao": "string",
      "risco": "BAIXO | MEDIO | ALTO"
    }
  ],
  "alerta_dumping": false,
  "preco_referencia": "string",
  "recomendacao_final": "string"
}"""

                    user = f"""MINHA EMPRESA (cliente):
{perfil_empresa_str()}

DADOS DO CONCORRENTE:
{dados_concorrente_str}

HISTÓRICO / INTELIGÊNCIA DO CONCORRENTE:
{historico_concorrente}

SEGMENTO DA DISPUTA: {segmento_espiao}

Monte o dossiê competitivo completo e as estratégias para vencer este concorrente."""

                    raw = chamar_claude(client, system, user, max_tokens=3000)
                    try:
                        clean = raw.strip().replace("```json", "").replace("```", "")
                        st.session_state.resultado_espiao = json.loads(clean)
                    except json.JSONDecodeError:
                        st.error("Erro ao interpretar resposta. Tente novamente.")
                        st.stop()

        if st.session_state.resultado_espiao:
            res = st.session_state.resultado_espiao

            st.markdown("---")

            if res.get("alerta_dumping"):
                render_card(
                    "⚠️ Risco de Dumping Detectado",
                    "🚨 ALERTA ESTRATÉGICO",
                    "A IA identificou padrão de preços predatórios. Prepare impugnação preventiva se o lance final ficar abaixo do custo operacional.",
                    "critical"
                )

            render_card("Perfil Competitivo", "🕵️ DOSSIÊ DO CONCORRENTE",
                        res.get("perfil_competitivo", ""))

            st.markdown(f"**💰 Estimativa de Preço do Concorrente:** {res.get('preco_referencia', 'N/A')}")

            st.markdown("### 🎯 Estratégias para Vencer")
            for est in res.get("estrategias_vencer", []):
                risco  = est.get("risco", "BAIXO")
                classe = "critical" if risco == "ALTO" else \
                         "warning-card" if risco == "MEDIO" else "success-card"
                render_card(
                    est.get("estrategia", ""),
                    f"⚡ ESTRATÉGIA | Risco: {risco}",
                    est.get("descricao", ""),
                    classe
                )

            st.markdown("### 🔓 Pontos Vulneráveis do Concorrente")
            for ponto in res.get("pontos_vulneraveis", []):
                st.markdown(f"- {ponto}")

            render_card(
                "Recomendação Executiva",
                "🏆 PLANO FINAL",
                res.get("recomendacao_final", ""),
                "success-card"
            )
