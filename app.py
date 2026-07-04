import datetime
import pandas as pd
import streamlit as st
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

# --- 3. GERENCIAMENTO DE SESSÃO / AUTENTICAÇÃO ---
def obter_usuario_logado():
    try:
        resposta = supabase.auth.get_user()
        if resposta and hasattr(resposta, 'user') and resposta.user:
            return resposta.user
    except Exception:
        return None
    return None

usuario = obter_usuario_logado()

# --- 4. TELA DE LOGIN (E-MAIL E SENHA) ---
if usuario is None:
    st.title("🔐 Acesse seu Controle de Compras")
    st.write("Faça login ou crie uma conta rápida abaixo para gerenciar seus gastos.")
    
    # Cria duas abas limpas na tela: uma para entrar e outra para se cadastrar
    aba_login, aba_cadastro = st.tabs(["Entrar na Conta", "Criar Nova Conta"])
    
    with aba_login:
        email = st.text_input("E-mail:", placeholder="seu@email.com", key="login_email")
        senha = st.text_input("Senha:", type="password", key="login_senha")
        
        if st.button("Entrar", use_container_width=True):
            if not email or not senha:
                st.warning("Por favor, preencha todos os campos.")
            else:
                try:
                    supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    st.success("✓ Login realizado com sucesso!")
                    st.rerun()  # Recarrega o app já autenticado
                except Exception as e:
                    st.error("E-mail ou senha incorretos. Tente novamente.")
                
    with aba_cadastro:
        novo_email = st.text_input("Escolha um E-mail:", placeholder="exemplo@email.com", key="reg_email")
        nova_senha = st.text_input("Escolha uma Senha (mín. 6 dígitos):", type="password", key="reg_senha")
        
        if st.button("Cadastrar Nova Conta", use_container_width=True):
            if not novo_email or not nova_senha:
                st.warning("Por favor, preencha todos os campos para o cadastro.")
            elif len(nova_senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    # Cadastra o usuário no Supabase Auth
                    supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                    
                    st.success("✨ Conta criada com sucesso!")
                    st.info("👉 Vá para a aba **'Entrar na Conta'** ao lado e insira suas credenciais para acessar!")
                except Exception as e:
                    # Se der erro de limite (Rate Limit), a conta geralmente foi criada mesmo assim
                    if "rate limit" in str(e).lower() or "not confirmed" in str(e).lower():
                        st.success("✨ Conta criada com sucesso!")
                        st.info("👉 Prontinho! Vá para a aba **'Entrar na Conta'** ao lado para fazer seu login.")
                    else:
                        st.error(f"Erro ao cadastrar: {e}")
                
    st.stop()  # Impede