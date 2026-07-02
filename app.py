import os
import sqlite3
import datetime

try:
    import streamlit as st  # type: ignore[import]
except ImportError as e:
    raise ImportError(
        "O módulo 'streamlit' não está instalado. Execute 'pip install streamlit' e tente novamente."
    ) from e

try:
    import pandas as pd  # type: ignore[import]
except ImportError as e:
    raise ImportError(
        "O módulo 'pandas' não está instalado. Execute 'pip install pandas' e tente novamente."
    ) from e

# --- 1. CONFIGURAÇÃO DO BANCO DE DADOS (SQLITE) ---
def conectar_banco():
    db_path = os.path.join(os.path.dirname(__file__), "historico_compras.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto TEXT,
            valor_unitario REAL,
            quantidade INTEGER,
            categoria TEXT,
            supermercado TEXT,
            data_compra TEXT
        )
    """)
    conn.commit()
    return conn, cursor

# --- 2. INTERFACE DO APLICATIVO (STREAMLIT) ---
st.set_page_config(page_title="Controle de Compras", page_icon="🛒", layout="centered")

st.title("🛒 Histórico de Compras Inteligente")
st.write("Preencha os campos abaixo para registrar seus gastos.")

# Listas de opções fixas
categorias_validas = ["Mercearia", "Hortifrúti", "Açougue", "Limpeza", "Higiene", "Bebidas", "Outros"]
supermercados_validos = ["Mercado do Bairro", "Hipermercado Centro", "Atacadão", "Outro"]

# Criação do Formulário na Tela
with st.form("formulario_compra", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        produto = st.text_input("Descrição do Produto:", placeholder="Ex: Arroz Integral 5kg")
        valor_unitario = st.number_input("Valor Unitário (R$):", min_value=0.01, step=0.01, format="%.2f")
        quantidade = st.number_input("Quantidade:", min_value=1, step=1)
        
    with col2:
        categoria = st.selectbox("Classe / Categoria:", categorias_validas)
        supermercado = st.text_input("Supermercado:", placeholder="Ex: Carrefour, Mercadinho do Zé")
        data_compra = st.date_input("Data da Compra:", datetime.datetime.today())

    botao_cadastrar = st.form_submit_button("Cadastrar Compra")

# --- 3. LÓGICA DE SALVAMENTO NO BANCO ---
if botao_cadastrar:
    if produto.strip() == "":
        st.error("Por favor, digite o nome do produto!")
    else:
        conn, cursor = conectar_banco()
        cursor.execute("""
            INSERT INTO compras (produto, valor_unitario, quantidade, categoria, supermercado, data_compra)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (produto, valor_unitario, quantidade, categoria, supermercado, str(data_compra)))
        conn.commit()
        conn.close()
        st.success(f"✓ '{produto}' salvo com sucesso no banco de dados!")
        # Recarrega a página para atualizar o histórico abaixo
        st.rerun()

# --- 4. EXIBIÇÃO DO HISTÓRICO E MÉTRICAS ---
st.write("---")
st.subheader("📊 Histórico de Compras Cadastradas")

conn, cursor = conectar_banco()
# Carrega os dados diretamente em um DataFrame do Pandas para facilitar o manuseio
df = pd.read_sql_query("SELECT * FROM compras ORDER BY data_compra DESC", conn)
conn.close()

if not df.empty:
    # Calcula o valor total de cada linha para as métricas
    df['Total'] = df['valor_unitario'] * df['quantidade']
    
    # Exibe métricas rápidas
    total_gasto = df['Total'].sum()
    total_itens = df['quantidade'].sum()
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Investido", f"R$ {total_gasto:.2f}")
    col_m2.metric("Qtd. Itens Comprados", f"{total_itens} un.")
    
    # Formatação amigável para exibição na tabela
    df_exibicao = df.rename(columns={
        'id': 'ID', 'produto': 'Produto', 'valor_unitario': 'Preço Unitário',
        'quantidade': 'Qtd', 'categoria': 'Categoria', 'supermercado': 'Supermercado',
        'data_compra': 'Data'
    })
    
    st.dataframe(df_exibicao[['ID', 'Produto', 'Preço Unitário', 'Qtd', 'Total', 'Categoria', 'Supermercado', 'Data']], hide_index=True)
else:
    st.info("Nenhuma compra cadastrada ainda. Comece preenchendo o formulário acima!")