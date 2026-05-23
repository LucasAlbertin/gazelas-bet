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

# Injeção de CSS Moderno
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0B1020, #111827);
    color: white;
}
h1, h2, h3, h4 { color: white !important; }
p, span, label { color: #E2E8F0 !important; }

/* Estilo dos Cards */
.card {
    background: #151C32;
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 15px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
}

/* Ranking e Tabelas */
.rank-card {
    background: #151C32;
    padding: 18px;
    border-radius: 16px;
    margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}

/* Botões Modernos */
.stButton > button {
    width: 100%;
    border-radius: 14px;
    background: linear-gradient(90deg,#00E676,#00C853);
    color: black !important;
    font-weight: bold;
    padding: 12px;
    transition: 0.3s;
    border: none;
}
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,230,118,0.35); }

/* Dashboard Compacto */
div[data-testid="metric-container"] { background: #151C32; border-radius: 18px; padding: 12px; border: 1px solid rgba(255,255,255,0.05); }
div[data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
div[data-testid="stMetricLabel"] { font-size: 14px !important; color: #A0AEC0 !important; }

/* Rodapé de Créditos */
.footer {
    text-align: center;
    padding: 20px;
    color: #94A3B8;
    font-size: 12px;
    letter-spacing: 1px;
    margin-top: 50px;
    border-top: 1px solid rgba(255,255,255,0.05);
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
# FUNÇÕES DE BANCO DE DADOS
# =========================================================

@st.cache_data(ttl=600)
def get_jogos():
    res = supabase.table("jogos").select("*").order("data_hora").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['data_apenas'] = pd.to_datetime(df['data_hora'].str.replace('T', ' ')).dt.strftime('%d/%m/%Y')
    return df

def verificar_liga_existente(codigo_liga):
    res = supabase.table("ligas").select("*").eq("codigo", codigo_liga.strip().upper()).execute()
    return len(res.data) > 0

def get_todas_ligas():
    res = supabase.table("ligas").select("*").order("nome").execute()
    return pd.DataFrame(res.data)

def criar_nova_liga(nome_liga, codigo_liga):
    cod = codigo_liga.strip().upper()
    res = supabase.table("ligas").insert({"nome": nome_liga.strip(), "codigo": cod}).execute()
    return True

def criar_usuario(nome, senha):
    try:
        supabase.table("usuarios").insert({"nome": nome.strip(), "senha": senha}).execute()
        return True
    except:
        return False

def vincular_usuario_a_liga(nome, codigo_liga):
    try:
        cod = codigo_liga.strip().upper()
        supabase.table("usuarios").update({"liga_codigo": cod}).eq("nome", nome.strip()).execute()
        return True
    except:
        return False

def verificar_login(nome, senha):
    res = supabase.table("usuarios").select("*").eq("nome", nome.strip()).eq("senha", senha).execute()
    return len(res.data) > 0

def salvar_palpite(usuario, jogo_id, p_a, p_b, codigo_liga):
    cod = codigo_liga.strip().upper()
    data = {"usuario": usuario, "jogo_id": jogo_id, "palpite_a": p_a, "palpite_b": p_b, "liga_codigo": cod}
    supabase.table("palpites").upsert(data).execute()

def get_palpites_usuario(usuario, codigo_liga):
    cod = codigo_liga.strip().upper()
    res = supabase.table("palpites").select("*").eq("usuario", usuario).eq("liga_codigo", cod).execute()
    if not res.data: 
        return pd.DataFrame(columns=['usuario', 'jogo_id', 'palpite_a', 'palpite_b', 'liga_codigo'])
    return pd.DataFrame(res.data)

def get_todos_palpites_do_jogo(jogo_id, codigo_liga):
    cod = codigo_liga.strip().upper()
    res = supabase.table("palpites").select("usuario, palpite_a, palpite_b").eq("jogo_id", jogo_id).eq("liga_codigo", cod).execute()
    if not res.data: 
        return pd.DataFrame(columns=['Participante', 'Gols A', 'Gols B'])
    df = pd.DataFrame(res.data)
    df.rename(columns={'usuario': 'Participante', 'palpite_a': 'Gols A', 'palpite_b': 'Gols B'}, inplace=True)
    return df

def calcular_ranking(codigo_liga):
    cod = codigo_liga.strip().upper()
    usuarios_res = supabase.table("usuarios").select("nome").eq("liga_codigo", cod).execute()
    jogos_res = supabase.table("jogos").select("*").not_.is_("gols_a", "null").execute()
    palpites_res = supabase.table("palpites").select("*").eq("liga_codigo", cod).execute()
    
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
            if p['usuario'] in pontos: 
                pontos[p['usuario']] += pts
                
    df = pd.DataFrame(list(pontos.items()), columns=['Participante', 'Pontos']).sort_values(by='Pontos', ascending=False).reset_index(drop=True)
    return df

def get_todos_usuarios_global():
    res = supabase.table("usuarios").select("nome, senha, liga_codigo").order("nome").execute()
    return pd.DataFrame(res.data)

# --- FUNÇÕES EXCLUSIVAS DE GERENCIAMENTO DO ADMIN ---
def deletar_usuario(nome_usuario):
    supabase.table("palpites").delete().eq("usuario", nome_usuario).execute()
    supabase.table("usuarios").delete().eq("nome", nome_usuario).execute()

def deletar_liga(cod_liga):
    supabase.table("palpites").delete().eq("liga_codigo", cod_liga).execute()
    supabase.table("usuarios").update({"liga_codigo": None}).eq("liga_codigo", cod_liga).execute()
    supabase.table("ligas").delete().eq("codigo", cod_liga).execute()

def deletar_jogo(jogo_id):
    supabase.table("palpites").delete().eq("jogo_id", jogo_id).execute()
    supabase.table("jogos").delete().eq("id", jogo_id).execute()

def atualizar_resultado_real(jogo_id, gols_a, gols_b):
    supabase.table("jogos").update({"gols_a": gols_a, "gols_b": gols_b}).eq("id", jogo_id).execute()

def adicionar_novo_jogo(time_a, time_b, data_hora, fase):
    supabase.table("jogos").insert({"time_a": time_a, "time_b": time_b, "data_hora": data_hora, "fase": fase}).execute()

def reset_banco_dados():
    try:
        supabase.table("palpites").delete().neq("usuario", "").execute()
        supabase.table("usuarios").delete().neq("nome", "").execute()
        supabase.table("ligas").delete().neq("nome", "").execute()
        supabase.table("jogos").update({"gols_a": None, "gols_b": None}).neq("time_a", "").execute()
    except Exception as e:
        st.error(f"Erro ao resetar banco: {e}")

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
        for _, j in jogos_realizados.iterrows():
            ta, tb = j['time_a'], j['time_b']; ga, gb = int(j['gols_a']), int(j['gols_b'])
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
# INTERFACE DE LOGIN / CADASTRO
# =========================================================
if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'liga_ativa' not in st.session_state: st.session_state.liga_ativa = None

if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        aba_login, aba_criar_conta, aba_criar_liga = st.tabs(["🔐 Entrar", "🆕 Criar Conta", "🏆 Criar Liga"])
        
        # ABA ENTRAR
        with aba_login:
            nl = st.text_input("Usuário:", key="login_user")
            sl = st.text_input("Senha:", type="password", key="login_pass")
            ll = st.text_input("Código da Liga:", help="Deixe em branco apenas se for o Admin.", key="login_liga")
            if st.button("Entrar no Sistema", type="primary"):
                if nl == ADMIN_USER and sl == ADMIN_PASS:
                    st.session_state.usuario_logado = "ADMIN"
                    st.session_state.liga_ativa = "GLOBAL"
                    st.rerun()
                elif not ll:
                    st.error("🚨 Jogadores comuns precisam informar o Código da Liga para entrar!")
                elif verificar_login(nl, sl):
                    if verificar_liga_existente(ll):
                        vincular_usuario_a_liga(nl, ll)
                        st.session_state.usuario_logado = nl
                        st.session_state.liga_ativa = ll.strip().upper()
                        st.rerun()
                    else:
                        st.error("🚨 Esse código de liga não existe! Verifique com o administrador.")
                else: 
                    st.error("❌ Usuário ou senha incorretos!")
                    
        # ABA CRIAR CONTA
        with aba_criar_conta:
            st.info("Crie seu acesso global. Você escolherá sua liga na hora de entrar!")
            nn = st.text_input("Escolha um Nome de Usuário:", key="create_user")
            sn = st.text_input("Escolha uma Senha:", type="password", key="create_pass")
            if st.button("Cadastrar Nova Conta"):
                if nn and sn:
                    if criar_usuario(nn, sn): 
                        st.success("🎉 Conta criada com sucesso! Vá para a aba '🔐 Entrar'.")
                    else: 
                        st.error("🚨 Este nome de usuário já está sendo utilizado por outra pessoa.")
                else: 
                    st.warning("Preencha todos os campos!")
                    
        # ABA CRIAR LIGA
        with aba_criar_liga:
            st.info("Crie um grupo exclusivo para seus amigos.")
            nome_liga = st.text_input("Nome da Liga (Ex: Amigos da FATEC):")
            cod_liga = st.text_input("Código de Acesso Personalizado (Ex: FATEC2026):")
            if st.button("Registrar Nova Liga"):
                if nome_liga and cod_liga:
                    if verificar_liga_existente(cod_liga):
                        st.error("🚨 Esse código de acesso já está em uso por outro grupo! Escolha outro.")
                    else:
                        try:
                            if criar_nova_liga(nome_liga, cod_liga):
                                st.success(f"Liga '{nome_liga}' criada com sucesso! Compartilhe o código '{cod_liga.upper()}' com seus amigos.")
                        except Exception as error_db:
                            st.error(f"❌ Erro de conexão com o banco: {error_db}")
                else:
                    st.warning("Preencha o nome e o código da liga!")
                    
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# APP LOGADO (ISOLADO POR LIGA)
# =========================================================
else:
    user = st.session_state.usuario_logado
    liga = st.session_state.liga_ativa
    jogos = get_jogos()
    ranking = calcular_ranking(liga) if user != "ADMIN" else pd.DataFrame()
    
    col_n, col_s = st.columns([5, 1])
    with col_n: 
        if user == "ADMIN": st.error("Logado como **ADMINISTRADOR MESTRE GLOBAL**.")
        else: st.write(f"👋 Jogador: **{user}** | 🏆 Liga: **{liga}**")
    with col_s: 
        if st.button("Sair"): 
            st.session_state.usuario_logado = None
            st.session_state.liga_ativa = None
            st.rerun()

    # Painel de métricas compactas
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Jogadores na Liga", len(ranking) if user != "ADMIN" else "Mestre")
    c2.metric("⚽ Total de Jogos", len(jogos))
    c3.metric("🏆 Líder da Liga", ranking.iloc[0]['Participante'] if not ranking.empty else "-")

    tab1, tab2, tab3, tab_copa, tab_regras, tab4 = st.tabs(["⚽ Palpites", "🏆 Ranking", "👀 Espiar", "🌍 Copa", "📜 Regras", "⚙️ Admin"])

    # 1. ABA PALPITES
    with tab1:
        if user == "ADMIN": st.warning("Admin Mestre global não realiza palpites.")
        else:
            st.subheader("Meus Palpites")
            if not jogos.empty:
                p_u = get_palpites_usuario(user, liga)
                for dia in jogos['data_apenas'].unique():
                    with st.expander(f"📅 Jogos do dia {dia}"):
                        for _, j in jogos[jogos['data_apenas'] == dia].iterrows():
                            st.markdown("<div class='card'>", unsafe_allow_html=True)
                            st.caption(f"🏆 {j.get('fase', 'Fase de Grupos')}")
                            dt_str = j['data_hora'].replace('T', ' '); h_j = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                            fuso_br = pytz.timezone('America/Sao_Paulo'); agora_br = datetime.now(fuso_br).replace(tzinfo=None)
                            travado = agora_br >= h_j
                            
                            p_at = p_u[p_u['jogo_id'] == j['id']]; ja_palpitou = not p_at.empty
                            v_a = int(p_at.iloc[0]['palpite_a']) if ja_palpitou else 0; v_b = int(p_at.iloc[0]['palpite_b']) if ja_palpitou else 0
                            
                            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                            with c1: st.write(f"**{j['time_a']}**")
                            with c5: st.write(f"**{j['time_b']}**")
                            
                            if travado:
                                with c2: st.warning(f"{v_a}" if ja_palpitou else "-", icon="🔒")
                                with c3: st.write("X")
                                with c4: st.warning(f"{v_b}" if ja_palpitou else "-", icon="🔒")
                                if not ja_palpitou: st.error("❌ Não palpitou a tempo.")
                            else:
                                with c2: pa_a = st.number_input(f"A_{j['id']}", min_value=0, value=v_a, label_visibility="collapsed")
                                with c3: st.write("X")
                                with c4: pa_b = st.number_input(f"B_{j['id']}", min_value=0, value=v_b, label_visibility="collapsed")
                                if not ja_palpitou: st.warning("⚠️ Você ainda não palpitou neste jogo!")
                                if st.button(f"Salvar {j['time_a']} x {j['time_b']}", key=f"btn_{j['id']}"):
                                    salvar_palpite(user, int(j['id']), pa_a, pa_b, liga)
                                    st.toast("Palpite Salvo!"); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

    # 2. ABA RANKING COMPACTA
    with tab2:
        st.subheader("🏆 Classificação Interna")
        if user == "ADMIN": st.info("O Admin gerencia as ligas e dados de forma global.")
        elif not ranking.empty:
            df_visual = ranking.copy()
            df_visual.insert(0, 'Posição', range(1, len(df_visual) + 1))
            
            def emojificar_posicao(pos):
                if pos == 1: return "🥇 1º"
                elif pos == 2: return "🥈 2º"
                elif pos == 3: return "🥉 3º"
                return f"▪️ {pos}º"
            
            df_visual['Posição'] = df_visual['Posição'].apply(emojificar_posicao)
            
            st.dataframe(
                df_visual,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Posição": st.column_config.TextColumn("Posição", width="small"),
                    "Participante": st.column_config.TextColumn("Participante"),
                    "Pontos": st.column_config.NumberColumn("Pontos Total", format="%d pts")
                }
            )
            
            st.markdown("---")
            texto_copia = f"🏆 GAZELAS BET - LIGA {liga} 🏆\n\n"
            for i, r in ranking.iterrows():
                pos = i + 1
                emoji_c = "🥇" if pos==1 else "🥈" if pos==2 else "🥉" if pos==3 else "▪️"
                texto_copia += f"{emoji_c} {pos}º {r['Participante']} — {r['Pontos']} pts\n"
            st.code(texto_copia, language="text")
        else:
            st.info("Nenhum participante pontuou nesta liga ainda.")

    # 3. ABA ESPIAR
    with tab3:
        if user == "ADMIN": st.warning("Aba restrita a contas de jogadores comuns.")
        elif not jogos.empty:
            fuso_br = pytz.timezone('America/Sao_Paulo'); agora_br = datetime.now(fuso_br).replace(tzinfo=None)
            for dia in jogos['data_apenas'].unique():
                with st.expander(f"📅 Jogos do dia {dia}"):
                    for _, j_i in jogos[jogos['data_apenas'] == dia].iterrows():
                        st.markdown(f"**{j_i['time_a']} x {j_i['time_b']}**")
                        h_j = datetime.strptime(j_i['data_hora'].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                        if agora_br >= h_j:
                            if st.button(f"Ver: {j_i['time_a']} x {j_i['time_b']}", key=f"espiar_{j_i['id']}"):
                                df_p = get_todos_palpites_do_jogo(j_i['id'], liga)
                                ra, rb = j_i['gols_a'], j_i['gols_b']
                                st.info(f"Placar: {int(ra) if pd.notnull(ra) else '?'} x {int(rb) if pd.notnull(rb) else '?'}")
                                users_p = df_p['Participante'].tolist()
                                for _, row in df_p.iterrows():
                                    pa, pb = int(row['Gols A']), int(row['Gols B']); txt = f"**{row['Participante']}**: {pa} x {pb}"
                                    if pd.notnull(ra):
                                        if pa==int(ra) and pb==int(rb): st.success(f"🎯 {txt}")
                                        elif (pa>pb and int(ra)>int(rb)) or (pa<pb and int(ra)<int(rb)) or (pa==pb and int(ra)==int(rb)): st.info(f"👍 {txt}")
                                        else: st.error(f"❌ {txt}")
                                    else: st.write(f"⏳ {txt}")
                                for usr in ranking['Participante'].tolist():
                                    if usr not in users_p and usr != "Admin": st.write(f"⚪ **{usr}** não palpitou.")
                        else: st.warning("🔒 Os palpites do grupo estão ocultos até o início do jogo.")
                        st.markdown("---")

    # 4. ABA COPA
    with tab_copa:
        df_copa = calcular_tabela_copa()
        if not df_copa.empty:
            for grupo in sorted(df_copa['Grupo'].unique()):
                st.markdown(f"### {grupo}")
                st.dataframe(df_copa[df_copa['Grupo']==grupo].sort_values(by=['Pts','SG','GP'], ascending=False).drop(columns=['Grupo']), use_container_width=True, hide_index=True)

    # 5. ABA REGRAS
    with tab_regras:
        st.subheader("📜 Regulamento do Bolão")
        st.markdown("""
        <div class='card'><h4 style='color:#00E676 !important;'>🎯 Pontuação</h4>
        <ul>
            <li><b>3 Pontos:</b> Placar exato.</li>
            <li><b>1 Ponto:</b> Acertou vencedor ou empate.</li>
            <li><b>0 Pontos:</b> Erro total.</li>
        </ul>
        </div>
        <div class='card'><h4 style='color:#00E676 !important;'>⏱️ Tempo de Jogo Regulamentar</h4>
        <p>A pontuação será contabilizada após o término oficial da partida:</p>
        <ul>
            <li><b>90 minutos</b> na fase de grupos.</li>
            <li><b>120 minutos</b> nas fases eliminatórias (inclui a prorrogação, mas <b>NÃO</b> conta a disputa por pênaltis).</li>
        </ul>
        </div>
        <div class='card'><h4 style='color:#00E676 !important;'>🔒 Travamento Automático</h4>
        <p>O cadeado fecha automaticamente no horário de início de cada jogo (Horário de Brasília).</p>
        </div>
        <div class='card'><h4 style='color:#00E676 !important;'>👀 Espiar</h4>
        <p>Os palpites dos adversários da sua liga só ficam visíveis após o início da partida.</p>
        </div>
        """, unsafe_allow_html=True)

    # 6. ABA ADMIN GLOBAL (COMPLETAMENTE EXPANDIDA COM CONTROLE TOTAL)
    with tab4:
        if user == "ADMIN":
            st.subheader("🔑 Painel Mestre Global")
            
            # --- MONITOR DE USUÁRIOS (VER LOGINS, SENHAS E EXCLUIR FAKES) ---
            with st.expander("👥 Gerenciar Contas de Jogadores"):
                df_usuarios = get_todos_usuarios_global()
                if not df_usuarios.empty:
                    st.write("Lista completa de jogadores no sistema:")
                    for _, row_u in df_usuarios.iterrows():
                        col_u1, col_u2, col_u3, col_u4 = st.columns([2, 2, 2, 1])
                        with col_u1: st.write(f"👤 {row_u['nome']}")
                        with col_u2: st.write(f"🔑 Senha: `{row_u['senha']}`")
                        with col_u3: st.write(f"🏆 Liga: `{row_u['liga_codigo']}`")
                        with col_u4:
                            if st.button("Excluir", key=f"del_user_{row_u['nome']}"):
                                deletar_usuario(row_u['nome'])
                                st.success(f"{row_u['nome']} apagado!")
                                st.rerun()
                else:
                    st.info("Nenhum usuário cadastrado.")

            # --- MONITOR DE LIGAS (VER E EXCLUIR GRUPOS INATIVOS) ---
            with st.expander("🏆 Gerenciar Ligas Ativas"):
                df_ligas = get_todas_ligas()
                if not df_ligas.empty:
                    for _, row_l in df_ligas.iterrows():
                        col_l1, col_l2, col_l3 = st.columns([3, 3, 1])
                        with col_l1: st.write(f"🔹 {row_l['nome']}")
                        with col_l2: st.write(f"Código: `{row_l['codigo']}`")
                        with col_l3:
                            if st.button("Apagar", key=f"del_liga_{row_l['codigo']}"):
                                deletar_liga(row_l['codigo'])
                                st.success("Liga excluída!")
                                st.rerun()
                else:
                    st.info("Nenhuma liga criada ainda.")

            st.markdown("---")
            
            # --- MONITOR DE JOGOS (EDITAR PLACAR E EXCLUIR PARTIDA) ---
            st.write("📊 **Gerenciar Resultados dos Jogos:**")
            if not jogos.empty:
                for _, jo in jogos.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([2,1,1,2,1])
                    with c1: st.write(f"{jo['time_a']} x {jo['time_b']}")
                    ga = int(jo['gols_a']) if pd.notnull(jo['gols_a']) else 0
                    gb = int(jo['gols_b']) if pd.notnull(jo['gols_b']) else 0
                    na = c2.number_input("A", value=ga, key=f"ad_a_{jo['id']}", label_visibility="collapsed")
                    nb = c3.number_input("B", value=gb, key=f"ad_b_{jo['id']}", label_visibility="collapsed")
                    
                    with c4:
                        if st.button("Salvar Placar", key=f"ad_btn_{jo['id']}"):
                            atualizar_resultado_real(int(jo['id']), na, nb)
                            st.cache_data.clear()
                            st.success("Salvo!")
                            st.rerun()
                    with c5:
                        if st.button("❌", key=f"del_jogo_{jo['id']}", help="Excluir este jogo permanentemente"):
                            deletar_jogo(jo['id'])
                            st.cache_data.clear()
                            st.rerun()
                            
            st.markdown("---")
            st.subheader("➕ Novo Jogo")
            c1, c2, c3, c4 = st.columns(4)
            t_a = c1.text_input("Time A")
            t_b = c2.text_input("Time B")
            fas = c3.selectbox("Fase", ["Fase de Grupos", "16 avos", "Oitavas", "Quartas", "Semifinal", "Final"])
            dat = c4.text_input("Data", value="2026-06-01 16:00:00")
            if st.button("Criar Jogo"):
                adicionar_novo_jogo(t_a, t_b, dat, fas)
                st.cache_data.clear()
                st.rerun()
                
            st.markdown("---")
            if st.checkbox("RESET TOTAL (ÁREA DE PERIGO)"):
                if st.button("LIMPAR TUDO"): 
                    reset_banco_dados()
                    st.cache_data.clear()
                    st.success("Banco de dados limpo com sucesso!")
                    st.rerun()
        else: 
            st.error("Acesso restrito ao administrador global do bolão.")

# RODAPÉ FIXO DE CRÉDITOS
st.markdown("<div class='footer'>CRIADO POR LUCAS ALBERTIN • GAZELAS BET 2026</div>", unsafe_allow_html=True)
