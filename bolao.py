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
# FUNÇÕES DE BANCO DE DADOS (ARQUITETURA MULTI-LIGA)
# =========================================================

@st.cache_data(ttl=600)
def get_jogos():
    res = supabase.table("jogos").select("*").order("data_hora").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['data_apenas'] = pd.to_datetime(df['data_hora'].str.replace('T', ' ')).dt.strftime('%d/%m/%Y')
    return df

def get_todas_ligas():
    res = supabase.table("ligas").select("*").order("nome").execute()
    return pd.DataFrame(res.data)

def verificar_liga_existente(codigo_liga):
    res = supabase.table("ligas").select("*").eq("codigo", codigo_liga.strip().upper()).execute()
    return len(res.data) > 0

def criar_nova_liga(nome_liga, codigo_liga, usuario_criador):
    cod = codigo_liga.strip().upper()
    supabase.table("ligas").insert({"nome": nome_liga.strip(), "codigo": cod}).execute()
    # Quem cria a liga já entra nela automaticamente
    ingressar_na_liga(usuario_criador, cod)
    return True

def criar_usuario(nome, senha):
    try:
        supabase.table("usuarios").insert({"nome": nome.strip(), "senha": senha}).execute()
        return True
    except:
        return False

def verificar_login(nome, senha):
    res = supabase.table("usuarios").select("*").eq("nome", nome.strip()).eq("senha", senha).execute()
    return len(res.data) > 0

def get_ligas_do_usuario(usuario):
    res = supabase.table("membros_liga").select("liga_codigo").eq("usuario_nome", usuario).execute()
    if not res.data:
        return []
    return [item['liga_codigo'] for item in res.data]

def ingressar_na_liga(usuario, codigo_liga):
    cod = codigo_liga.strip().upper()
    try:
        # Verifica se já é membro para não duplicar por erro de clique duplo
        existe = supabase.table("membros_liga").select("*").eq("usuario_nome", usuario).eq("liga_codigo", cod).execute()
        if len(existe.data) > 0:
            return True
        
        supabase.table("membros_liga").insert({"usuario_nome": usuario, "liga_codigo": cod}).execute()
        return True
    except Exception as e:
        st.error(f"Erro técnico ao ingressar no banco: {e}")
        return False

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
    membros_res = supabase.table("membros_liga").select("usuario_nome").eq("liga_codigo", cod).execute()
    jogos_res = supabase.table("jogos").select("*").not_.is_("gols_a", "null").execute()
    palpites_res = supabase.table("palpites").select("*").eq("liga_codigo", cod).execute()
    
    pontos = {m['usuario_nome']: 0 for m in membros_res.data}
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

def count_membros_liga(codigo_liga):
    res = supabase.table("membros_liga").select("id").eq("liga_codigo", codigo_liga).execute()
    return len(res.data)

def get_todos_usuarios_global():
    res = supabase.table("usuarios").select("nome, senha").order("nome").execute()
    return pd.DataFrame(res.data)

# --- GERENCIAMENTO ADMIN ---
def deletar_usuario(nome_usuario):
    supabase.table("palpites").delete().eq("usuario", nome_usuario).execute()
    supabase.table("membros_liga").delete().eq("usuario_nome", nome_usuario).execute()
    supabase.table("usuarios").delete().eq("nome", nome_usuario).execute()

def deletar_liga(cod_liga):
    supabase.table("palpites").delete().eq("liga_codigo", cod_liga).execute()
    supabase.table("membros_liga").delete().eq("liga_codigo", cod_liga).execute()
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
        supabase.table("membros_liga").delete().neq("liga_codigo", "").execute()
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
# HEADER E SESSÕES
# =========================================================
st.markdown("<div style='text-align:center;'><h1>⚽ GAZELAS BET</h1></div>", unsafe_allow_html=True)

if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'liga_ativa' not in st.session_state: st.session_state.liga_ativa = None

# =========================================================
# FLUXO 1: DESLOGADO (LOGIN / CADASTRO CLEAN)
# =========================================================
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        aba_login, aba_criar_conta = st.tabs(["🔐 Entrar", "🆕 Criar Conta"])
        
        with aba_login:
            nl = st.text_input("Usuário:", key="login_user")
            sl = st.text_input("Senha:", type="password", key="login_pass")
            if st.button("Entrar no Sistema", type="primary"):
                if nl == ADMIN_USER and sl == ADMIN_PASS:
                    st.session_state.usuario_logado = "ADMIN"
                    st.rerun()
                elif verificar_login(nl, sl):
                    st.session_state.usuario_logado = nl
                    st.rerun()
                else: 
                    st.error("❌ Usuário ou senha incorretos!")
                    
        with aba_criar_conta:
            st.info("Crie seu acesso. Você escolherá suas ligas na próxima tela!")
            nn = st.text_input("Escolha um Nome de Usuário:", key="create_user")
            sn = st.text_input("Escolha uma Senha:", type="password", key="create_pass")
            if st.button("Cadastrar Nova Conta"):
                if nn and sn:
                    if criar_usuario(nn, sn): 
                        st.success("🎉 Conta criada! Vá para a aba '🔐 Entrar'.")
                    else: 
                        st.error("🚨 Nome de usuário já ocupado.")
                else: 
                    st.warning("Preencha todos os campos!")
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# FLUXO 2: LOGADO COMO ADMIN MESTRE GLOBAL
# =========================================================
elif st.session_state.usuario_logado == "ADMIN":
    st.error("🤖 MESTRE GLOBAL — PAINEL DE CONTROLE SUPREMO")
    if st.button("Sair do Modo Admin"):
        st.session_state.usuario_logado = None
        st.rerun()
        
    jogos = get_jogos()
    
    # Gerenciador de Contas
    with st.expander("👥 Gerenciar Contas de Jogadores"):
        df_usuarios = get_todos_usuarios_global()
        if not df_usuarios.empty:
            for _, row_u in df_usuarios.iterrows():
                c_u1, c_u2, c_u3 = st.columns([3, 3, 1])
                c_u1.write(f"👤 {row_u['nome']}")
                c_u2.write(f"🔑 Senha: `{row_u['senha']}`")
                if c_u3.button("Excluir", key=f"del_user_{row_u['nome']}"):
                    deletar_usuario(row_u['nome'])
                    st.rerun()
                    
    # Gerenciador de Ligas
    with st.expander("🏆 Gerenciar Ligas Ativas"):
        df_ligas = get_todas_ligas()
        if not df_ligas.empty:
            for _, row_l in df_ligas.iterrows():
                c_l1, c_l2, c_l3 = st.columns([3, 3, 1])
                c_l1.write(f"🔹 {row_l['nome']}")
                c_l2.write(f"Código: `{row_l['codigo']}`")
                if c_l3.button("Apagar", key=f"del_liga_{row_l['codigo']}"):
                    deletar_liga(row_l['codigo'])
                    st.rerun()

    # Gerenciador de Resultados
    st.write("📊 **Resultados dos Jogos:**")
    if not jogos.empty:
        for _, jo in jogos.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2,1,1,2,1])
            c1.write(f"{jo['time_a']} x {jo['time_b']}")
            ga = int(jo['gols_a']) if pd.notnull(jo['gols_a']) else 0
            gb = int(jo['gols_b']) if pd.notnull(jo['gols_b']) else 0
            na = c2.number_input("A", value=ga, key=f"ad_a_{jo['id']}", label_visibility="collapsed")
            nb = c3.number_input("B", value=gb, key=f"ad_b_{jo['id']}", label_visibility="collapsed")
            if c4.button("Salvar Placar", key=f"ad_btn_{jo['id']}"):
                atualizar_resultado_real(int(jo['id']), na, nb)
                st.cache_data.clear()
                st.rerun()
            if c5.button("❌", key=f"del_jogo_{jo['id']}"):
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
        
    if st.checkbox("RESET TOTAL (ÁREA DE PERIGO)"):
        if st.button("LIMPAR BANCO COMPLETO"):
            reset_banco_dados()
            st.cache_data.clear()
            st.rerun()

# =========================================================
# FLUXO 3: LOGADO MAS SEM LIGA SELECIONADA (PAINEL INTERMEDIÁRIO DE SANFONAS)
# =========================================================
elif st.session_state.liga_ativa is None:
    user = st.session_state.usuario_logado
    col_u, col_s = st.columns([5,1])
    col_u.write(f"👋 Olá, **{user}**!")
    if col_s.button("Sair"):
        st.session_state.usuario_logado = None
        st.rerun()
        
    st.subheader("🏆 Minhas Ligas & Grupos")
    st.write("Dispute o primeiro lugar do ranking de pontos com seus amigos.")
    
    # 1. SANFONA: MINHAS LIGAS
    with st.expander("📁 Minhas Ligas)", expanded=True):
        codigos_usuario = get_ligas_do_usuario(user)
        df_todas = get_todas_ligas()
        
        if codigos_usuario and not df_todas.empty:
            df_minhas = df_todas[df_todas['codigo'].isin(codigos_usuario)]
            for _, row_m in df_minhas.iterrows():
                st.markdown(f"<div style='padding:10px; background:#1E2640; border-radius:10px; margin-bottom:8px;'><b>🛡️ {row_m['nome']}</b> (Código: {row_m['codigo']})</div>", unsafe_allow_html=True)
                if st.button(f"Acessar Sala do Bolão: {row_m['nome']}", key=f"entrar_sala_{row_m['codigo']}"):
                    st.session_state.liga_ativa = row_m['codigo']
                    st.rerun()
        else:
            st.info("Você ainda não entrou em nenhuma liga clássica. Entre ou crie uma abaixo!")

    # 2. SANFONA: LIGAS EXISTENTES (SISTEMA INTELIGENTE DE INGRESSO)
    with st.expander("🔍 Ligas Existentes no Banco (Descobrir e Entrar)"):
        df_todas = get_todas_ligas()
        codigos_usuario = get_ligas_do_usuario(user)
        
        if not df_todas.empty:
            for _, row_e in df_todas.iterrows():
                # Se o cara já tá na liga, avisa. Se não tá, abre o input
                if row_e['codigo'] in codigos_usuario:
                    st.write(f"🟢 **{row_e['nome']}** — Você já participa deste grupo!")
                else:
                    st.write(f"🔹 **{row_e['nome']}** — {count_membros_liga(row_e['codigo'])} participantes")
                    c_txt, c_btn = st.columns([3, 1])
                    pass_liga = c_txt.text_input("Senha/Código de Acesso:", key=f"input_pass_{row_e['codigo']}", placeholder="Digite o código da liga...", label_visibility="collapsed")
                    
                    if c_btn.button("Ingressar", key=f"btn_ingres_{row_e['codigo']}"):
                        if not pass_liga:
                            st.warning("Digite o código para entrar!")
                        elif pass_liga.strip().upper() == row_e['codigo']:
                            if ingressar_na_liga(user, row_e['codigo']):
                                st.success(f"🎉 Vinculado à liga '{row_e['nome']}' com sucesso!")
                                # Força o Streamlit a recarregar o script limpando a memória da árvore
                                st.rerun()
                        else:
                            st.error("❌ Código de acesso incorreto!")
                st.markdown("<hr style='margin:10px 0; border-color:rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        else:
            st.info("Nenhuma liga foi criada globalmente ainda.")

    # 3. SANFONA: CRIAR LIGA
    with st.expander("➕ Criar Nova Liga Clássica"):
        n_liga = st.text_input("Nome da Liga (Ex: Cartoleiros da FATEC):")
        c_liga = st.text_input("Código Customizado da Liga (Ex: COPA99):")
        if st.button("Registrar Liga Clássica"):
            if n_liga and c_liga:
                if verificar_liga_existente(c_liga):
                    st.error("🚨 Esse código já existe! Escolha outro código de acesso.")
                else:
                    criar_nova_liga(n_liga, c_liga, user)
                    st.success(f"Liga '{n_liga}' criada! Divulgue o código '{c_liga.upper()}' pros guris.")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos para fundar a liga.")

# =========================================================
# FLUXO 4: DENTRO DE UMA LIGA ATIVA (AMBIENTE FILTRADO)
# =========================================================
else:
    user = st.session_state.usuario_logado
    liga = st.session_state.liga_ativa
    jogos = get_jogos()
    ranking = calcular_ranking(liga)
    
    # Cabeçalho de retorno estilizado
    if st.button("🔙 Voltar para a Lista de Minhas Ligas"):
        st.session_state.liga_ativa = None
        st.rerun()
        
    st.write(f"👤 Jogador: **{user}** | 🛡️ Liga Ativa: **{liga}**")
    
    # Painel de métricas compactas da liga
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Jogadores no Grupo", len(ranking))
    c2.metric("⚽ Jogos Ativos", len(jogos))
    c3.metric("🏆 Líder da Liga", ranking.iloc[0]['Participante'] if not ranking.empty else "-")

    tab1, tab2, tab3, tab_copa, tab_regras = st.tabs(["⚽ Palpites", "🏆 Ranking", "👀 Espiar", "🌍 Copa", "📜 Regras"])

  # 1. PALPITES (ISOLADOS POR LIGA)
    with tab1:
        if not jogos.empty:
            p_u = get_palpites_usuario(user, liga)
            
            # Captura o horário atual de Brasília para fazer a triagem
            fuso_br = pytz.timezone('America/Sao_Paulo')
            agora_br = datetime.now(fuso_br).replace(tzinfo=None)
            
            # Criar uma coluna temporária no DataFrame para verificar se o jogo já começou/passou
            jogos['datetime_objeto'] = pd.to_datetime(jogos['data_hora'].str.replace('T', ' '))
            jogos['ja_comecou'] = agora_br >= jogos['datetime_objeto']
            
            # Separar os jogos em duas listas de dias
            dias_futuros = jogos[jogos['ja_comecou'] == False]['data_apenas'].unique()
            dias_passados = jogos[jogos['ja_comecou'] == True]['data_apenas'].unique()
            
            # -------------------------------------------------------
            # SEÇÃO 1: PRÓXIMOS JOGOS (NO TOPO)
            # -------------------------------------------------------
            st.markdown("### 🔥 Próximos Jogos")
            jogos_futuros_existentes = False
            
            for dia in dias_futuros:
                # Filtrar apenas os jogos daquele dia que ainda NÃO começaram
                jogos_do_dia = jogos[(jogos['data_apenas'] == dia) & (jogos['ja_comecou'] == False)]
                if not jogos_do_dia.empty:
                    jogos_futuros_existentes = True
                    with st.expander(f"📅 Jogos de {dia} — Abertos", expanded=True):
                        for _, j in jogos_do_dia.iterrows():
                            st.markdown("<div class='card'>", unsafe_allow_html=True)
                            st.caption(f"🏆 {j.get('fase', 'Fase de Grupos')}")
                            
                            p_at = p_u[p_u['jogo_id'] == j['id']]
                            ja_palpitou = not p_at.empty
                            v_a = int(p_at.iloc[0]['palpite_a']) if ja_palpitou else 0
                            v_b = int(p_at.iloc[0]['palpite_b']) if ja_palpitou else 0
                            
                            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                            with c1: st.write(f"**{j['time_a']}**")
                            with c5: st.write(f"**{j['time_b']}**")
                            
                            with c2: pa_a = st.number_input(f"A_{j['id']}", min_value=0, value=v_a, label_visibility="collapsed")
                            with c3: st.write("X")
                            with c4: pa_b = st.number_input(f"B_{j['id']}", min_value=0, value=v_b, label_visibility="collapsed")
                            
                            if not ja_palpitou: 
                                st.warning("⚠️ Você ainda não palpitou neste jogo!")
                                
                            if st.button(f"Salvar {j['time_a']} x {j['time_b']}", key=f"btn_{j['id']}"):
                                salvar_palpite(user, int(j['id']), pa_a, pa_b, liga)
                                st.toast("Palpite Salvo!")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                            
            if not jogos_futuros_existentes:
                st.info("Não há novos jogos agendados para os próximos dias.")
                
            st.markdown("<br><hr style='border-color:rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
            
            # -------------------------------------------------------
            # SEÇÃO 2: JOGOS ANTERIORES / ENCERRADOS (EMBAIXO)
            # -------------------------------------------------------
            st.markdown("### 🔒 Jogos Anteriores / Encerrados")
            
            # Se existirem dias passados, agrupa todos dentro de um expander mestre para não poluir a tela
            if len(dias_passados) > 0:
                with st.expander("📁 Visualizar histórico de jogos encerrados nesta liga"):
                    # Inverter a ordem dos dias passados para que o dia mais recente fique no topo do histórico
                    for dia in reversed(dias_passados):
                        jogos_do_dia_passado = jogos[(jogos['data_apenas'] == dia) & (jogos['ja_comecou'] == True)]
                        if not jogos_do_dia_passado.empty:
                            st.markdown(f"<div style='color:#A0AEC0; font-weight:bold; padding: 5px 0;'>📅 Rodada de {dia}</div>", unsafe_allow_html=True)
                            
                            for _, j in jogos_do_dia_passado.iterrows():
                                st.markdown("<div class='card' style='opacity: 0.75;'>", unsafe_allow_html=True)
                                st.caption(f"🔒 {j.get('fase', 'Fase de Grupos')} — Encerrado")
                                
                                p_at = p_u[p_u['jogo_id'] == j['id']]
                                ja_palpitou = not p_at.empty
                                v_a = int(p_at.iloc[0]['palpite_a']) if ja_palpitou else "-"
                                v_b = int(p_at.iloc[0]['palpite_b']) if ja_palpitou else "-"
                                
                                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                                with c1: st.write(f"{j['time_a']}")
                                with c5: st.write(f"{j['time_b']}")
                                
                                # Mostra o placar travado com ícone de cadeado de forma limpa
                                with c2: st.markdown(f"<div style='text-align:center; background:#1A202C; border-radius:5px; padding:3px;'><b>{v_a}</b></div>", unsafe_allow_html=True)
                                with c3: st.write("X")
                                with c4: st.markdown(f"<div style='text-align:center; background:#1A202C; border-radius:5px; padding:3px;'><b>{v_b}</b></div>", unsafe_allow_html=True)
                                
                                # Mostra o placar real do jogo do lado se o admin já tiver inserido
                                if pd.notnull(j['gols_a']) and pd.notnull(j['gols_b']):
                                    st.markdown(f"<div style='text-align:center; font-size:12px; color:#00E676;'>Placar oficial: {int(j['gols_a'])} x {int(j['gols_b'])}</div>", unsafe_allow_html=True)
                                elif not ja_palpitou:
                                    st.markdown("<div style='text-align:center; font-size:12px; color:#EF4444;'>❌ Você perdeu o prazo deste jogo.</div>", unsafe_allow_html=True)
                                    
                                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum jogo foi encerrado até o momento.")

    # 2. RANKING COMPACTO DA LIGA
    with tab2:
        st.subheader("🏆 Classificação da Liga Clássica")
        if not ranking.empty:
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
                texto_copia += f"{i+1}º {r['Participante']} — {r['Pontos']} pts\n"
            st.code(texto_copia, language="text")
        else:
            st.info("Ninguém pontuou nessa liga ainda.")

    # 3. ESPIAR (SÓ COMPANHEIROS DA MESMA LIGA)
    with tab3:
        st.subheader("👀 Espiar Adversários")
        if not jogos.empty:
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
                                st.info(f"Placar Real: {int(ra) if pd.notnull(ra) else '?'} x {int(rb) if pd.notnull(rb) else '?'}")
                                users_p = df_p['Participante'].tolist()
                                for _, row in df_p.iterrows():
                                    pa, pb = int(row['Gols A']), int(row['Gols B']); txt = f"**{row['Participante']}**: {pa} x {pb}"
                                    if pd.notnull(ra):
                                        if pa==int(ra) and pb==int(rb): st.success(f"🎯 {txt}")
                                        elif (pa>pb and int(ra)>int(rb)) or (pa<pb and int(ra)<int(rb)) or (pa==pb and int(ra)==int(rb)): st.info(f"👍 {txt}")
                                        else: st.error(f"❌ {txt}")
                                    else: st.write(f"⏳ {txt}")
                                for usr in ranking['Participante'].tolist():
                                    if usr not in users_p: st.write(f"⚪ **{usr}** não palpitou.")
                        else: st.warning("🔒 Oculto até o início do jogo.")
                        st.markdown("---")

    # 4. TABELA COPA MUNDIAL
    with tab_copa:
        df_copa = calcular_tabela_copa()
        if not df_copa.empty:
            for grupo in sorted(df_copa['Grupo'].unique()):
                st.markdown(f"### {grupo}")
                st.dataframe(df_copa[df_copa['Grupo']==grupo].sort_values(by=['Pts','SG','GP'], ascending=False).drop(columns=['Grupo']), use_container_width=True, hide_index=True)

    # 5. REGRAS
    with tab_regras:
        st.subheader("📜 Regulamento do Bolão")
        st.markdown("""
        <div class='card'><h4 style='color:#00E676 !important;'>🎯 Pontuação</h4>
        <ul>
            <li><b>3 Pontos:</b> Placar exato.</li>
            <li><b>1 Ponto:</b> Acertou vencedor ou empate.</li>
            <li><b>0 Pontos:</b> Erro total.</li>
        </ul></div>
        <div class='card'><h4 style='color:#00E676 !important;'>⏱️ Tempo Regulamentar</h4>
        <ul>
            <li><b>90 minutos</b> na fase de grupos.</li>
            <li><b>120 minutos</b> no mata-mata (inclui prorrogação, <b>NÃO</b> conta pênaltis).</li>
        </ul></div>
        <div class='card'><h4 style='color:#00E676 !important;'>🔒 Travamento</h4>
        <p>O bloqueio ocorre de forma automática no minuto inicial do jogo.</p></div>
        """, unsafe_allow_html=True)

# RODAPÉ FIXO DE CRÉDITOS
st.markdown("<div class='footer'>CRIADO POR LUCAS ALBERTIN • GAZELAS BET 2026</div>", unsafe_allow_html=True)
