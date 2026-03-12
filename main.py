import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import anthropic
import time

# --- 1. CONFIGURAÇÕES DE INTERFACE E TEMA ---
st.set_page_config(
    page_title="LicitA-IA | Intelligence Unit",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🛡️"
)

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1E1E1E; }
    [data-testid="stHeader"] { background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f5; border-radius: 8px 8px 0 0; padding: 12px 24px; font-weight: bold; color: #002766; }
    .stTabs [aria-selected="true"] { background-color: #096dd9 !important; color: white !important; }
    .card { background-color: #f8f9fa; padding: 25px; border-radius: 12px; border-left: 8px solid #096dd9; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .critical { border-left-color: #ff4b4b; }
    .success-card { border-left-color: #52c41a; }
    .stButton>button { background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%); color: white; border: none; padding: 10px; border-radius: 8px; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,58,140,0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMÓRIA DA EMPRESA (SESSION STATE) ---
if 'empresa' not in st.session_state:
    st.session_state.empresa = {
        "cnpj": "", "razao_social": "", "capital_social": 0.0,
        "liquidez_corrente": 1.0, "certificacoes": []
    }

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
    st.title("LicitA-IA Suite")
    api_key = st.text_input("Anthropic API Key (Claude)", type="password", help="Chave para redigir peças")
    st.divider()
    st.markdown("### Status do Sistema")
    st.success("✅ Motor: Claude 3.5 Sonnet")
    st.info(f"🏢 Empresa Ativa:\n{st.session_state.empresa['razao_social'] if st.session_state.empresa['razao_social'] else 'Não configurada'}")

st.markdown('<h1 style="color: #002766; font-size: 36px; margin-bottom: 0;">🛡️ LicitA-IA: Intelligence Unit</h1>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 16px; color: #595959;'>Auditoria, Matching e Espionagem Competitiva em Tempo Real.</p>", unsafe_allow_html=True)

# --- 4. ABAS DO SISTEMA ---
tab_perfil, tab_auditoria, tab_juridico, tab_espiao = st.tabs([
    "🏢 1. Perfil (DNA)", 
    "🔍 2. Auditoria de Editais", 
    "⚖️ 3. Advogado AI (Claude)", 
    "🕵️ 4. Espião de Concorrência"
])

# ABA 1: PERFIL
with tab_perfil:
    st.subheader("Configuração do DNA Corporativo")
    st.write("Preencha os dados da sua empresa para que a IA possa cruzar com as exigências dos editais.")
    
    c1, c2 = st.columns(2)
    with c1:
        cnpj = st.text_input("CNPJ", value=st.session_state.empresa['cnpj'])
        razao = st.text_input("Razão Social", value=st.session_state.empresa['razao_social'])
    with c2:
        capital = st.number_input("Capital Social Registrado (R$)", value=st.session_state.empresa['capital_social'])
        liquidez = st.number_input("Índice de Liquidez Corrente", value=st.session_state.empresa['liquidez_corrente'])
        
    certif = st.multiselect("Certificações Ativas", ["ISO 9001", "ISO 14001", "ISO 27001", "SASSMAQ"], default=st.session_state.empresa['certificacoes'])

    if st.button("💾 Salvar Perfil da Empresa"):
        st.session_state.empresa.update({
            "cnpj": cnpj, "razao_social": razao, "capital_social": capital,
            "liquidez_corrente": liquidez, "certificacoes": certif
        })
        st.success("Perfil atualizado! O sistema agora usará esses dados nas auditorias.")

# ABA 2: AUDITORIA
with tab_auditoria:
    st.subheader("Auditoria de Conformidade e Riscos")
    if not st.session_state.empresa['razao_social']:
        st.warning("⚠️ Configure o Perfil da Empresa na primeira aba antes de realizar a auditoria.")
    else:
        edital_file = st.file_uploader("Upload do Edital (PDF)", type="pdf")
        if edital_file and st.button("Executar Pente-Fino"):
            with st.spinner("Analisando cláusulas e cruzando com o seu DNA..."):
                time.sleep(2) # Simulação de tempo de leitura
                st.write(f"**Análise para:** {st.session_state.empresa['razao_social']}")
                
                # Simulação de lógica de negócio baseada no perfil preenchido
                if st.session_state.empresa['capital_social'] < 500000:
                    st.markdown(f"""
                    <div class="card critical">
                        <small style="color:#ff4b4b;">🚨 RISCO FINANCEIRO DETECTADO</small>
                        <h3>Exigência de Capital Social Incompatível</h3>
                        <p>O edital exige Capital Social de R$ 500.000,00 (Pág 18). Sua empresa possui apenas <b>R$ {st.session_state.empresa['capital_social']:,.2f}</b>.</p>
                        <b>Recomendação:</b> Formar consórcio ou impugnar a cláusula se for considerada restritiva.
                    </div>
                    """, unsafe_allow_html=True)
                
                if "ISO 9001" not in st.session_state.empresa['certificacoes']:
                    st.markdown("""
                    <div class="card critical">
                        <small style="color:#ff4b4b;">🚨 RISCO TÉCNICO DETECTADO</small>
                        <h3>Falta de Certificação Exigida</h3>
                        <p>Identificada a exigência de certificação <b>ISO 9001</b> no item 9.4 do edital. Você não possui esta certificação cadastrada.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("""
                <div class="card success-card">
                    <small style="color:#52c41a;">✅ REQUISITO ATENDIDO</small>
                    <h3>Habilitação Jurídica</h3>
                    <p>Nenhuma cláusula restritiva incomum encontrada na seção de habilitação jurídica e fiscal.</p>
                </div>
                """, unsafe_allow_html=True)

# ABA 3: ADVOGADO AI
with tab_juridico:
    st.subheader("⚖️ Gerador de Impugnações (Claude 3.5 Sonnet)")
    st.write("Redija peças com fundamentação jurídica impecável baseada na Lei 14.133/21.")
    
    tipo_doc = st.selectbox("Tipo de Peça", ["Impugnação ao Edital", "Recurso Administrativo", "Pedido de Esclarecimento"])
    texto_problema = st.text_area("Descreva a falha ou cole o trecho abusivo do edital:", height=150)
    
    if st.button("Gerar Peça Jurídica"):
        if not api_key:
            st.error("⚠️ Insira a sua API Key da Anthropic na barra lateral esquerda.")
        elif not texto_problema:
            st.warning("⚠️ Descreva o problema encontrado no edital para gerar a peça.")
        else:
            with st.spinner("Claude 3.5 pesquisando jurisprudência e redigindo a minuta..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    prompt = f"Você é um advogado sênior especialista em licitações públicas no Brasil (Lei 14.133/21). Redija uma {tipo_doc} focada no seguinte problema encontrado em um edital: '{texto_problema}'. A empresa cliente se chama {st.session_state.empresa['razao_social']}. Seja direto, formal, e cite jurisprudência do TCU ou princípios administrativos que embasem o pedido. Não invente números de acórdãos se não tiver certeza, foque nos princípios legais (ex: competitividade, razoabilidade)."
                    
                    response = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    st.markdown('<div class="card"><b>📄 Minuta Estruturada:</b></div>', unsafe_allow_html=True)
                    st.text_area("Copie o conteúdo abaixo:", value=response.content[0].text, height=400)
                except Exception as e:
                    st.error(f"Erro ao conectar com a API: {e}")

# ABA 4: ESPIÃO
with tab_espiao:
    st.subheader("🕵️ Espião de Concorrência")
    cnpj_rival = st.text_input("CNPJ ou Nome do Concorrente (Simulação):")
    if cnpj_rival and st.button("Analisar Histórico de Lances"):
        st.info(f"Mapeando comportamento de: {cnpj_rival}...")
        time.sleep(1)
        dados_grafico = pd.DataFrame({'Desconto Aplicado (%)': [0, 5, 12, 18, 20, 21, 21]}, index=[0, 5, 10, 15, 20, 25, 30])
        st.line_chart(dados_grafico)
        st.markdown(f"""
        <div class="card">
            <strong>Insight Estratégico:</strong><br>
            Este concorrente costuma abandonar o pregão ao atingir a margem de <b>21% de desconto</b>. 
            Prepare seu custo para cobrir esse valor nos minutos finais.
        </div>
        """, unsafe_allow_html=True)
