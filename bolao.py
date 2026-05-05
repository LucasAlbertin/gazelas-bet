import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gazelas Bet 2026", layout="centered")
DB_NAME = "bolao.db"

# --- FUNÇÕES DE BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS jogos (
                    id INTEGER PRIMARY KEY,
                    time_a TEXT,
                    time_b TEXT,
                    data_hora TEXT,
                    gols_a INTEGER,
                    gols_b INTEGER)''')
                    
    c.execute('''CREATE TABLE IF NOT EXISTS palpites (
                    usuario TEXT,
                    jogo_id INTEGER,
                    palpite_a INTEGER,
                    palpite_b INTEGER,
                    PRIMARY KEY (usuario, jogo_id))''')
    
    c.execute('SELECT count(*) FROM jogos')
    if c.fetchone()[0] == 0:
        
        # --- SEUS JOGOS REAIS AQUI ---
        jogos_da_copa = [
            # Grupo A
            ('🇲🇽 México', '🇿🇦 África do Sul', '2026-06-11 16:00:00'),
            ('🇰🇷 Coreia do Sul', '🇨🇿 República Tcheca', '2026-06-11 20:00:00'),
            
            # Grupo B
            ('🇨🇦 Canadá', '🇧🇦 Bósnia', '2026-06-12 16:00:00'),
            
            # Grupo D
            ('🇺🇸 Estados Unidos', '🇵🇾 Paraguai', '2026-06-12 22:00:00')
        ]
        
        for time_a, time_b, data_hora in jogos_da_copa:
            c.execute("INSERT INTO jogos (time_a, time_b, data_hora) VALUES (?, ?, ?)", 
                      (time_a, time_b, data_hora))
                      
        conn.commit()
    
    conn.close()

def get_jogos():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM jogos", conn)
    conn.close()
    return df

def salvar_palpite(usuario, jogo_id, palpite_a, palpite_b):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO palpites (usuario, jogo_id, palpite_a, palpite_b) VALUES (?, ?, ?, ?)",
              (usuario, jogo_id, palpite_a, palpite_b))
    conn.commit()
    conn.close()

def get_palpites_usuario(usuario):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM palpites WHERE usuario = ?", conn, params=(usuario,))
    conn.close()
    return df

def get_todos_palpites_do_jogo(jogo_id):
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT usuario as Participante, palpite_a as 'Gols A', palpite_b as 'Gols B'
    FROM palpites
    WHERE jogo_id = ?
    ORDER BY usuario
    """
    df = pd.read_sql_query(query, conn, params=(jogo_id,))
    conn.close()
    return df

def atualizar_resultado_real(jogo_id, gols_a, gols_b):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE jogos SET gols_a = ?, gols_b = ? WHERE id = ?", (gols_a, gols_b, jogo_id))
    conn.commit()
    conn.close()

def calcular_ranking():
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT p.usuario, p.palpite_a, p.palpite_b, j.gols_a, j.gols_b
    FROM palpites p
    JOIN jogos j ON p.jogo_id = j.id
    WHERE j.gols_a IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    pontuacoes = {}
    
    for index, row in df.iterrows():
        user = row['usuario']
        pts = 0
        pA, pB = row['palpite_a'], row['palpite_b']
        rA, rB = row['gols_a'], row['gols_b']
        
        if pA == rA and pB == rB:
            pts = 3 
        elif (pA > pB and rA > rB) or (pA < pB and rA < rB) or (pA == pB and rA == rB):
            pts = 1 
            
        pontuacoes[user] = pontuacoes.get(user, 0) + pts
        
    return pd.DataFrame(list(pontuacoes.items()), columns=['Participante', 'Pontos']).sort_values(by='Pontos', ascending=False).reset_index(drop=True)

# --- INICIALIZAÇÃO ---
init_db()

# --- INTERFACE ---
st.title("⚽🦌 Gazelas Bet")

usuario = st.text_input("Digite seu nome para começar:", placeholder="Ex: Lucas")

if usuario:
    # AGORA TEMOS 4 ABAS
    tab1, tab2, tab3, tab4 = st.tabs(["⚽ Palpitar", "🏆 Ranking", "👀 Espiar Palpites", "⚙️ Admin"])

    # --- ABA 1: PALPITES ---
    with tab1:
        st.subheader(f"Palpites de {usuario}")
        jogos = get_jogos()
        palpites_user = get_palpites_usuario(usuario)
        
        for index, jogo in jogos.iterrows():
            st.markdown("---")
            hora_jogo = datetime.strptime(jogo['data_hora'], '%Y-%m-%d %H:%M:%S')
            agora = datetime.now()
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
            
            with col1:
                st.write(f"**{jogo['time_a']}**")
            with col5:
                st.write(f"**{jogo['time_b']}**")
            
            travado = agora >= hora_jogo
            
            palpite_atual = palpites_user[palpites_user['jogo_id'] == jogo['id']]
            val_a = int(palpite_atual.iloc[0]['palpite_a']) if not palpite_atual.empty else 0
            val_b = int(palpite_atual.iloc[0]['palpite_b']) if not palpite_atual.empty else 0

            if travado:
                with col2: st.warning(f"{val_a}", icon="🔒")
                with col3: st.write("X")
                with col4: st.warning(f"{val_b}", icon="🔒")
                st.caption(f"Jogo iniciado em {hora_jogo.strftime('%d/%m %H:%M')}.")
            else:
                with col2: p_a = st.number_input(f"A_{jogo['id']}", min_value=0, value=val_a, label_visibility="collapsed")
                with col3: st.write("X")
                with col4: p_b = st.number_input(f"B_{jogo['id']}", min_value=0, value=val_b, label_visibility="collapsed")
                
                if st.button(f"Salvar {jogo['time_a']} x {jogo['time_b']}", key=f"btn_{jogo['id']}"):
                    salvar_palpite(usuario, int(jogo['id']), p_a, p_b)
                    st.success("Palpite Salvo!")
                st.caption(f"Fecha em: {hora_jogo.strftime('%d/%m %H:%M')}")

    # --- ABA 2: RANKING ---
    with tab2:
        st.markdown("### *Gazelas Bet*⚽🦌")
        st.markdown("_Classificação_ 🏆\n")
        
        df_rank = calcular_ranking()
        
        if not df_rank.empty:
            texto_ranking = ""
            for index, row in df_rank.iterrows():
                posicao = index + 1
                nome = row['Participante']
                pontos = row['Pontos']
                
                if posicao == 1: emoji = "🥇"
                elif posicao == 2: emoji = "🥈"
                elif posicao == 3: emoji = "🥉"
                elif posicao <= 10: emoji = "▪️"
                else: emoji = "🔻"
                
                texto_ranking += f"{emoji}{posicao}. {nome} - {pontos} pts  \n"
            
            st.markdown(texto_ranking)
            st.code(texto_ranking, language="text")
            st.caption("👆 Copie o texto acima para mandar no grupo!")
        else:
            st.info("Nenhum ponto computado ainda.")

    # --- ABA 3: ESPIAR PALPITES ---
    with tab3:
        st.subheader("👀 O que a galera apostou?")
        st.write("Selecione um jogo para ver os palpites (Só são revelados após o início da partida).")
        
        jogos = get_jogos()
        # Cria uma lista formatada para a caixa de seleção
        opcoes_jogos = {jogo['id']: f"{jogo['time_a']} x {jogo['time_b']} ({datetime.strptime(jogo['data_hora'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M')})" for index, jogo in jogos.iterrows()}
        
        jogo_selecionado_id = st.selectbox("Escolha o jogo:", options=list(opcoes_jogos.keys()), format_func=lambda x: opcoes_jogos[x])
        
        if jogo_selecionado_id:
            jogo_info = jogos[jogos['id'] == jogo_selecionado_id].iloc[0]
            hora_jogo = datetime.strptime(jogo_info['data_hora'], '%Y-%m-%d %H:%M:%S')
            agora = datetime.now()
            
            # Trava anti-cópia: só mostra se o jogo já começou
            if agora >= hora_jogo:
                df_palpites_jogo = get_todos_palpites_do_jogo(jogo_selecionado_id)
                if not df_palpites_jogo.empty:
                    st.dataframe(df_palpites_jogo, hide_index=True, use_container_width=True)
                else:
                    st.info("Ninguém deu palpite para este jogo ainda.")
            else:
                st.warning("⚠️ Shhhh! O jogo ainda não começou. Os palpites estão ocultos para ninguém copiar!")

    # --- ABA 4: ADMIN ---
    with tab4:
        st.warning("Preencha os placares REAIS dos jogos (Apenas você deve usar isso)")
        jogos = get_jogos()
        for index, jogo in jogos.iterrows():
            c1, c2, c3, c4 = st.columns([2,1,1,2])
            with c1: st.write(f"{jogo['time_a']} x {jogo['time_b']}")
            
            r_a_atual = int(jogo['gols_a']) if pd.notnull(jogo['gols_a']) else 0
            r_b_atual = int(jogo['gols_b']) if pd.notnull(jogo['gols_b']) else 0
            
            with c2: novo_gols_a = st.number_input("Gols A", value=r_a_atual, key=f"admin_a_{jogo['id']}")
            with c3: novo_gols_b = st.number_input("Gols B", value=r_b_atual, key=f"admin_b_{jogo['id']}")
            with c4: 
                if st.button("Salvar Resultado Real", key=f"admin_btn_{jogo['id']}"):
                    atualizar_resultado_real(jogo['id'], novo_gols_a, novo_gols_b)
                    st.success("Placar real atualizado!")

else:
    st.info("👆 Digite seu nome acima para entrar no Bolão.")