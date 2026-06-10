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

# Injeção de CSS Moderno com as Sanfonas e Cores Travadas
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0B1020, #111827);
    color: white;
}
h1, h2, h3, h4 { color: white !important; }
p, span, label { color: #E2E8F0 !important; }

/* ==========================================
   SANFONAS (ABERTAS E FECHADAS)
   ========================================== */
.stExpander {
    background-color: #151C32 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    margin-bottom: 12px;
}

/* Força o fundo a continuar escuro mesmo quando focada, aberta ou clicada */
.stExpander:focus-within, 
.stExpander:focus, 
.stExpander:hover,
.stExpander[data-expanded="true"] {
    background-color: #151C32 !important;
    border: 1px solid rgba(0, 230, 118, 0.4) !important; /* Adiciona uma borda sutil verde neon ao selecionar */
}

/* Garante que o texto de dentro NUNCA fique escuro/invisível */
.stExpander p, 
.stExpander span, 
.stExpander label, 
.stExpander svg,
.stExpander:focus-within p, 
.stExpander:focus-within span, 
.stExpander:focus-within label,
.stExpander:focus p, 
.stExpander:focus span, 
.stExpander:focus label {
    color: #E2E8F0 !important;
    fill: #E2E8F0 !important;
}

/* Força especificamente o título da sanfona a ser sempre branco */
.stExpander summary text,
.stExpander summary p,
.stExpander summary span {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* ==========================================
   RESTANTE DOS COMPONENTES VISUAIS
   ========================================== */
/* Estilo dos Cards de Palpites */
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

# Conexão com Supabase 
SUPABASE_URL = "https://busfsfrcodfnjgkizfme.supabase.co"
SUPABASE_KEY = "sb_publishable_tnx9hoG8lqnwvS2Po02GWQ_d9EcB2AL"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USER = "Admin"
ADMIN_PASS = "gazelas123" 

# =========================================================
# FUNÇÕES DE BANCO DE DADOS
# =========================================================

@st.cache_data(ttl=300)
def get_jogos():
    res = supabase.table("jogos").select("*").order("data_hora").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['datetime_convertido'] = pd.to_datetime(df['data_hora'].str.replace('T', ' '))
        df['data_apenas'] = df['datetime_convertido'].dt.strftime('%d/%m/%Y')
        df['hora_apenas'] = df['datetime_convertido'].dt.strftime('%H:%M')
    return df

@st.cache_data(ttl=30)
def get_todas_ligas():
    res = supabase.table("ligas").select("*").order("nome").execute()
    return pd.DataFrame(res.data)

def verificar_liga_existente(codigo_liga):
    df_ligas = get_todas_ligas()
    if df_ligas.empty: return False
    return codigo_liga.strip().upper() in df_ligas['codigo'].values

def criar_nova_liga(nome_liga, codigo_liga, usuario_criador):
    cod = codigo_liga.strip().upper()
    supabase.table("ligas").insert({"nome": nome_liga.strip(), "codigo": cod}).execute()
    st.cache_data.clear()
    ingressar_na_liga(usuario_criador, cod)
    return True

def criar_usuario(nome, senha):
    try:
        # Força o nome a salvar sem espaços e tudo em minúsculo
        nome_limpo = nome.strip().lower()
        supabase.table("usuarios").insert({"nome": nome_limpo, "senha": senha}).execute()
        st.cache_data.clear()
        return True
    except:
        return False

def verificar_login(nome, senha):
    nome_limpo = nome.strip().lower()
    res = supabase.table("usuarios").select("*").eq("nome", nome_limpo).eq("senha", senha).execute()
    return len(res.data) > 0

@st.cache_data(ttl=15)
def get_ligas_do_usuario(usuario):
    res = supabase.table("membros_liga").select("liga_codigo").eq("usuario_nome", usuario).execute()
    if not res.data: return []
    return [item['liga_codigo'] for item in res.data]

@st.cache_data(ttl=15)
def get_todos_membros_liga_global():
    res = supabase.table("membros_liga").select("usuario_nome, liga_codigo").execute()
    return pd.DataFrame(res.data)

def ingressar_na_liga(usuario, codigo_liga):
    cod = codigo_liga.strip().upper()
    try:
        supabase.table("membros_liga").insert({"usuario_nome": usuario, "liga_codigo": cod}).execute()
        st.cache_data.clear()
        return True
    except:
        return False

def salvar_palpite(usuario, jogo_id, p_a, p_b, codigo_liga):
    cod = codigo_liga.strip().upper()
    nome_limpo = usuario.strip().lower() # Garante que o palpite case com o usuário do banco
    data = {"usuario": nome_limpo, "jogo_id": jogo_id, "palpite_a": p_a, "palpite_b": p_b, "liga_codigo": cod}
    supabase.table("palpites").upsert(data).execute()
    st.cache_data.clear()

@st.cache_data(ttl=10)
def get_palpites_usuario(usuario, codigo_liga):
    cod = codigo_liga.strip().upper()
    res = supabase.table("palpites").select("*").eq("usuario", usuario).eq("liga_codigo", cod).execute()
    if not res.data: 
        return pd.DataFrame(columns=['usuario', 'jogo_id', 'palpite_a', 'palpite_b', 'liga_codigo'])
    return pd.DataFrame(res.data)

@st.cache_data(ttl=30)
def get_todos_palpites_do_jogo(jogo_id, codigo_liga):
    cod = codigo_liga.strip().upper()
    res = supabase.table("palpites").select("usuario, palpite_a, palpite_b").eq("jogo_id", jogo_id).eq("liga_codigo", cod).execute()
    if not res.data: 
        return pd.DataFrame(columns=['Participante', 'Gols A', 'Gols B'])
    df = pd.DataFrame(res.data)
    df.rename(columns={'usuario': 'Participante', 'palpite_a': 'Gols A', 'palpite_b': 'Gols B'}, inplace=True)
    return df

@st.cache_data(ttl=30)
def calcular_ranking(codigo_liga):
    cod = codigo_liga.strip().upper()
    df_membros = get_todos_membros_liga_global()
    membros_filtrados = df_membros[df_membros['liga_codigo'] == cod]['usuario_nome'].tolist() if not df_membros.empty else []
    
    jogos_res = supabase.table("jogos").select("id, gols_a, gols_b").not_.is_("gols_a", "null").execute()
    palpites_res = supabase.table("palpites").select("jogo_id, usuario, palpite_a, palpite_b").eq("liga_codigo", cod).execute()
    
    pontos = {m: 0 for m in membros_filtrados}
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

@st.cache_data(ttl=60)
def get_todos_usuarios_global():
    res = supabase.table("usuarios").select("nome, senha").order("nome").execute()
    return pd.DataFrame(res.data)

# --- GERENCIAMENTO ADMIN ---
def deletar_usuario(nome_usuario):
    supabase.table("palpites").delete().eq("usuario", nome_usuario).execute()
    supabase.table("membros_liga").delete().eq("usuario_nome", nome_usuario).execute()
    supabase.table("usuarios").delete().eq("nome", nome_usuario).execute()
    st.cache_data.clear()

def deletar_liga(cod_liga):
    supabase.table("palpites").delete().eq("liga_codigo", cod_liga).execute()
    supabase.table("membros_liga").delete().eq("liga_codigo", cod_liga).execute()
    supabase.table("ligas").delete().eq("codigo", cod_liga).execute()
    st.cache_data.clear()

def remover_membro_da_liga(usuario_nome, cod_liga):
    # Remove o vínculo do usuário com aquela liga específica
    supabase.table("membros_liga").delete().eq("usuario_nome", usuario_nome).eq("liga_codigo", cod_liga).execute()
    # Também limpa os palpites que ele fez especificamente dentro dessa liga para não poluir o banco
    supabase.table("palpites").delete().eq("usuario", usuario_nome).eq("liga_codigo", cod_liga).execute()
    st.cache_data.clear()

def deletar_jogo(jogo_id):
    supabase.table("palpites").delete().eq("jogo_id", jogo_id).execute()
    supabase.table("jogos").delete().eq("id", jogo_id).execute()
    st.cache_data.clear()

def atualizar_resultado_real(jogo_id, gols_a, gols_b):
    supabase.table("jogos").update({"gols_a": gols_a, "gols_b": gols_b}).eq("id", jogo_id).execute()
    st.cache_data.clear()

def adicionar_novo_jogo(time_a, time_b, data_hora, fase):
    supabase.table("jogos").insert({"time_a": time_a, "time_b": time_b, "data_hora": data_hora, "fase": fase}).execute()
    st.cache_data.clear()

def reset_banco_dados():
    try:
        supabase.table("palpites").delete().neq("usuario", "").execute()
        supabase.table("membros_liga").delete().neq("liga_codigo", "").execute()
        supabase.table("usuarios").delete().neq("nome", "").execute()
        supabase.table("ligas").delete().neq("nome", "").execute()
        supabase.table("jogos").update({"gols_a": None, "gols_b": None}).neq("time_a", "").execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Erro ao resetar banco: {e}")

@st.cache_data(ttl=120)
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
    jogos_df = get_jogos()
    if jogos_df.empty: return pd.DataFrame()
    jogos_realizados = jogos_df[jogos_df['gols_a'].notnull()]
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
# GERENCIADOR DE SESSÃO E COOKIES
# =========================================================
st.markdown("<div style='text-align:center;'><h1>⚽ GAZELAS BET</h1></div>", unsafe_allow_html=True)

if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'liga_ativa' not in st.session_state: st.session_state.liga_ativa = None

# Mecanismo de persistência simples em nível de session local para o Rerun
if st.session_state.usuario_logado is None and "cookie_user" in st.query_params:
    cookie_u = st.query_params["cookie_user"]
    if cookie_u == "ADMIN":
        st.session_state.usuario_logado = "ADMIN"
    else:
        st.session_state.usuario_logado = cookie_u

# =========================================================
# FLUXO 1: DESLOGADO
# =========================================================
if st.session_state.usuario_logado is None:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        aba_login, aba_criar_conta = st.tabs(["🔐 Entrar", "🆕 Criar Conta"])
        
        with aba_login:
            nl = st.text_input("Usuário:", key="login_user")
            sl = st.text_input("Senha:", type="password", key="login_pass")
            manter_logado = st.checkbox("Manter logado neste dispositivo", value=True)
            
            if st.button("Entrar", type="primary"):
                if nl == ADMIN_USER and sl == ADMIN_PASS:
                    st.session_state.usuario_logado = "ADMIN"
                    if manter_logado:
                        st.query_params["cookie_user"] = "ADMIN"
                    st.rerun()
                elif verificar_login(nl, sl):
                    st.session_state.usuario_logado = nl
                    if manter_logado:
                        st.query_params["cookie_user"] = nl
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
# FLUXO 2: ADMIN
# =========================================================
elif st.session_state.usuario_logado == "ADMIN":
    st.error("🤖 MESTRE GLOBAL — PAINEL DE CONTROLE SUPREMO")
    if st.button("Sair do Modo Admin"):
        st.session_state.usuario_logado = None
        if "cookie_user" in st.query_params:
            del st.query_params["cookie_user"]
        st.rerun()
        
    jogos = get_jogos()
    
    # 1. Sanfona de Usuários Globais (Pode deixar como estava)
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
                    
    # =========================================================
    # GERENCIADOR DE LIGAS E USUARIOS
    # =========================================================
    with st.expander("🏆 Gerenciar Ligas Ativas & Membros"):
        df_ligas = get_todas_ligas()
        df_membros_todos = get_todos_membros_liga_global()
        
        if not df_ligas.empty:
            for _, row_l in df_ligas.iterrows():
                cod_l = row_l['codigo']
                
                c_l1, c_l2, c_l3 = st.columns([3, 3, 1])
                c_l1.markdown(f"### 🔹 {row_l['nome']}")
                c_l2.markdown(f"Código: `{cod_l}`")
                if c_l3.button("Apagar Liga", key=f"del_liga_{cod_l}"):
                    deletar_liga(cod_l)
                    st.rerun()
                
                if not df_membros_todos.empty:
                    membros_da_liga = df_membros_todos[df_membros_todos['liga_codigo'] == cod_l]['usuario_nome'].tolist()
                    
                    if membros_da_liga:
                        st.write(f"👥 **Membros activos ({len(membros_da_liga)}):**")
                        for membro in membros_da_liga:
                            col_m1, col_m2 = st.columns([5, 2])
                            col_m1.write(f"👉 {membro}")
                            if col_m2.button("Remover da Liga", key=f"kick_{membro}_{cod_l}"):
                                remover_membro_da_liga(membro, cod_l)
                                st.success(f"👤 {membro} foi removido da liga com sucesso!")
                                st.rerun()
                    else:
                        st.caption("ℹ️ Nenhum participante ingressou nesta liga ainda.")
                
                st.markdown("<hr style='margin:15px 0; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

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
                st.rerun()
            if c5.button("❌", key=f"del_jogo_{jo['id']}"):
                deletar_jogo(jo['id'])
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
        st.rerun()
        
    if st.checkbox("RESET TOTAL (ÁREA DE PERIGO)"):
        if st.button("LIMPAR BANCO COMPLETO"):
            reset_banco_dados()
            st.rerun()

# =========================================================
# FLUXO 3: LOGADO - PAINEL SANFONADO DE LIGAS
# =========================================================
elif st.session_state.liga_ativa is None:
    user = st.session_state.usuario_logado
    col_u, col_s = st.columns([5,1])
    col_u.write(f"👋 Olá, **{user}**!")
    if col_s.button("Sair"):
        st.session_state.usuario_logado = None
        if "cookie_user" in st.query_params:
            del st.query_params["cookie_user"]
        st.rerun()
        
    st.subheader("🏆 Minhas Ligas & Grupos")
    st.write("Dispute o primeiro lugar do ranking de pontos com seus amigos.")
    
    df_membros_cached = get_todos_membros_liga_global()
    
    # 1. SANFONA: MINHAS LIGAS
    with st.expander("📁 Minhas Ligas", expanded=True):
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

    # 2. SANFONA: LIGAS EXISTENTES
    with st.expander("🔍 Ligas Existentes"):
        df_todas = get_todas_ligas()
        codigos_usuario = get_ligas_do_usuario(user)
        
        if not df_todas.empty:
            for _, row_e in df_todas.iterrows():
                if row_e['codigo'] in codigos_usuario:
                    st.write(f"🟢 **{row_e['nome']}** — Você já participa deste grupo!")
                else:
                    count_membros = len(df_membros_cached[df_membros_cached['liga_codigo'] == row_e['codigo']]) if not df_membros_cached.empty else 0
                    st.write(f"🔹 **{row_e['nome']}** — {count_membros} participantes")
                    c_txt, c_btn = st.columns([3, 1])
                    pass_liga = c_txt.text_input("Senha/Código de Acesso:", key=f"input_pass_{row_e['codigo']}", placeholder="Digite o código da liga...", label_visibility="collapsed")
                    
                    if c_btn.button("Ingressar", key=f"btn_ingres_{row_e['codigo']}"):
                        if not pass_liga:
                            st.warning("Digite o código para entrar!")
                        elif pass_liga.strip().upper() == row_e['codigo']:
                            if ingressar_na_liga(user, row_e['codigo']):
                                st.success(f"🎉 Bem vindo à liga '{row_e['nome']}'!")
                                st.rerun()
                        else:
                            st.error("❌ Código de acesso incorreto!")
                st.markdown("<hr style='margin:10px 0; border-color:rgba(75,100,150,0.05);'>", unsafe_allow_html=True)
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
                    st.success(f"Liga '{n_liga}' criada!")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos para fundar a liga.")

# =========================================================
# FLUXO 4: DENTRO DE UMA LIGA ATIVA
# =========================================================
else:
    user = st.session_state.usuario_logado
    liga = st.session_state.liga_ativa
    jogos = get_jogos()
    ranking = calcular_ranking(liga)
    
    if st.button("🔙 Voltar para a Lista de Minhas Ligas"):
        st.session_state.liga_ativa = None
        st.rerun()
        
    st.write(f"👤 Jogador: **{user}** | 🛡️ Liga Ativa: **{liga}**")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Jogadores no Grupo", len(ranking))
    c2.metric("⚽ Jogos Ativos", len(jogos))
    c3.metric("🏆 Líder da Liga", ranking.iloc[0]['Participante'] if not ranking.empty else "-")

    tab1, tab2, tab3, tab_copa, tab_regras = st.tabs(["⚽ Palpites", "🏆 Ranking", "👀 Espiar", "🌍 Copa", "📜 Regras"])

    # 1. PALPITES (Ajuste #2 - EXIBIÇÃO CLARA DE HORÁRIO E HORÁRIO DA TRAVA)
    with tab1:
        if not jogos.empty:
            p_u = get_palpites_usuario(user, liga)
            
            fuso_br = pytz.timezone('America/Sao_Paulo')
            agora_br = datetime.now(fuso_br).replace(tzinfo=None)
            
            jogos['ja_comecou'] = agora_br >= jogos['datetime_convertido']
            
            dias_futuros = jogos[jogos['ja_comecou'] == False]['data_apenas'].unique()
            dias_passados = jogos[jogos['ja_comecou'] == True]['data_apenas'].unique()
            
            # --- JOGOS FUTUROS ---
            st.markdown("### 🔥 Próximos Jogos")
            jogos_futuros_existentes = False
            
            for dia in dias_futuros:
                jogos_do_dia = jogos[(jogos['data_apenas'] == dia) & (jogos['ja_comecou'] == False)]
                if not jogos_do_dia.empty:
                    jogos_futuros_existentes = True
                    with st.expander(f"📅 Jogos de {dia} — Abertos", expanded=True):
                        for _, j in jogos_do_dia.iterrows():
                            st.markdown("<div class='card'>", unsafe_allow_html=True)
                            
                            # Ajuste #2: Linha visual explícita com horário do jogo e o travamento do bolão
                            st.markdown(f"""
                            <div style='display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px;'>
                                <span style='color: #00E676;'>🏆 {j.get('fase', 'Fase de Grupos')}</span>
                                <span style='color: #A0AEC0;'>🕒 Início: <b>{j['hora_apenas']}</b> (Horário de Brasília)</span>
                                <span style='color: #FFB300;'>🔒 Fecha às: <b>{j['hora_apenas']}</b></span>
                            </div>
                            """, unsafe_allow_html=True)
                            
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
                            
                            if not ja_palpitou: st.warning("⚠️ Você ainda não palpitou neste jogo!")
                            if st.button(f"Salvar {j['time_a']} x {j['time_b']}", key=f"btn_{j['id']}"):
                                salvar_palpite(user, int(j['id']), pa_a, pa_b, liga)
                                st.toast("Palpite Salvo!")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                            
            if not jogos_futuros_existentes:
                st.info("Não há novos jogos agendados para os próximos dias.")
                
            st.markdown("<br><hr style='border-color:rgba(75,100,150,0.1);'><br>", unsafe_allow_html=True)
            
            # --- JOGOS ANTERIORES ---
            st.markdown("### 🔒 Jogos Anteriores / Encerrados")
            if len(dias_passados) > 0:
                with st.expander("📁 Visualizar histórico de jogos encerrados"):
                    for dia in reversed(dias_passados):
                        jogos_do_dia_passado = jogos[(jogos['data_apenas'] == dia) & (jogos['ja_comecou'] == True)]
                        if not jogos_do_dia_passado.empty:
                            st.markdown(f"<div style='color:#A0AEC0; font-weight:bold; padding: 5px 0;'>📅 Rodada de {dia}</div>", unsafe_allow_html=True)
                            for _, j in jogos_do_dia_passado.iterrows():
                                st.markdown("<div class='card' style='opacity: 0.75;'>", unsafe_allow_html=True)
                                
                                st.markdown(f"""
                                <div style='display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px;'>
                                    <span style='color: #94A3B8;'>🔒 {j.get('fase', 'Fase de Grupos')}</span>
                                    <span style='color: #EF4444;'>⏱️ Iniciado às {j['hora_apenas']} (Cadeado trancado)</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                p_at = p_u[p_u['jogo_id'] == j['id']]
                                ja_palpitou = not p_at.empty
                                v_a = int(p_at.iloc[0]['palpite_a']) if ja_palpitou else "-"
                                v_b = int(p_at.iloc[0]['palpite_b']) if ja_palpitou else "-"
                                
                                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                                with c1: st.write(f"{j['time_a']}")
                                with c5: st.write(f"{j['time_b']}")
                                
                                with c2: st.markdown(f"<div style='text-align:center; background:#1A202C; border-radius:5px; padding:3px;'><b>{v_a}</b></div>", unsafe_allow_html=True)
                                with c3: st.write("X")
                                with c4: st.markdown(f"<div style='text-align:center; background:#1A202C; border-radius:5px; padding:3px;'><b>{v_b}</b></div>", unsafe_allow_html=True)
                                
                                if pd.notnull(j['gols_a']) and pd.notnull(j['gols_b']):
                                    st.markdown(f"<div style='text-align:center; font-size:12px; color:#00E676;'>Placar oficial: {int(j['gols_a'])} x {int(j['gols_b'])}</div>", unsafe_allow_html=True)
                                elif not ja_palpitou:
                                    st.markdown("<div style='text-align:center; font-size:12px; color:#EF4444;'>❌ Você perdeu o prazo deste jogo.</div>", unsafe_allow_html=True)
                                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Nenhum jogo foi encerrado até o momento.")

    # 2. RANKING
    with tab2:
        st.subheader("🏆 Classification da Liga Clássica")
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

    # 3. ESPIAR
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
        """, unsafe_allow_html=True)

# RODAPÉ FIXO DE CRÉDITOS
st.markdown("<div class='footer'>CRIADO POR LUCAS ALBERTIN • GAZELAS BET 2026</div>", unsafe_allow_html=True)
