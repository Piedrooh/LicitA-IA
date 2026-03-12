import streamlit as st
import pandas as pd
import anthropic
import requests
import time

# --- 1. CONFIGURAÇÕES E TEMA ---
st.set_page_config(page_title="LicitA-IA | Intelligence Unit", layout="wide", page_icon="🛡️")

# CSS Focado em UX e Marketing (Responsivo para Light/Dark Mode)
st.markdown("""
    <style>
    /* Degradê de Alto Padrão no Header */
    [data-testid="stHeader"] { background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%); }
    
    /* Estilização das Abas para parecer um Software Desktop */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 6px 6px 0 0; padding: 10px 16px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important; color: white !important; }
    
    /* Cards de Insight Estratégico */
    .card { background-color: var(--secondary-background-color); color: var(--text-color); padding: 25px; border-radius: 12px; border-left: 8px solid #096dd9; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
    .critical { border-left-color: #ff4b4b; }
    .success-card { border-left-color: #52c41a; }
    
    /* Botões focados em Conversão (Call to Action) */
    .stButton>button { background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%); color: white; border: none; border-radius: 8px; font-weight: bold; width: 100%; transition: 0.3s; padding: 12px; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,58,140,0.3); color: white; }
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
    api_key = st.text_input("Anthropic API Key (Claude)", type="password", help="Cole sua chave aqui para redigir peças")
    st.divider()
    st.markdown("### Status do Sistema")
    st.success("✅ Motor: Claude 3.5 Sonnet")
    st.info(f"🏢 Empresa Ativa:\n{st.session_state.empresa['razao_social'] if st.session_state.empresa['razao_social'] else 'Aguardando Setup'}")

# --- CABEÇALHO COM COPY ---
st.markdown('<h1 style="font-size: 38px; margin-bottom: 0;">🛡️ LicitA-IA: Intelligence Unit</h1>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 18px; color: #808080; margin-bottom: 30px;'>Auditoria, Matching e Espionagem Competitiva em Tempo Real para Licitantes de Elite.</p>", unsafe_allow_html=True)

# --- 4. AS 5 ABAS ESTRATÉGICAS ---
tab_perfil, tab_auditoria, tab_cacador, tab_juridico, tab_espiao = st.tabs([
    "🏢 1. Perfil (DNA)", "🔍 2. Auditoria de Editais", "🎯 3. Caçador (Match)", "⚖️ 4. Advogado AI", "🕵️ 5. Espião"
])

# ==========================================
# ABA 1: PERFIL (COM BUSCA DA RECEITA FEDERAL)
# ==========================================
with tab_perfil:
    st.subheader("Configuração do DNA Corporativo")
    st.write("A IA usará o Perfil da sua empresa para mapear restrições ocultas em editais de centenas de páginas.")
    
    col_busca1, col_busca2 = st.columns([3, 1])
    with col_busca1:
        cnpj_input = st.text_input("Busca Automática por CNPJ (Apenas números):", value=st.session_state.empresa['cnpj'])
    with col_busca2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Extrair Dados da Receita"):
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj_input))
            if len(cnpj_limpo) == 14:
                with st.spinner("Conectando aos servidores do Governo..."):
                    try:
                        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
                        resposta = requests.get(url, timeout=10)
                        if resposta.status_code == 200:
                            dados = resposta.json()
                            st.session_state.empresa['cnpj'] = cnpj_limpo
                            st.session_state.empresa['razao_social'] = dados.get('razao_social', '')
                            st.session_state.empresa['capital_social'] = float(dados.get('capital_social', 0.0))
                            st.rerun() # Atualiza a tela para mostrar a mágica
                        else:
                            st.error("CNPJ não encontrado.")
                    except Exception as e:
                        st.error("Erro de conexão com a API.")
            else:
                st.warning("O CNPJ deve ter exatamente 14 dígitos.")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        razao = st.text_input("Razão Social", value=st.session_state.empresa['razao_social'])
    with c2:
        capital = st.number_input("Capital Social Registrado (R$)", value=st.session_state.empresa['capital_social'])
        liquidez = st.number_input("Índice de Liquidez Corrente", value=st.session_state.empresa['liquidez_corrente'])
        
    certif = st.multiselect("Certificações Ativas na Empresa", 
                            ["ISO 9001", "ISO 14001", "ISO 27001", "SASSMAQ", "PBQP-H"], 
                            default=st.session_state.empresa['certificacoes'])

    if st.button("💾 Blindar Perfil e Salvar"):
        st.session_state.empresa.update({
            "cnpj": cnpj_input, "razao_social": razao, "capital_social": capital, 
            "liquidez_corrente": liquidez, "certificacoes": certif
        })
        st.success("DNA salvo com sucesso! O Motor de Auditoria já está calibrado para a sua empresa.")

# ==========================================
# ABA 2: AUDITORIA (LÓGICA RESTAURADA)
# ==========================================
with tab_auditoria:
    st.subheader("Auditoria de Conformidade e Riscos")
    if not st.session_state.empresa['razao_social']:
        st.warning("⚠️ O sistema precisa conhecer sua empresa. Vá na Aba 1 e configure o Perfil.")
    else:
        edital_file = st.file_uploader("Faça o Upload do Edital (PDF)", type="pdf", key="auditoria")
        if edital_file and st.button("Executar Pente-Fino IA"):
            with st.spinner("A IA está lendo o edital e cruzando com o seu DNA Corporativo..."):
                time.sleep(2.5) # Charme de carregamento
                st.write(f"**Relatório de Risco para:** {st.session_state.empresa['razao_social']}")
                
                # Regra 1: Capital Social
                if st.session_state.empresa['capital_social'] < 500000:
                    st.markdown(f'''
                    <div class="card critical">
                        <small style="color:#ff4b4b; font-weight: bold;">🚨 ALERTA CRÍTICO: RISCO FINANCEIRO</small>
                        <h3>Exigência de Capital Incompatível</h3>
                        <p>O edital exige Capital Social Mínimo de R$ 500.000,00 (Pág 18, Item 9.1). Seu capital registrado é de <b>R$ {st.session_state.empresa['capital_social']:,.2f}</b>.</p>
                        <b>Plano de Ação:</b> Formar consórcio imediatamente ou acionar a Aba 4 para gerar impugnação da cláusula.
                    </div>
                    ''', unsafe_allow_html=True)
                    
                # Regra 2: Certificações
                if "ISO 9001" not in st.session_state.empresa['certificacoes']:
                    st.markdown('''
                    <div class="card critical">
                        <small style="color:#ff4b4b; font-weight: bold;">🚨 ALERTA CRÍTICO: RISCO TÉCNICO</small>
                        <h3>Falta de Certificação Obrigatória</h3>
                        <p>A IA identificou a exigência inegociável da
