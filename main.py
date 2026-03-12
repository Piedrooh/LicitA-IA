import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import json
import requests
import time
import anthropic

# --- 1. CONFIGURAÇÃO DE TEMA E INTERFACE ---
st.set_page_config(page_title="LicitA-IA | Intelligence Unit", layout="wide", initial_sidebar_state="expanded", page_icon="🛡️")

st.markdown("""
<style>
/* Fundo Absoluto e Clean */
.stApp { background-color: #FFFFFF; color: #1E1E1E; }
/* Header Premium */
[data-testid="stHeader"] { background: linear-gradient(90deg, #001529 0%, #003a8c 50%, #096dd9 100%); height: 3rem; }
/* Abas Estilo Software Desktop */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 6px 6px 0 0; padding: 10px 16px; font-weight: 600; color: #595959; }
.stTabs [aria-selected="true"] { background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%) !important; color: white !important; }
/* Cards de Risco e Insights */
.risk-card { background-color: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 6px solid #096dd9; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #1E1E1E;}
.critical { border-left-color: #ff4b4b; }
.warning { border-left-color: #ffa500; }
.success { border-left-color: #52c41a; }
/* Certificações Visuais */
.cert-card { background: linear-gradient(90deg, #f0f8ff 0%, #e6f7ff 100%); padding: 12px 18px; border-radius: 8px; margin-bottom: 10px; display: flex; align-items: center; border: 1px solid #bae0ff; color: #003a8c; font-weight: 600; font-size: 15px; }
/* Botões de Conversão */
.stButton>button { background: linear-gradient(90deg, #096dd9 0%, #003a8c 100%); color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: 600; transition: 0.3s; width: 100%; }
.stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,58,140,0.3); color: white; }
</style>
""", unsafe_allow_html=True)

# --- 2. ESTADO DA SESSÃO ---
if 'empresa' not in st.session_state:
    st.session_state.empresa = {
        "cnpj": "", "razao_social": "", "capital_social": 0.0,
        "liquidez_corrente": 1.0, "certificacoes": [], "atestados": ""
    }
for k in ["res_auditoria", "res_espiao"]:
    if k not in st.session_state: st.session_state[k] = None

# --- 3. FUNÇÕES BASE ---
def extrair_texto_pdf(file) -> str:
    file.seek(0)
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([f"[PÁG {i+1}]\n{doc[i].get_text()}" for i in range(len(doc))])
    except Exception as e:
        st.error(f"Erro no PDF: {e}")
        return ""

def render_risk_card(titulo, subtitulo, corpo, classe=""):
    cor = {"critical": "#ff4b4b", "warning": "#ffa500", "success": "#52c41a"}.get(classe, "#096dd9")
    st.markdown(f'<div class="risk-card {classe}"><small style="color:{cor}; font-weight:700;">{subtitulo}</small><h4 style="margin: 6px 0 8px 0; color:#002766;">{titulo}</h4><p style="margin:0; color:#444;">{corpo.replace(chr(10), "<br>")}</p></div>', unsafe_allow_html=True)

def render_cert(cert):
    icones = {"ISO 9001": "✅", "ISO 14001": "🌱", "ISO 27001": "🔒", "SASSMAQ": "🚒", "PBQP-H": "🏗️", "OHSAS 18001": "⛑️"}
    st.markdown(f'<div class="cert-card"><span style="font-size: 20px; margin-right: 12px;">{icones.get(cert, "📄")}</span> {cert}</div>', unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.title("LicitA-IA Control")
    api_key = st.text_input("API Key (Claude / Anthropic)", type="password")
    if api_key: st.success("✅ Motor: Claude 3.5 Sonnet ativo")
    else: st.warning("⚠️ Insira a API Key para usar a IA")
    st.info(f"🏢 Empresa Ativa:\n{st.session_state.empresa['razao_social'] if st.session_state.empresa['razao_social'] else 'Aguardando Setup'}")

# --- CABEÇALHO ---
st.markdown('<h1 style="font-size:38px; margin-bottom:0; color:#002766;">🛡️ Unidade de Inteligência LicitA-IA</h1>', unsafe_allow_html=True)
st.markdown("<p style='font-size:18px; color:#595959; margin-bottom:30px;'>Auditoria de Riscos, Matchmaking e Redação Jurídica para Licitantes de Alta Performance.</p>", unsafe_allow_html=True)

# --- 5. ABAS ---
t_perfil, t_auditoria, t_cacador, t_juridico, t_espiao = st.tabs(["🏢 1. Perfil", "🔍 2. Auditoria", "🎯 3. Caçador", "⚖️ 4. Advogado AI", "🕵️ 5. Espião"])

# --- ABA 1: PERFIL ---
with t_perfil:
    c1, c2 = st.columns([3, 1])
    with c1: cnpj_in = st.text_input("Busca Automática por CNPJ (Somente Números):", value=st.session_state.empresa["cnpj"])
    with c2:
        st.write("")
        if st.button("🔍 Extrair Dados"):
            cnpj_num = "".join(filter(str.isdigit, cnpj_in))
            if len(cnpj_num) == 14:
                try:
                    resp = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_num}", timeout=10)
                    if resp.status_code == 200:
                        d = resp.json()
                        st.session_state.empresa.update({"cnpj": cnpj_num, "razao_social": d.get("razao_social", ""), "capital_social": float(d.get("capital_social") or 0.0)})
                        st.rerun()
                except: st.error("Erro na busca da Receita.")
            else: st.warning("Digite 14 números.")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        razao = st.text_input("Razão Social", value=st.session_state.empresa["razao_social"])
        cap = st.number_input("Capital Social (R$)", value=float(st.session_state.empresa["capital_social"]))
    with col2:
        liq = st.number_input("Liquidez Corrente", value=float(st.session_state.empresa["liquidez_corrente"]))
    
    certif = st.multiselect("Certificações Ativas", ["ISO 9001", "ISO 14001", "ISO 27001", "SASSMAQ", "PBQP-H", "OHSAS 18001"], default=st.session_state.empresa["certificacoes"])
    if certif:
        cc = st.columns(3)
        for i, c in enumerate(sorted(certif)):
            with cc[i%3]: render_cert(c)
            
    atestados = st.text_area("Atestados de Capacidade Técnica:", value=st.session_state.empresa.get("atestados", ""), height=80)
    
    if st.button("💾 Blindar Perfil e Salvar"):
        st.session_state.empresa.update({"cnpj": "".join(filter(str.isdigit, cnpj_in)), "razao_social": razao, "capital_social": cap, "liquidez_corrente": liq, "certificacoes": certif, "atestados": atestados})
        st.success("✅ DNA salvo com sucesso!")

# --- ABA 2: AUDITORIA ---
with t_auditoria:
    file_edital = st.file_uploader("Upload Edital (PDF)", type="pdf")
    if file_edital and st.button("🚀 INICIAR AUDITORIA IA"):
        if not api_key: st.error("Insira a API Key na barra lateral!")
        else:
            with st.status("Auditando Edital...", expanded=True) as status:
                st.write("📄 Extraindo texto do PDF...")
                texto = extrair_texto_pdf(file_edital)
                st.write("🧠 Cruzando com a Lei 14.133/21...")
                client = anthropic.Anthropic(api_key=api_key)
                
                sys_prompt = "Você é auditor de licitações. Analise o edital e retorne APENAS um JSON válido: {\"riscos\": [{\"severidade\": \"CRITICO\" ou \"ATENCAO\", \"categoria\": \"Habilitação, Qualificação, etc\", \"pagina\": \"Ex: Pág 14\", \"titulo\": \"...\", \"descricao\": \"...\", \"acao\": \"...\"}]}"
                user_prompt = f"PERFIL DA EMPRESA:\n{st.session_state.empresa}\n\nTEXTO DO EDITAL:\n{texto[:80000]}"
                
                try:
                    r = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=2500, system=sys_prompt, messages=[{"role": "user", "content": user_prompt}])
                    clean_json = r.content[0].text.strip().replace("```json", "").replace("```", "")
                    st.session_state.res_auditoria = json.loads(clean_json)
                    status.update(label="✅ Análise Concluída!", state="complete", expanded=False)
                except Exception as e: st.error(f"Falha na IA: Não foi possível processar o documento. {e}")
                
    if st.session_state.res_auditoria:
        st.markdown("---")
        riscos = st.session_state.res_auditoria.get("riscos", [])
        m1, m2 = st.columns(2)
        m1.metric("Riscos Críticos", len([r for r in riscos if r['severidade']=="CRITICO"]), delta_color="inverse")
        m2.metric("Pontos de Atenção", len([r for r in riscos if r['severidade']=="ATENCAO"]))
        for r in riscos:
            c_class = "critical" if r['severidade'] == "CRITICO" else "warning"
            render_risk_card(r['titulo'], f"{r['severidade']} | {r['pagina']} | {r['categoria']}", f"{r['descricao']}\n\n💡 Ação Recomendada: {r.get('acao', '')}", c_class)

# --- ABA 3: CAÇADOR ---
with t_cacador:
    c1, c2 = st.columns(2)
    with c1: st.text_input("Segmento de Interesse (Ex: Uniformes, TI):")
    with c2: st.selectbox("Estado (UF):", ["SP", "RJ", "MG", "PR", "SC", "RS", "DF", "BA"])
    if st.button("🚀 Ativar Radar de Mercado"):
        with st.spinner("Procurando cruzamentos de atestados..."):
            time.sleep(1.5) # Simulação visual de busca para o MVP
            render_risk_card("Pregão Eletrônico 45/2026 - Tribunal de Justiça", "🎯 MATCH PERFEITO (94%)", f"Segmento totalmente compatível. O volume exigido é aderente aos atestados da empresa {st.session_state.empresa['razao_social']}.", "success")

# --- ABA 4: ADVOGADO AI ---
with t_juridico:
    tipo = st.selectbox("Peça Jurídica:", ["Impugnação ao Edital", "Recurso Administrativo", "Pedido de Esclarecimento"])
    fund = st.text_area("Fundamento (Descreva o erro do edital):", height=100)
    if st.button("⚖️ Redigir Peça Completa"):
        if not api_key: st.warning("Insira a API Key na lateral.")
        elif not fund: st.warning("Descreva o problema.")
        else:
            with st.spinner("Estruturando peça jurídica com base na Lei 14.133/21..."):
                client = anthropic.Anthropic(api_key=api_key)
                prompt = f"Redija uma {tipo} para a empresa {st.session_state.empresa['razao_social']}. Problema base a ser atacado: {fund}. Fundamente rigorosamente na Lei 14.133/21. Entregue a peça pronta para assinatura."
                try:
                    resp = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=2500, messages=[{"role": "user", "content": prompt}])
                    st.text_area("Minuta Pronta (Copie e cole no Word):", value=resp.content[0].text, height=450)
                except Exception as e: st.error(f"Erro: {e}")

# --- ABA 5: ESPIÃO ---
with t_espiao:
    cnpj_rival = st.text_input("CNPJ do Concorrente (Para rastreio):")
    if st.button("🕵️ Analisar Comportamento do Concorrente"):
        with st.spinner("Buscando dados no portal de transparência..."):
            time.sleep(1.5) # Simulação visual para o MVP
            render_risk_card("Padrão de Lances Identificado", "⚠️ ALERTA DE DUMPING", f"O CNPJ {cnpj_rival} possui um histórico de agressividade em lances, costumando abandonar a disputa apenas no desconto máximo de 21%.", "warning")
