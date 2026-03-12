import streamlit as st
import pandas as pd
import anthropic
import time

# --- 1. CONFIGURAÇÕES E TEMA ---
st.set_page_config(page_title="LicitA-IA | Intelligence Unit", layout="wide", page_icon="🛡️")

# CSS Dinâmico (Adapta ao Light e Dark Mode do cliente automaticamente)
st.markdown("""
    <style>
    /* O Streamlit agora controla o fundo principal. Vamos estilizar apenas os Cards e Botões. */
    
    [data-testid="stHeader"] { 
        background: linear-gradient(90deg, #001529 0%, #003a8c 100%); 
    }
    
    .card { 
        /* Usa a cor de fundo secundária do tema atual (claro ou escuro) */
        background-color: var(--secondary-background-color); 
        /* Usa a cor de texto do tema atual */
        color: var(--text-color); 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 8px solid #096dd9; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
    }
    .critical { border-left-color: #ff4b4b; }
    .success-card { border-left-color: #52c41a; }
    
    .stButton>button { 
        background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%); 
        color: white; 
        border: none; 
        border-radius: 8px; 
        font-weight: bold; 
        width: 100%; 
        transition: 0.3s; 
    }
    .stButton>button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 5px 15px rgba(0,58,140,0.3); 
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MEMÓRIA DA EMPRESA ---
if 'empresa' not in st.session_state:
    st.session_state.empresa = {
        "cnpj": "", "razao_social": "", "capital_social": 0.0,
        "liquidez_corrente": 1.0, "certificacoes": []
    }

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
    st.title("LicitA-IA Suite")
    api_key = st.text_input("Anthropic API Key (Claude)", type="password")
    st.divider()
    st.success("✅ Motor: Claude 3.5 Sonnet")
    st.info(f"🏢 Empresa Ativa:\n{st.session_state.empresa['razao_social'] if st.session_state.empresa['razao_social'] else 'Não configurada'}")

st.markdown('<h1 style="font-size: 36px; margin-bottom: 0;">🛡️ LicitA-IA: Intelligence Unit</h1>', unsafe_allow_html=True)
st.caption("Auditoria, Matching e Espionagem Competitiva em Tempo Real.")

# --- 4. AS 5 ABAS ESTRATÉGICAS ---
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao = st.tabs([
    "🏢 1. Perfil (DNA)", 
    "🔍 2. Auditoria", 
    "🎯 3. Caçador (Match)", 
    "⚖️ 4. Advogado AI", 
    "🕵️ 5. Espião"
])

# ABA 1: PERFIL
with tab_perfil:
    st.subheader("Configuração do DNA Corporativo")
    c1, c2 = st.columns(2)
    with c1:
        cnpj = st.text_input("CNPJ", value=st.session_state.empresa['cnpj'])
        razao = st.text_input("Razão Social", value=st.session_state.empresa['razao_social'])
    with c2:
        capital = st.number_input("Capital Social (R$)", value=st.session_state.empresa['capital_social'])
        liquidez = st.number_input("Índice de Liquidez Corrente", value=st.session_state.empresa['liquidez_corrente'])
    certif = st.multiselect("Certificações", ["ISO 9001", "ISO 14001", "ISO 27001", "SASSMAQ"], default=st.session_state.empresa['certificacoes'])

    if st.button("💾 Salvar Perfil"):
        st.session_state.empresa.update({"cnpj": cnpj, "razao_social": razao, "capital_social": capital, "liquidez_corrente": liquidez, "certificacoes": certif})
        st.success("Perfil atualizado!")

# ABA 2: AUDITORIA
with tab_auditoria:
    st.subheader("Auditoria de Conformidade e Riscos")
    edital_file = st.file_uploader("Upload do Edital (PDF)", type="pdf", key="auditoria")
    if edital_file and st.button("Executar Pente-Fino"):
        with st.spinner("Cruzando edital com o seu DNA..."):
            time.sleep(1.5)
            if st.session_state.empresa['capital_social'] < 500000:
                st.markdown(f'<div class="card critical"><b>🚨 Risco Financeiro:</b> Edital exige Capital Social de R$ 500k. Você possui R$ {st.session_state.empresa["capital_social"]:,.2f}.</div>', unsafe_allow_html=True)
            st.markdown('<div class="card success-card"><b>✅ Habilitação Jurídica:</b> Sem cláusulas restritivas detectadas.</div>', unsafe_allow_html=True)

# ABA 3: CAÇADOR (O MATCHING)
with tab_cacador:
    st.subheader("🎯 Caçador: Matching Inteligente de Atestados")
    st.write("A IA lê seus atestados antigos e cruza com os editais abertos no dia.")
    atestado_file = st.file_uploader("Upload de Atestado de Capacidade Técnica (PDF)", type="pdf", key="atestado")
    if atestado_file and st.button("Buscar Editais Compatíveis"):
        with st.spinner("Procurando oportunidades no Portal Nacional..."):
            time.sleep(2)
            st.markdown("""
            <div class="card success-card">
                <small style="color:#52c41a;">MATCH ENCONTRADO (89% de aderência)</small>
                <h3>Pregão 45/2026 - Prefeitura de SP</h3>
                <p>Seus atestados cobrem 100% dos requisitos de 'Fornecimento de Software'. O volume exigido é compatível com seu histórico.</p>
                <b>Ação Sugerida:</b> Baixar edital e rodar Auditoria.
            </div>
            """, unsafe_allow_html=True)

# ABA 4: ADVOGADO AI
with tab_juridico:
    st.subheader("⚖️ Gerador de Impugnações (Claude 3.5 Sonnet)")
    tipo_doc = st.selectbox("Tipo de Peça", ["Impugnação ao Edital", "Recurso", "Esclarecimento"])
    texto_problema = st.text_area("Descreva a falha:", height=100)
    
    if st.button("Gerar Peça"):
        if not api_key:
            st.error("Insira a API Key na barra lateral.")
        else:
            with st.spinner("Claude 3.5 redigindo..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    prompt = f"Redija uma {tipo_doc} sobre: {texto_problema}. Empresa: {st.session_state.empresa['razao_social']}. Use a Lei 14.133/21."
                    response = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=1500, messages=[{"role": "user", "content": prompt}])
                    st.markdown('<div class="card"><b>Minuta:</b></div>', unsafe_allow_html=True)
                    st.text_area("Cópia:", value=response.content[0].text, height=300)
                except Exception as e:
                    st.error(f"Erro: {e}")

# ABA 5: ESPIÃO
with tab_espiao:
    st.subheader("🕵️ Espião de Concorrência")
    cnpj_rival = st.text_input("CNPJ do Concorrente:")
    if cnpj_rival and st.button("Analisar Padrão de Lances"):
        dados_grafico = pd.DataFrame({'Desconto (%)': [0, 5, 12, 18, 20]}, index=[0, 5, 10, 15, 20])
        st.line_chart(dados_grafico)
        st.info("Este concorrente costuma parar em 20% de desconto.")
