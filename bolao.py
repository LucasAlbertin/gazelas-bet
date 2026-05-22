import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client

# =========================================================
# CONFIGURAÇÃO INICIAL & TEMA MESTRE
# =========================================================
st.set_page_config(
    page_title="Gazelas Bet 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Injeção do seu CSS Moderno com os ajustes de tamanho das métricas
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0B1020, #111827);
    color: white;
}
h1, h2, h3, h4 {
    color: white !important;
}
p, span, label {
    color: #E2E8F0 !important;
}
.card {
    background: #151C32;
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 15px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
}
.rank-card {
    background: #151C32;
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}
.gold {
    border: 2px solid gold;
    box-shadow: 0 0 25px rgba(255,215,0,0.25);
}
.stButton > button {
    width: 100%;
    border-radius: 14px;
    border: none;
    background: linear-gradient(90deg,#00E676,#00C853);
    color: black !important;
    font-weight: bold;
    padding: 12px;
    transition: 0.3s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,230,118,0.35);
}
.stNumberInput input {
    text-align: center;
    border-radius: 12px !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 16px;
    font-weight: 700;
}

/* --- DASHBOARD COMPACTO --- */
div[data-testid="metric-container"] {
    background: #151C32;
    border-radius: 18px;
    padding: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}
div[data-testid="stMetricValue"] {
    font-size: 24px !important; 
    font-weight: bold;
}
div[data-testid="stMetricLabel"] {
    font-size: 14px !important; 
    color: #A0AEC0 !important;
}
</style>
""", unsafe_allow_html=True)

# Conexão com Supabase (Lendo dos Secrets para sua segurança)
SUPABASE_URL = "https://busfsfrcodfnjgkizfme.supabase.co"
SUPABASE_KEY = "sb_publishable_tnx9hoG8lqnwvS2Po02GWQ_d9EcB2AL"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USER = "Admin"
ADMIN_PASS = "gazelas123" 

# =========================================================
# FUNÇÕES DE BANCO DE DADOS (SUPABASE)
# =========================================================

@st.cache_data(ttl=600)
def get_jogos():
    res = supabase.table("jogos").select("*").order("data_hora").execute()
    return pd.DataFrame(res.data)

def salvar_palpite(usuario, jogo_id, p_a, p_b):
    data = {"usuario": usuario, "jogo_id": jogo_id, "palpite_a": p_a, "palpite_b": p_b}
    supabase.table("palpites").upsert(data).execute()

def criar_usuario(nome, senha):
    try:
        supabase.table("usuarios").insert({"nome": nome, "senha": senha}).execute()
        return True
    except: 
        return False

def verificar_login(nome, senha):
    res = supabase.table("usuarios").select("*").eq("nome", nome).eq("senha", senha).execute()
    return len(res.data) > 0

def get_todos_usuarios():
    res = supabase.table("usuarios").select("nome, senha").execute()
    return pd.DataFrame(res.data)

def atualizar_resultado_real(j_id, g_a, g_b):
    supabase.table("jogos").update({"gols_a": g_a, "gols_b": g_b}).eq("id", j_id).execute()

def adicionar_novo_jogo(time_a, time_b, data_hora, fase):
    data = {"time_a": time_a, "time_b": time_b, "data_hora": data_hora, "fase": fase}
    supabase.table("jogos").insert(data).execute()

def reset_banco_dados():
    supabase.table("palpites").delete().neq("usuario", "").execute()
    supabase.table("usuarios").delete().neq("nome", "").execute()
    supabase.table("jogos").update({"gols_a": None, "gols_b": None}).neq("time_a", "").execute()

def get_palpites_usuario(usuario):
    res = supabase.table("palpites").select("*").eq("usuario", usuario).execute()
    if not res.data:
        return pd.DataFrame(columns=['usuario', 'jogo_id', 'palpite_a', 'palpite_b'])
    return pd.DataFrame(res.data)

def get_todos_palpites_do_jogo(jogo_id):
    res = supabase.table("palpites").select("usuario, palpite_a, palpite_b").eq("jogo_id", jogo_id).execute()
    if not res.data:
        return pd.DataFrame(columns=['Participante', 'Gols A', 'Gols B'])
    df = pd.DataFrame(res.data)
    df.rename(columns={'usuario': 'Participante', 'palpite_a': 'Gols A', 'palpite_b': 'Gols B'}, inplace=True)
    return df

def calcular_ranking():
    usuarios_res = supabase.table("usuarios").select("nome").execute()
    jogos_res = supabase.table("jogos").select("*").not_.is_("gols_a", "null").execute()
    palpites_res = supabase.table("palpites").select("*").execute()
    
    pontos = {u['nome']: 0 for u in usuarios_res.data}
    jogos_dict = {j['id']: j for j in jogos_res.data}
    
    for p in palpites_res.data:
        if p['jogo_id'] in jogos_dict:
            j = jogos_dict[p['jogo_id']]
            pa, pb = int(p['palpite_a']), int(p['palpite_b'])
            ra, rb = int(j['gols_a']), int(j['gols_b'])
            
            pts = 0
            if pa == ra and pb == rb: pts = 3
            elif (pa > pb and ra > rb) or (pa < pb and ra < rb) or (pa == pb and ra == rb): pts = 1
            if p['usuario'] in pontos: pontos[p['usuario']] += pts
            
    df = pd.DataFrame(list(pontos.items()), columns=['Participante', 'Pontos']).sort_values(by='Pontos', ascending=False).reset_index(drop=True)
    return df

def calcular_tabela_copa():
    grupos = {
        'Grupo A': ['🇲🇽 México', '🇿🇦 África do Sul', '🇰🇷 Coreia do Sul', '🇨🇿 República Tcheca'],
        'Grupo B': ['🇨🇦 Canadá', '🇧🇦 Bósnia', '🇶🇦 Catar', '🇨🇭 Suíça'],
        'Grupo C': ['🇧🇷 Brasil', '🇲🇦 Marrocos', '🇭🇹 Haiti', '🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia'],
        'Grupo D': ['🇺🇸 Estados Unidos', '🇵🇾 Paraguai', '🇦🇺 Austrália', '🇹🇷 Turquia'],
        'Grupo E': ['🇩🇪 Alemanha', '🇨🇼 Curaçau', '🇨🇮 Costa do Marfim', '🇪🇨 Equador'],
        'Grupo F': ['🇳🇱 Holanda', '🇯🇵 Japão', '🇸🇪 Suécia', '🇹🇳 Tunísia'],
        'Grupo G': ['🇧🇪 Bélgica', '🇪🇬 Egito', '🇮🇷 Irã', '🇳🇿 Nova Zelândia'],
        'Grupo H': ['🇪🇸 Espanha', '🇨🇻 Cabo Verde', '🇸🇦 Arábia Saudita', '🇺🇾 Uruguai'],
        'Grupo I': ['🇫🇷 França', '🇸🇳 Senegal', '🇮🇶 Iraque', '🇳🇴 Noruega'],
        'Grupo J': ['🇦🇹 Áustria', '🇯🇴 Jordânia', '🇦🇷 Argentina', '🇩🇿 Argélia'],
        'Grupo K': ['🇵🇹 Portugal', '🇨🇩 Congo', '🇺🇿 Uzbequistão', '🇨🇴 Colômbia'],
        'Grupo L': ['🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra', '🇭🇷 Croácia', '🇬🇭 Gana', '🇵🇦 Panamá']
    }
    res = supabase.table("jogos").select("time_a, time_b, gols_a, gols_b").not_.is_("gols_a", "null").execute()
    jogos_realizados = pd.DataFrame(res.data)
    tabela = {}
    for grupo, times in grupos.items():
        for time in times:
            tabela[time] = {'Grupo': grupo, 'Time': time, 'Pts': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0}
    if not jogos_realizados.empty:
        for _, jogo in jogos_realizados.iterrows():
            ta, tb = jogo['time_a'], jogo['time_b']
            ga, gb = int(jogo['gols_a']), int(jogo['gols_b'])
            if ta in tabela:
                tabela[ta]['J'] += 1; tabela[ta]['GP'] += ga; tabela[ta]['GC'] += gb; tabela[ta]['SG'] += (ga - gb)
                if ga > gb: tabela[ta]['Pts'] += 3; tabela[ta]['V'] += 1
                elif ga == gb: tabela[ta]['Pts'] += 1; tabela[ta]['E'] += 1
                else: tabela[ta]['D'] += 1
            if tb in tabela:
                tabela[tb]['J'] += 1; tabela[tb]['GP'] += gb; tabela[tb]['GC'] += ga; tabela[tb]['SG'] += (gb - ga)
                if gb > ga: tabela[tb]['Pts'] += 3; tabela[tb]['V'] += 1
                elif gb == ga: tabela[tb]['Pts'] += 1; tabela[tb]['E'] += 1
                else: tabela[tb]['D'] += 1
    return pd.DataFrame(list(tabela.values()))

# =========================================================
# HEADER PREMIUM
# =========================================================
st.markdown("""
<div style='text-align:center;padding:10px 0;'>
    <h1 style='font-size:46px;margin-bottom:0; letter-spacing: 2px;'>⚽ GAZELAS BET</h1>
    <p style='color:#A0AEC0;font-size:16px;'>Bolão Oficial da Copa do Mundo 2026</p>
</div>
""", unsafe_allow_html=True)

if 'usuario_logado' not in st.session_state: 
    st.session_state.usuario_logado = None

# =========================================================
# INTERFACE DE LOGIN / CADASTRO
# =========================================================
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        aba_login, aba_criar = st.tabs(["🔐 Entrar", "🆕 Criar Conta"])
        
        with aba_login:
            nl = st.text_input("Nome:")
            sl = st.text_input("Senha:", type="password")
            if st.button("Entrar", type="primary"):
                if nl == ADMIN_USER and sl == ADMIN_PASS:
                    st.session_state.usuario_logado = "ADMIN"
                    st.rerun()
                elif verificar_login(nl, sl):
                    st.session_state.usuario_logado = nl
                    st.rerun()
                else: st.error("Nome ou senha incorretos!")
                
        with aba_criar:
            st.info("Escolha um nome fácil para os seus amigos identificarem.")
            nn = st.text_input("Novo Nome:")
            sn = st.text_input("Nova Senha:", type="password")
            if st.button("Cadastrar"):
                if nn.upper() == ADMIN_USER.upper(): st.error("🚨 Nome reservado pelo sistema!")
                elif nn and sn:
                    if criar_usuario(nn, sn): st.success("Conta criada! Vá em 'Entrar'.")
                    else: st.error("🚨 Nome já existe ou erro no banco!")
                else: st.warning("Preencha tudo!")
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# SISTEMA LOGADO
# =========================================================
else:
    user = st.session_state.usuario_logado
    jogos = get_jogos()
    ranking = calcular_ranking()
    
    col_n, col_s = st.columns([5, 1])
    with col_n: 
        if user == "ADMIN": st.error("Logado como **ADMINISTRADOR MESTRE**.")
        else: st.write(f"👋 Bem-vindo, **{user}**!")
    with col_s: 
        if st.button("Sair"):
            st.session_state.usuario_logado = None
            st.rerun()

    total_jogos = len(jogos)
    total_users = len(ranking)
    lider = ranking.iloc[0]['Participante'] if not ranking.empty else "-"
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("👥 Jogadores", total_users)
    with c2: st.metric("⚽ Jogos Ativos", total_jogos)
    with c3: st.metric("🏆 Líder Atual", lider)

    tab1, tab2, tab3, tab_copa, tab4 = st.tabs(["⚽ Palpites", "🏆 Ranking", "👀 Espiar", "🌍 Copa", "⚙️ Admin"])

    # 1. ABA PALPITES
    with tab1:
        if user == "ADMIN":
            st.warning("⚠️ O Admin Mestre não dá palpites. Use uma conta de jogador comum.")
        else:
            st.subheader("Meus Palpites")
            if not jogos.empty:
                p_u = get_palpites_usuario(user)
                jogos['data_apenas'] = pd.to_datetime(jogos['data_hora'].str.replace('T', ' ')).dt.strftime('%d/%m/%Y')
                dias_unicos = jogos['data_apenas'].unique()
                
                for dia in dias_unicos:
                    with st.expander(f"📅 Jogos do dia {dia}"):
                        jogos_do_dia = jogos[jogos['data_apenas'] == dia]
                        for _, j in jogos_do_dia.iterrows():
                            st.markdown("<div class='card'>", unsafe_allow_html=True)
                            fase_jogo = j.get('fase', 'Fase de Grupos')
                            if not pd.notna(fase_jogo): fase_jogo = 'Fase de Grupos'
                            st.caption(f"🏆 {fase_jogo}")
                            
                            dt_str = j['data_hora'].replace('T', ' ')
                            h_j = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                            
                            fuso_br = pytz.timezone('America/Sao_Paulo')
                            agora_br = datetime.now(fuso_br).replace(tzinfo=None)
                            travado = agora_br >= h_j
                            
                            p_at = p_u[p_u['jogo_id'] == j['id']]
                            ja_palpitou = not p_at.empty # Checa se existe a linha no Supabase
                            
                            v_a = int(p_at.iloc[0]['palpite_a']) if ja_palpitou else 0
                            v_b = int(p_at.iloc[0]['palpite_b']) if ja_palpitou else 0
                            
                            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                            with c1: st.write(f"**{j['time_a']}**")
                            with c5: st.write(f"**{j['time_b']}**")
                            
                            if travado:
                                with c2: st.warning(f"{v_a}" if ja_palpitou else "-", icon="🔒")
                                with c3: st.write("X")
                                with c4: st.warning(f"{v_b}" if ja_palpitou else "-", icon="🔒")
                                if not ja_palpitou:
                                    st.error("❌ Você não deixou palpite para este jogo antes do início.")
                                else:
                                    st.caption(f"Jogo iniciado ({h_j.strftime('%H:%M')}).")
                            else:
                                with c2: pa_a = st.number_input(f"A_{j['id']}", min_value=0, value=v_a, label_visibility="collapsed")
                                with c3: st.write("X")
                                with c4: pa_b = st.number_input(f"B_{j['id']}", min_value=0, value=v_b, label_visibility="collapsed")
                                
                                # AVISO INTELIGENTE DE UX
                                if not ja_palpitou:
                                    st.warning("⚠️ Você ainda não palpitou neste jogo! Configure seu placar acima e clique em salvar.")
                                
                                if st.button(f"Salvar {j['time_a']} x {j['time_b']}", key=f"btn_{j['id']}"):
                                    salvar_palpite(user, int(j['id']), pa_a, pa_b)
                                    st.toast("Palpite salvo com sucesso!", icon="⚽")
                                    st.rerun()
                                st.caption(f"Fecha às: {h_j.strftime('%H:%M')}")
                            st.markdown("</div>", unsafe_allow_html=True)
            else: st.info("Aguardando o Admin cadastrar os jogos.")

    # 2. ABA RANKING CARDS + TEXTO COPIÁVEL
    with tab2:
        st.subheader("🏆 Ranking Geral do Grupo")
        if not ranking.empty:
            for i, r in ranking.iterrows():
                pos = i + 1
                classe = "rank-card"
                emoji = "🏅"
                if pos == 1:
                    classe += " gold"
                    emoji = "🥇"
                elif pos == 2: emoji = "🥈"
                elif pos == 3: emoji = "🥉"
                
                st.markdown(f"""
                <div class="{classe}">
                    <h4 style='margin:0;'>{emoji} #{pos} — {r['Participante']}</h4>
                    <p style='margin:5px 0 0 0; color:#00E676; font-weight:bold;'>{r['Pontos']} pontos</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.write("📋 **Mural para o WhatsApp:** Clique no ícone de cópia da caixinha cinza abaixo!")
            
            texto_copia = "🏆 GAZELAS BET - CLASSIFICAÇÃO ATUALIZADA 🏆\n\n"
            for i, r in ranking.iterrows():
                pos = i + 1
                emoji_c = "🥇" if pos==1 else "🥈" if pos==2 else "🥉" if pos==3 else "▪️"
                texto_copia += f"{emoji_c} {pos}º {r['Participante']} — {r['Pontos']} pts\n"
            
            st.code(texto_copia, language="text")
        else: st.info("Nenhum usuário pontuou ainda.")

    # 3. ABA ESPIAR (SANFONA + AVISOS SE NÃO PALPITOU)
    with tab3:
        st.subheader("👀 Espiar Palpites")
        if not jogos.empty:
            jogos['data_apenas'] = pd.to_datetime(jogos['data_hora'].str.replace('T', ' ')).dt.strftime('%d/%m/%Y')
            dias_unicos = jogos['data_apenas'].unique()
            fuso_br = pytz.timezone('America/Sao_Paulo')
            agora_br = datetime.now(fuso_br).replace(tzinfo=None)

            # Lista mestre de participantes cadastrados para cruzar dados
            todos_users_nomes = ranking['Participante'].tolist() if not ranking.empty else []

            for dia in dias_unicos:
                with st.expander(f"📅 Jogos do dia {dia}"):
                    jogos_do_dia = jogos[jogos['data_apenas'] == dia]
                    for _, j_i in jogos_do_dia.iterrows():
                        st.markdown(f"**{j_i['time_a']} x {j_i['time_b']}**")
                        dt_str = j_i['data_hora'].replace('T', ' ')
                        h_j = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                        
                        if agora_br >= h_j:
                            if st.button(f"Ver palpites: {j_i['time_a']} x {j_i['time_b']}", key=f"espiar_{j_i['id']}"):
                                df_palpites_jogo = get_todos_palpites_do_jogo(j_i['id'])
                                
                                ra, rb = j_i['gols_a'], j_i['gols_b']
                                placar_a = int(ra) if pd.notnull(ra) else '?'
                                placar_b = int(rb) if pd.notnull(rb) else '?'
                                st.info(f"Placar Real: {j_i['time_a']} {placar_a} x {placar_b} {j_i['time_b']}")
                                
                                users_que_palpitaram = []
                                
                                # Mostra quem de fato palpitou
                                if not df_palpites_jogo.empty:
                                    for _, row in df_palpites_jogo.iterrows():
                                        participante = row['Participante']
                                        users_que_palpitaram.append(participante)
                                        
                                        pa, pb = int(row['Gols A']), int(row['Gols B'])
                                        txt = f"**{participante}** apostou: **{pa} x {pb}**"
                                        
                                        if pd.notnull(ra) and pd.notnull(rb):
                                            ra_i, rb_i = int(ra), int(rb)
                                            if pa == ra_i and pb == rb_i: st.success(f"🎯 {txt}")
                                            elif (pa > pb and ra_i > rb_i) or (pa < pb and ra_i < rb_i) or (pa == pb and ra_i == rb_i): st.info(f"👍 {txt}")
                                            else: st.error(f"❌ {txt}")
                                        else: st.write(f"⏳ {txt}")
                                
                                # Cruza os dados e aponta quem ESQUECEU de palpitar
                                for usr in todos_users_nomes:
                                    if usr not in users_que_palpitaram and usr != "Admin":
                                        st.write(f"⚪ **{usr}** não palpitou neste jogo.")
                                        
                        else: st.warning("⚠️ Palpites ocultos até o início do jogo.", icon="🔒")
                        st.markdown("---")
        else: st.info("Nenhum jogo cadastrado.")

    # 4. ABA COPA MUNDIAL
    with tab_copa:
        st.subheader("🌍 Tabela Oficial da Copa")
        df_copa = calcular_tabela_copa()
        if not df_copa.empty:
            grupos_ordenados = sorted(df_copa['Grupo'].unique())
            for grupo in grupos_ordenados:
                st.markdown(f"### {grupo}")
                df_grupo = df_copa[df_copa['Grupo'] == grupo].sort_values(by=['Pts', 'SG', 'GP'], ascending=[False, False, False]).drop(columns=['Grupo']).reset_index(drop=True)
                df_grupo.index = df_grupo.index + 1
                st.dataframe(df_grupo, use_container_width=True)

    # 5. ABA ADMIN
    with tab4:
        if user == "ADMIN":
            st.subheader("🔑 Painel do Mestre")
            with st.expander("👥 Lista de Usuários e Senhas"):
                st.dataframe(get_todos_usuarios(), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.write("**Preencha os placares oficiais:**")
            if not jogos.empty:
                for _, jo in jogos.iterrows():
                    c_a, c_b, c_c, c_d = st.columns([2,1,1,2])
                    fase_lbl = jo.get('fase', 'Fase de Grupos')
                    if not pd.notna(fase_lbl): fase_lbl = 'Fase de Grupos'
                    with c_a: st.write(f"[{fase_lbl}] {jo['time_a']} x {jo['time_b']}")
                    
                    ga = int(jo['gols_a']) if pd.notnull(jo['gols_a']) else 0
                    gb = int(jo['gols_b']) if pd.notnull(jo['gols_b']) else 0
                    with c_b: n_ga = st.number_input("G_A", value=ga, key=f"ad_a_{jo['id']}", label_visibility="collapsed")
                    with c_c: n_gb = st.number_input("G_B", value=gb, key=f"ad_b_{jo['id']}", label_visibility="collapsed")
                    with c_d: 
                        if st.button("Salvar Resultado", key=f"ad_btn_{jo['id']}"):
                            atualizar_resultado_real(int(jo['id']), n_ga, n_gb)
                            st.cache_data.clear() 
                            st.success("Resultado Salvo!")
                            st.rerun()
                        
            st.markdown("---")
            st.subheader("➕ Adicionar Jogo (Mata-mata)")
            c_t1, c_t2, c_fase, c_dt, c_bt = st.columns([2, 2, 2, 2, 1])
            with c_t1: novo_t_a = st.text_input("Time A (Ex: 🇧🇷 Brasil)")
            with c_t2: novo_t_b = st.text_input("Time B (Ex: 🇫🇷 França)")
            with c_fase: 
                opcoes_fase = ["Fase de Grupos", "16 avos", "Oitavas", "Quartas", "Semifinal", "3º Lugar", "Final"]
                nova_fase = st.selectbox("Fase do Torneio", opcoes_fase, index=2)
            with c_dt: novo_data = st.text_input("Data", value="2026-06-28 16:00:00")
            with c_bt: 
                st.write(""); st.write("")
                if st.button("Criar", type="primary"):
                    if novo_t_a and novo_t_b and novo_data:
                        adicionar_novo_jogo(novo_t_a, novo_t_b, novo_data, nova_fase)
                        st.cache_data.clear() 
                        st.success("Adicionado!")
                        st.rerun()
                    else: st.warning("Preencha todos os campos!")

            st.markdown("---")
            st.error("🚨 ÁREA DE PERIGO: RESET DO BOLÃO")
            confirmar_reset = st.checkbox("Eu tenho certeza absoluta que quero APAGAR todos os dados para o lançamento oficial.")
            if confirmar_reset and st.button("LIMPAR TUDO AGORA", type="primary"):
                reset_banco_dados()
                st.cache_data.clear()
                st.success("Banco de dados limpo!")
                st.balloons()
        else: st.error("Acesso restrito ao Administrator.")
