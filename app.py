import datetime
import pandas as pd
import streamlit as st
import uuid  # Adicionado para tratar o formato de ID aceito pelo banco
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Controle de Compras", page_icon="🛒", layout="centered")

# --- 2. CONEXÃO COM O SUPABASE ---
SUPABASE_URL = "https://cdavsoxdjphqbqyglpme.supabase.co"
SUPABASE_KEY = "sb_publishable_IfkGaoejXNbnb12BHW5InA_REiKH90t"

@st.cache_resource
def inicializar_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = inicializar_supabase()

# --- 3. GERENCIAMENTO DE SESSÃO CUSTOMIZADO ---
if "usuario_email" not in st.session_state:
    st.session_state["usuario_email"] = None

# --- 4. TELA DE LOGIN (BANCO DE DADOS CUSTOMIZADO) ---
if st.session_state["usuario_email"] is None:
    st.title("🔐 Acesse seu Controle de Compras")
    st.write("Faça login ou crie uma conta rápida abaixo para gerenciar seus gastos.")
    
    aba_login, aba_cadastro = st.tabs(["Entrar na Conta", "Criar Nova Conta"])
    
    with aba_login:
        email = st.text_input("E-mail:", placeholder="seu@email.com", key="login_email").strip().lower()
        senha = st.text_input("Senha:", type="password", key="login_senha")
        
        if st.button("Entrar", use_container_width=True):
            if not email or not senha:
                st.warning("Por favor, preencha todos os campos.")
            else:
                try:
                    busca = supabase.table("usuarios_app").select("*").eq("email", email).eq("senha", senha).execute()
                    if busca.data:
                        st.session_state["usuario_email"] = email
                        st.success("✓ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos. Tente novamente.")
                except Exception as e:
                    st.error(f"Erro ao conectar com o banco: {e}")
                
    with aba_cadastro:
        novo_email = st.text_input("Escolha um E-mail:", placeholder="exemplo@email.com", key="reg_email").strip().lower()
        nova_senha = st.text_input("Escolha uma Senha (mín. 6 dígitos):", type="password", key="reg_senha")
        
        if st.button("Cadastrar e Entrar", use_container_width=True):
            if not novo_email or not nova_senha:
                st.warning("Por favor, preencha todos os campos para o cadastro.")
            elif len(nova_senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    dados_usuario = {"email": novo_email, "senha": nova_senha}
                    supabase.table("usuarios_app").insert(dados_usuario).execute()
                    
                    st.session_state["usuario_email"] = novo_email
                    st.success("✨ Conta criada com sucesso!")
                    st.rerun()
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                        st.error("Este e-mail já está cadastrado! Use a aba de Login.")
                    else:
                        st.error(f"Erro ao cadastrar: {e}")
                
    st.stop()

# --- 5. PAINEL DO USUÁRIO AUTENTICADO ---
email_texto = st.session_state["usuario_email"]
# Transforma o e-mail em um formato UUID fixo e estável para a tabela "compras" aceitar sem erros
usuario_atual = str(uuid.uuid5(uuid.NAMESPACE_DNS, email_texto)) if email_texto else None

with st.sidebar:
    st.write(f"Conectado como: \n**{st.session_state['usuario_email']}**")
    if st.button("Sair / Mudar de Conta", use_container_width=True):
        st.session_state["usuario_email"] = None
        st.rerun()

st.title("🛒 Meu Histórico de Compras Inteligente")
st.write("Preencha os campos abaixo para registrar seus gastos diretamente na sua conta.")

categorias_validas = ["Mercearia", "Hortifrúti", "Açougue", "Limpeza", "Higiene", "Bebidas", "Outros"]

# --- 6. FORMULÁRIO DE CADASTRO DE COMPRA ---
with st.form("formulario_compra", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        produto = st.text_input("Descrição do Produto:", placeholder="Ex: Arroz Integral 5kg")
        valor_unitario = st.number_input("Valor Unitário (R$):", min_value=0.01, step=0.01, format="%.2f")
        quantidade = st.number_input("Quantidade:", min_value=1, step=1)
        
    with col2:
        categoria = st.selectbox("Classe / Categoria:", categorias_validas)
        supermercado = st.text_input("Supermercado:", placeholder="Ex: Carrefour, Mercadinho")
        data_compra = st.date_input("Data da Compra:", datetime.date.today())

    botao_cadastrar = st.form_submit_button("Cadastrar Compra")

if botao_cadastrar:
    if produto.strip() == "":
        st.error("Por favor, digite o nome do produto!")
    else:
        dados_compra = {
            "produto": produto,
            "valor_unitario": valor_unitario,
            "quantidade": quantidade,
            "categoria": categoria,
            "supermercado": supermercado,
            "data_compra": str(data_compra),
            "user_id": usuario_atual
        }
        
        try:
            supabase.table("compras").insert(dados_compra).execute()
            st.success(f"✓ '{produto}' salvo com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar no Supabase: {e}")

# --- 7. EXIBIÇÃO DO HISTÓRICO PERSONALIZADO ---
st.write("---")
st.subheader("📊 Meu Histórico de Compras")

try:
    resposta = supabase.table("compras").select("*").eq("user_id", usuario_atual).order("data_compra", desc=True).execute()
    dados_banco = resposta.data
except Exception as e:
    st.error(f"Erro ao buscar dados do Supabase: {e}")
    dados_banco = []

df = pd.DataFrame(dados_banco)

if not df.empty:
    df['Total'] = df['valor_unitario'] * df['quantidade']
    total_gasto = df['Total'].sum()
    total_itens = df['quantidade'].sum()
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Investido", f"R$ {total_gasto:.2f}")
    col_m2.metric("Qtd. Itens Comprados", f"{total_itens} un.")
    
    df_exibicao = df.rename(columns={
        'id': 'ID', 'produto': 'Produto', 'valor_unitario': 'Preço Unitário',
        'quantidade': 'Qtd', 'categoria': 'Categoria', 'supermercado': 'Supermercado',
        'data_compra': 'Data'
    })
    
    st.info("💡 **Como apagar um item:** Selecione a linha desejada na tabela abaixo e aperte a tecla **Delete**.")
    
    dados_editados = st.data_editor(
        df_exibicao[['ID', 'Produto', 'Preço Unitário', 'Qtd', 'Total', 'Categoria', 'Supermercado', 'Data']],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        disabled=["ID", "Produto", "Preço Unitário", "Qtd", "Total", "Categoria", "Supermercado", "Data"],
        key="editor_compras"
    )
    
    if "editor_compras" in st.session_state:
        linhas_deletadas = st.session_state["editor_compras"].get("deleted_rows", [])
        if linhas_deletadas:
            for indice_linha in linhas_deletadas:
                id_deletado = int(df_exibicao.iloc[indice_linha]['ID'])
                try:
                    supabase.table("compras").delete().eq("id", id_deletado).execute()
                except Exception as e:
                    st.error(f"Erro ao deletar: {e}")
            
            st.success("Item removido do seu histórico!")
            st.rerun()
else:
    st.info("Nenhuma compra registrada ainda.")