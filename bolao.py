import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client

st.set_page_config(
    page_title="Gazelas Bet 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0B1020, #111827);
    color: white;
}
h1, h2, h3, h4 { color: white !important; }
p, span, label { color: #E2E8F0 !important; }

.stExpander {
    background-color: #151C32 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
    margin-bottom: 12px;
}
.stExpander:focus-within,
.stExpander:focus,
.stExpander:hover,
.stExpander[data-expanded="true"] {
    background-color: #151C32 !important;
    border: 1px solid rgba(0, 230, 118, 0.4) !important;
}
.stExpander p, .stExpander span, .stExpander label, .stExpander svg,
.stExpander:focus-within p, .stExpander:focus-within span, .stExpander:focus-within label,
.stExpander:focus p, .stExpander:focus span, .stExpander:focus label {
    color: #E2E8F0 !important;
    fill: #E2E8F0 !important;
}
.stExpander summary text, .stExpander summary p, .stExpander summary span {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}
.card {
    background: #151C32;
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 15px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
}
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


# =========================================================
# CREDENCIAIS
# =========================================================
def get_secret(chave, padrao):
    try:
        return st.secrets[chave]
    except Exception:
        return padrao

SUPABASE_URL = get_secret("SUPABASE_URL", "https://busfsfrcodfnjgkizfme.supabase.co")
SUPABASE_KEY = get_secret("SUPABASE_KEY", "sb_publishable_tnx9hoG8lqnwvS2Po02GWQ_d9EcB2AL")
ADMIN_USER = get_secret("ADMIN_USER", "Admin")
ADMIN_PASS = get_secret("ADMIN_PASS", "gazelas123")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================
# HELPERS
# =========================================================
def to_int_seguro(valor, padrao=None):
    try:
        if valor is None:
            return padrao
        return int(float(valor))
    except (TypeError, ValueError):
        return padrao


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
        nome_limpo = nome.strip()
        res = supabase.table("usuarios").select("nome").ilike("nome", nome_limpo).execute()
        if len(res.data) > 0:
            return False
        supabase.table("usuarios").insert({"nome": nome_limpo, "senha": senha}).execute()
        st.cache_data.clear()
        return True
    except Exception:
        return False

def atualizar_dados_usuario(nome_atual, novo_nome, nova_senha):
    nome_atual_limpo = nome_atual.strip()
    novo_nome_limpo = novo_nome.strip()
    if nome_atual_limpo.lower() != novo_nome_limpo.lower():
        res = supabase.table("usuarios").select("nome").ilike("nome", novo_nome_limpo).execute()
        if len(res.data) > 0:
            return False, "🚨 Esse novo nome de usuário já está sendo usado!"
    try:
        supabase.table("usuarios").update({"nome": novo_nome_limpo, "senha": nova_senha}).eq("nome", nome_atual_limpo).execute()
        if nome_atual_limpo != novo_nome_limpo:
            supabase.table("membros_liga").update({"usuario_nome": novo_nome_limpo}).eq("usuario_nome", nome_atual_limpo).execute()
            supabase.table("palpites").update({"usuario": novo_nome_limpo}).eq("usuario", nome_atual_limpo).execute()
        st.cache_data.clear()
        return True, "✅ Dados atualizados com sucesso! Faça login novamente para aplicar."
    except Exception as e:
        return False, f"❌ Erro ao atualizar no banco: {e}"

def verificar_login(nome, senha):
    nome_limpo = nome.strip()
    res = supabase.table("usuarios").select("*").ilike("nome", nome_limpo).eq("senha", senha).execute()
    if len(res.data) > 0:
        return res.data[0]['nome']
    return None

@st.cache_data(ttl=15)
def get_ligas_do_usuario(usuario):
    res = supabase.table("membros_liga").select("liga_codigo").eq("usuario_nome", usuario).execute()
    if not res.data: return []
    return [item['liga_codigo'] for item in res.data]

def get_todos_membros_liga_global():
    res = supabase.table("membros_liga").select("usuario_nome, liga_codigo").execute()
    return pd.DataFrame(res.data)

def ingressar_na_liga(usuario, codigo_liga):
    cod = codigo_liga.strip().upper()
    try:
        supabase.table("membros_liga").insert({"usuario_nome": usuario, "liga_codigo": cod}).execute()
        st.cache_data.clear()
        return True
    except Exception:
        return False

def salvar_palpite(usuario, jogo_id, p_a, p_b, codigo_liga):
    cod = codigo_liga.strip().upper()
    data = {
        "usuario": usuario.strip(),
        "jogo_id": int(jogo_id),
        "palpite_a": to_int_seguro(p_a, 0),
        "palpite_b": to_int_seguro(p_b, 0),
        "liga_codigo": cod
    }
    supabase.table("palpites").upsert(data, on_conflict="usuario,jogo_id,liga_codigo").execute()
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

def calcular_ranking(codigo_liga):
    cod = codigo_liga.strip().upper()

    membros_res = supabase.table("membros_liga").select("usuario_nome").eq("liga_codigo", cod).execute()
    jogos_res = supabase.table("jogos").select("*").execute()
    palpites_res = supabase.table("palpites").select("jogo_id, usuario, palpite_a, palpite_b").eq("liga_codigo", cod).limit(10000).execute()
    ajustes_res = supabase.table("ajustes_pontos").select("usuario_nome, pontos_ajuste").eq("liga_codigo", cod).execute()

    membros = [str(m['usuario_nome']).strip() for m in membros_res.data]
    pontos = {m: 0 for m in membros}

    jogos_dict = {}
    for j in jogos_res.data:
        jogos_dict[int(j['id'])] = j

    for a in ajustes_res.data:
        usr = str(a['usuario_nome']).strip()
        nome_oficial = next((m for m in membros if m.upper() == usr.upper()), None)
        if nome_oficial:
            pontos[nome_oficial] += int(a['pontos_ajuste'])

    vistos = set()
    for p in palpites_res.data:
        usr = str(p['usuario']).strip()
        jid = int(p['jogo_id'])
        chave = (usr.upper(), jid)
        if chave in vistos or jid not in jogos_dict:
            continue
        vistos.add(chave)

        nome_oficial = next((m for m in membros if m.upper() == usr.upper()), None)
        if not nome_oficial:
            continue

        j = jogos_dict[jid]
        pa, pb = to_int_seguro(p['palpite_a']), to_int_seguro(p['palpite_b'])
        ra, rb = to_int_seguro(j.get('gols_a')), to_int_seguro(j.get('gols_b'))

        if None in (pa, pb, ra, rb):
            continue

        if pa == ra and pb == rb:
            pontos[nome_oficial] += 3
        elif (pa > pb and ra > rb) or (pa < pb and ra < rb) or (pa == pb and ra == rb):
            pontos[nome_oficial] += 1

    df = pd.DataFrame(list(pontos.items()), columns=['Participante', 'Pontos'])
    df = df.sort_values(by='Pontos', ascending=False).reset_index(drop=True)
    return df


def corrigir_vinculo_membro(usuario_nome, codigo_liga):
    cod = codigo_liga.strip().upper()
    try:
        supabase.table("membros_liga").insert({"usuario_nome": usuario_nome, "liga_codigo": cod}).execute()
        st.cache_data.clear()
        return True
    except Exception:
        return False

@st.cache_data(ttl=60)
def get_todos_usuarios_global():
    res = supabase.table("usuarios").select("nome, senha").order("nome").execute()
    return pd.DataFrame(res.data)

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
    supabase.table("membros_liga").delete().eq("usuario_nome", usuario_nome).eq("liga_codigo", cod_liga).execute()
    supabase.table("palpites").delete().eq("usuario", usuario_nome).eq("liga_codigo", cod_liga).execute()
    st.cache_data.clear()

def deletar_jogo(jogo_id):
    supabase.table("palpites").delete().eq("jogo_id", jogo_id).execute()
    supabase.table("jogos").delete().eq("id", jogo_id).execute()
    st.cache_data.clear()

def atualizar_resultado_real(jogo_id, gols_a, gols_b):
    supabase.table("jogos").update({"gols_a": gols_a, "gols_b": gols_b}).eq("id", jogo_id).execute()
    st.cache_data.clear()

def redefinir_senha_usuario(nome_usuario, nova_senha):
    supabase.table("usuarios").update({"senha": nova_senha}).eq("nome", nome_usuario).execute()
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
            ta, tb = j['time_a'], j['time_b']
            ga = to_int_seguro(j['gols_a'], 0)
            gb = to_int_seguro(j['gols_b'], 0)
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
# GERENCIADOR DE SESSÃO
# =========================================================
st.markdown("<div style='text-align:center;'><h1>⚽ GAZELAS BET</h1></div>", unsafe_allow_html=True)

if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'liga_ativa' not in st.session_state: st.session_state.liga_ativa = None

if st.session_state.usuario_logado is None and "cookie_user" in st.query_params:
    cookie_u = st.query_params["cookie_user"]
    if cookie_u == "ADMIN":
        st.session_state.usuario_logado = "ADMIN"
    else:
        res_c = supabase.table("usuarios").select("nome").ilike("nome", cookie_u.strip()).execute()
        if len(res_c.data) > 0:
            st.session_state.usuario_logado = res_c.data[0]['nome']
        else:
            del st.query_params["cookie_user"]

# =========================================================
# FLUXO 1: DESLOGADO
# =========================================================
if st.session_state.usuario_logado is None:
    st.markdown("""
    <div class='card' style='text-align: center; border-left: 5px solid #00E676;'>
        <h3 style='margin-top:0;'>👋 Bem-vindos ao Gazelas Bet!</h3>
        <p>A Copa do Mundo está chegando e é claro que vai rolar o tradicional bolão.
        Serão mais de 100 jogos para você provar que entende de futebol ou não passa de um corneteiro de sofá.</p>
        <p style='font-weight: bold; color: #00E676 !important;'>O webapp não tem segredo! Veja como participar:</p>
    </div>
    """, unsafe_allow_html=True)

    c_p1, c_p2, c_p3 = st.columns(3)
    c_p1.markdown("<div class='card' style='text-align:center; padding:10px;'>👤<br><b>1. Crie sua conta</b><br><span style='font-size:12px; color:#A0AEC0;'>Escolha usuário e senha</span></div>", unsafe_allow_html=True)
    c_p2.markdown("<div class='card' style='text-align:center; padding:10px;'>🔐<br><b>2. Faça o login</b><br><span style='font-size:12px; color:#A0AEC0;'>Acesse o sistema</span></div>", unsafe_allow_html=True)
    c_p3.markdown("<div class='card' style='text-align:center; padding:10px;'>🛡️<br><b>3. Escolha a liga</b><br><span style='font-size:12px; color:#A0AEC0;'>Insira o código do grupo</span></div>", unsafe_allow_html=True)

    st.markdown("<p style='text-align:center; font-weight:bold; color:#00E676;'>E pronto, você está apto para demonstrar seus dotes futebolísticos! ⚽</p>", unsafe_allow_html=True)

    col_texto, col_login = st.columns([11, 10], gap="large")

    with col_texto:
        st.markdown("### 📌 Guia de Uso")
        with st.expander("⚽ ABA PALPITES"):
            st.write("Os jogos estão separados por dia pra ninguém perder a chance de pontuar. É só entrar e deixar seus placares.")
        with st.expander("🏆 ABA RANKING"):
            st.write("Aqui fica a tabela de pontos corridos do bolão. Após o fim das partidas, a classificação atualizada também será enviada no grupo.")
        with st.expander("👀 ESPIAR"):
            st.write("Depois que o prazo do jogo fechar, você poderá ver os palpites da galera e descobrir quem copiou seu placar.")
        with st.expander("🌍 COPA"):
            st.write("Informações gerais sobre seleções, grupos e andamento do torneio.")
        with st.expander("📖 REGRAS"):
            st.write("Autoexplicativo, né? Dá uma lida para não reclamar de pontuação depois!")

        st.markdown("<p style='font-size:15px; font-weight:bold; color:#FFB300;'>Que vença o melhor e VAMOS RUMO AO HEXA!!! 🇧🇷🏆</p>", unsafe_allow_html=True)

    with col_login:
        st.markdown("### 🔐 Acessar Plataforma")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        aba_login, aba_criar_conta = st.tabs(["🔐 Entrar", "🆕 Criar Conta"])

        with aba_login:
            nl = st.text_input("Usuário:", key="login_user")
            sl = st.text_input("Senha:", type="password", key="login_pass")
            manter_logado = st.checkbox("Manter logado neste dispositivo", value=True)

            if st.button("Entrar no Sistema", type="primary"):
                if nl == ADMIN_USER and sl == ADMIN_PASS:
                    st.session_state.usuario_logado = "ADMIN"
                    if manter_logado:
                        st.query_params["cookie_user"] = "ADMIN"
                    st.rerun()
                else:
                    nome_oficial_banco = verificar_login(nl, sl)
                    if nome_oficial_banco:
                        st.session_state.usuario_logado = nome_oficial_banco
                        if manter_logado:
                            st.query_params["cookie_user"] = nome_oficial_banco
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")

        with aba_criar_conta:
            st.info("Crie seu acesso global. Você escolherá suas ligas na próxima tela!")
            nn = st.text_input("Escolha um Nome de Usuário:", key="create_user")
            sn = st.text_input("Escolha uma Senha:", type="password", key="create_pass")
            if st.button("Cadastrar Nova Conta"):
                if nn and sn:
                    if criar_usuario(nn, sn):
                        st.success("🎉 Conta criada! Vá para a aba '🔐 Entrar'.")
                    else:
                        st.error("🚨 Nome de usuário indisponível ou já ocupado.")
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

    with st.expander("📊 Ranking Direto do Banco (sem cache)", expanded=False):
        st.caption("Mostra o ranking calculado na hora, ignorando qualquer cache.")
        df_ligas_rank = get_todas_ligas()
        if not df_ligas_rank.empty:
            liga_rank = st.selectbox("Escolha a liga:", df_ligas_rank['codigo'].tolist(), key="rank_direto_liga")
            if st.button("Calcular Agora", key="btn_rank_direto"):
                df_direto = calcular_ranking(liga_rank)
                if not df_direto.empty:
                    df_direto.insert(0, 'Pos', range(1, len(df_direto) + 1))
                    st.dataframe(df_direto, use_container_width=True, hide_index=True)
                    texto = f"🏆 GAZELAS BET - LIGA {liga_rank} 🏆\n\n"
                    for _, r in df_direto.iterrows():
                        texto += f"{int(r['Pos'])}º {r['Participante']} — {r['Pontos']} pts\n"
                    st.code(texto, language="text")
                else:
                    st.info("Nenhum dado encontrado.")

    with st.expander("🔁 RECALCULAR PONTOS — Todas as Ligas", expanded=False):
        if st.button("🔁 Recalcular Agora", type="primary", key="btn_recalculo_geral"):
            st.cache_data.clear()
            df_ligas_recalculo = get_todas_ligas()
            if df_ligas_recalculo.empty:
                st.info("Nenhuma liga cadastrada ainda.")
            else:
                total_inconsistencias = 0
                for _, liga_row in df_ligas_recalculo.iterrows():
                    cod_liga_rc = liga_row['codigo']
                    nome_liga_rc = liga_row['nome']
                    ranking_rc = calcular_ranking(cod_liga_rc)
                    st.markdown(f"### 🛡️ {nome_liga_rc} (`{cod_liga_rc}`)")
                    if not ranking_rc.empty:
                        st.dataframe(ranking_rc, use_container_width=True, hide_index=True)
                    else:
                        st.caption("Nenhum membro ou nenhum ponto ainda nesta liga.")
                    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
                st.success("✅ Recálculo concluído.")

    with st.expander("✏️ Ajuste Manual de Pontos"):
        st.caption("Use para corrigir pontos perdidos por bug, cache ou qualquer inconsistência.")
        df_ligas_adj = get_todas_ligas()
        df_membros_adj = get_todos_membros_liga_global()

        if not df_ligas_adj.empty:
            liga_sel = st.selectbox("Liga:", df_ligas_adj['codigo'].tolist(), key="adj_liga")
            membros_sel = []
            if not df_membros_adj.empty:
                membros_sel = df_membros_adj[df_membros_adj['liga_codigo'] == liga_sel]['usuario_nome'].tolist()

            if membros_sel:
                usuario_sel = st.selectbox("Jogador:", sorted(membros_sel), key="adj_usuario")
                pontos_adj = st.number_input("Pontos a adicionar (use negativo para remover):", value=0, step=1, key="adj_pontos")
                motivo_adj = st.text_input("Motivo:", key="adj_motivo")

                ajustes_atuais = supabase.table("ajustes_pontos").select("*").eq("liga_codigo", liga_sel).execute()
                if ajustes_atuais.data:
                    st.markdown("**Ajustes já aplicados nesta liga:**")
                    df_adj = pd.DataFrame(ajustes_atuais.data)
                    st.dataframe(df_adj[['usuario_nome', 'pontos_ajuste', 'motivo', 'created_at']], use_container_width=True, hide_index=True)
                    ids_adj = [str(a['id']) for a in ajustes_atuais.data]
                    if ids_adj:
                        adj_del = st.selectbox("Remover ajuste pelo ID:", ["—"] + ids_adj, key="adj_del")
                        if adj_del != "—" and st.button("Remover este ajuste", key="btn_del_adj"):
                            supabase.table("ajustes_pontos").delete().eq("id", int(adj_del)).execute()
                            st.success("Ajuste removido!")
                            st.rerun()

                if st.button("Aplicar Ajuste", type="primary", key="btn_aplicar_adj"):
                    if pontos_adj != 0:
                        supabase.table("ajustes_pontos").insert({
                            "usuario_nome": usuario_sel,
                            "liga_codigo": liga_sel,
                            "pontos_ajuste": int(pontos_adj),
                            "motivo": motivo_adj.strip() if motivo_adj else "Ajuste manual"
                        }).execute()
                        st.success(f"✅ {pontos_adj:+d} pontos aplicados para {usuario_sel} na liga {liga_sel}!")
                        st.rerun()
                    else:
                        st.warning("O valor de pontos não pode ser zero.")
            else:
                st.info("Nenhum membro nesta liga.")

    with st.expander("👥 Gerenciar Contas de Jogadores"):
        df_usuarios = get_todos_usuarios_global()
        if not df_usuarios.empty:
            for _, row_u in df_usuarios.iterrows():
                c_u1, c_u2, c_u3, c_u4 = st.columns([3, 2, 2, 1])
                c_u1.write(f"👤 {row_u['nome']}")
                c_u2.write("🔑 ••••••••")
                with c_u3.popover("Redefinir senha"):
                    nova_s = st.text_input("Nova senha:", type="password", key=f"reset_pass_{row_u['nome']}")
                    if st.button("Confirmar", key=f"confirma_reset_{row_u['nome']}"):
                        if nova_s:
                            redefinir_senha_usuario(row_u['nome'], nova_s)
                            st.success("Senha atualizada!")
                            st.rerun()
                        else:
                            st.warning("Digite uma senha.")
                if c_u4.button("Excluir", key=f"del_user_{row_u['nome']}"):
                    deletar_usuario(row_u['nome'])
                    st.rerun()
        else:
            st.info("Nenhum usuário cadastrado ainda.")

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
                        st.write(f"👥 **Membros ativos ({len(membros_da_liga)}):**")
                        for membro in membros_da_liga:
                            col_m1, col_m2 = st.columns([5, 2])
                            col_m1.write(f"👉 {membro}")
                            if col_m2.button("Remover da Liga", key=f"kick_{membro}_{cod_l}"):
                                remover_membro_da_liga(membro, cod_l)
                                st.success(f"👤 {membro} foi removido da liga!")
                                st.rerun()
                    else:
                        st.caption("ℹ️ Nenhum participante ingressou nesta liga ainda.")
                st.markdown("<hr style='margin:15px 0; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    st.write("📊 **Resultados dos Jogos:**")
    if not jogos.empty:
        for _, jo in jogos.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2,1,1,2,1])
            c1.write(f"{jo['time_a']} x {jo['time_b']}")
            ga = to_int_seguro(jo['gols_a'], 0)
            gb = to_int_seguro(jo['gols_b'], 0)
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
        if t_a and t_b:
            adicionar_novo_jogo(t_a, t_b, dat, fas)
            st.rerun()
        else:
            st.warning("Preencha os dois times.")

    if st.checkbox("RESET TOTAL (ÁREA DE PERIGO)"):
        st.warning("Essa ação apaga TODOS os usuários, ligas e palpites. Não pode ser desfeita.")
        if st.button("LIMPAR BANCO COMPLETO"):
            reset_banco_dados()
            st.rerun()

# =========================================================
# FLUXO 3: LOGADO - LISTAGEM DE LIGAS
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
    df_membros_cached = get_todos_membros_liga_global()

    with st.expander("📁 Minhas Ligas (Onde estou participando)", expanded=True):
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
            st.info("Você ainda não entrou em nenhuma liga. Entre ou crie uma abaixo!")

    with st.expander("🔍 Ligas Existentes no Banco"):
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
                                st.success(f"🎉 Vinculado à liga '{row_e['nome']}'!")
                                st.rerun()
                        else:
                            st.error("❌ Código de acesso incorreto!")
                st.markdown("<hr style='margin:10px 0; border-color:rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        else:
            st.info("Nenhuma liga foi criada globalmente ainda.")

    with st.expander("➕ Criar Nova Liga Clássica"):
        n_liga = st.text_input("Nome da Liga (Ex: Cartoleiros da FATEC):")
        c_liga = st.text_input("Código Customizado da Liga (Ex: COPA99):")
        if st.button("Registrar Liga Clássica"):
            if n_liga and c_liga:
                if verificar_liga_existente(c_liga):
                    st.error("🚨 Esse código já existe! Escolha outro.")
                else:
                    criar_nova_liga(n_liga, c_liga, user)
                    st.success(f"Liga '{n_liga}' criada!")
                    st.rerun()
            else:
                st.warning("Preencha todos os campos para fundar a liga.")

    with st.expander("⚙️ Configurações da Conta"):
        st.markdown("<p style='font-size:13px; color:#A0AEC0;'>Deseja alterar seus dados de acesso?</p>", unsafe_allow_html=True)
        novo_nome_input = st.text_input("Seu Nome de Usuário:", value=user, key="edit_profile_name")
        nova_senha_input = st.text_input("Nova Senha (deixe em branco para manter):", value="", type="password", key="edit_profile_pass")
        if st.button("Salvar Alterações de Cadastro", type="secondary"):
            if novo_nome_input:
                if nova_senha_input:
                    sucesso, mensagem = atualizar_dados_usuario(user, novo_nome_input, nova_senha_input)
                else:
                    res_u = supabase.table("usuarios").select("senha").eq("nome", user).execute()
                    senha_atual = res_u.data[0]['senha'] if res_u.data else ""
                    sucesso, mensagem = atualizar_dados_usuario(user, novo_nome_input, senha_atual)
                if sucesso:
                    st.success(mensagem)
                    st.session_state.usuario_logado = None
                    if "cookie_user" in st.query_params:
                        del st.query_params["cookie_user"]
                    st.rerun()
                else:
                    st.error(mensagem)
            else:
                st.warning("O nome de usuário não pode ficar vazio!")

# =========================================================
# FLUXO 4: INTERIOR DE UMA LIGA
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

    with tab1:
        if not jogos.empty:
            p_u = get_palpites_usuario(user, liga)
            fuso_br = pytz.timezone('America/Sao_Paulo')
            agora_br = datetime.now(fuso_br).replace(tzinfo=None)
            jogos['ja_comecou'] = agora_br >= jogos['datetime_convertido']
            dias_futuros = jogos[jogos['ja_comecou'] == False]['data_apenas'].unique()
            dias_passados = jogos[jogos['ja_comecou'] == True]['data_apenas'].unique()

            st.markdown("### 🔥 Próximos Jogos")
            jogos_futuros_existentes = False

            for dia in dias_futuros:
                jogos_do_dia = jogos[(jogos['data_apenas'] == dia) & (jogos['ja_comecou'] == False)]
                if not jogos_do_dia.empty:
                    jogos_futuros_existentes = True
                    with st.expander(f"📅 Jogos de {dia} — Abertos", expanded=True):
                        for _, j in jogos_do_dia.iterrows():
                            st.markdown("<div class='card'>", unsafe_allow_html=True)
                            st.markdown(f"""
                            <div style='display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px;'>
                                <span style='color: #00E676;'>🏆 {j.get('fase', 'Fase de Grupos')}</span>
                                <span style='color: #A0AEC0;'>🕒 Início: <b>{j['hora_apenas']}</b> (Horário de Brasília)</span>
                                <span style='color: #FFB300;'>🔒 Fecha às: <b>{j['hora_apenas']}</b></span>
                            </div>
                            """, unsafe_allow_html=True)

                            p_at = p_u[p_u['jogo_id'] == j['id']]
                            ja_palpitou = not p_at.empty
                            v_a = to_int_seguro(p_at.iloc[0]['palpite_a'], 0) if ja_palpitou else 0
                            v_b = to_int_seguro(p_at.iloc[0]['palpite_b'], 0) if ja_palpitou else 0

                            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                            with c1: st.write(f"**{j['time_a']}**")
                            with c5: st.write(f"**{j['time_b']}**")
                            with c2: pa_a = st.number_input(f"A_{j['id']}", min_value=0, value=v_a, label_visibility="collapsed")
                            with c3: st.write("X")
                            with c4: pa_b = st.number_input(f"B_{j['id']}", min_value=0, value=v_b, label_visibility="collapsed")

                            if not ja_palpitou: st.warning("⚠️ Você ainda não palpitou neste jogo!")
                            if st.button(f"Salvar {j['time_a']} x {j['time_b']}", key=f"btn_{j['id']}"):
                                salvar_palpite(user, j['id'], pa_a, pa_b, liga)
                                st.toast("Palpite Salvo!")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

            if not jogos_futuros_existentes:
                st.info("Não há novos jogos agendados abertos para palpites.")

            st.markdown("<br><hr style='border-color:rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)
            st.markdown("### 🔒 Jogos Anteriores / Encerrados")

            if len(dias_passados) > 0:
                with st.expander("📁 Visualizar histórico de jogos encerrados"):
                    for dia in reversed(list(dias_passados)):
                        jogos_do_dia_passado = jogos[(jogos['data_apenas'] == dia) & (jogos['ja_comecou'] == True)]
                        if not jogos_do_dia_passado.empty:
                            st.markdown(f"<div style='color:#A0AEC0; font-weight:bold; padding: 5px 0;'>📅 Rodada de {dia}</div>", unsafe_allow_html=True)
                            for _, j in jogos_do_dia_passado.iterrows():
                                st.markdown("<div class='card' style='opacity: 0.75;'>", unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style='display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px;'>
                                    <span style='color: #94A3B8;'>🔒 {j.get('fase', 'Fase de Grupos')}</span>
                                    <span style='color: #EF4444;'>⏱️ Iniciado às {j['hora_apenas']}</span>
                                </div>
                                """, unsafe_allow_html=True)

                                p_at = p_u[p_u['jogo_id'] == j['id']]
                                ja_palpitou = not p_at.empty
                                v_a = to_int_seguro(p_at.iloc[0]['palpite_a']) if ja_palpitou else "-"
                                v_b = to_int_seguro(p_at.iloc[0]['palpite_b']) if ja_palpitou else "-"

                                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                                with c1: st.write(f"{j['time_a']}")
                                with c5: st.write(f"{j['time_b']}")
                                with c2: st.markdown(f"<div style='text-align:center; background:#1A202C; border-radius:5px; padding:3px;'><b>{v_a}</b></div>", unsafe_allow_html=True)
                                with c3: st.write("X")
                                with c4: st.markdown(f"<div style='text-align:center; background:#1A202C; border-radius:5px; padding:3px;'><b>{v_b}</b></div>", unsafe_allow_html=True)

                                if pd.notnull(j['gols_a']) and pd.notnull(j['gols_b']):
                                    st.markdown(f"<div style='text-align:center; font-size:12px; color:#00E676;'>Placar oficial: {to_int_seguro(j['gols_a'])} x {to_int_seguro(j['gols_b'])}</div>", unsafe_allow_html=True)
                                elif not ja_palpitou:
                                    st.markdown("<div style='text-align:center; font-size:12px; color:#EF4444;'>❌ Você perdeu o prazo deste jogo.</div>", unsafe_allow_html=True)
                                st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("🏆 Classificação da Liga")
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
            st.info("Ainda não há pontos a exibir nesta liga.")

    with tab3:
        st.subheader("👀 Espiar Adversários")
        if not jogos.empty:
            fuso_br = pytz.timezone('America/Sao_Paulo')
            agora_br = datetime.now(fuso_br).replace(tzinfo=None)
            for dia in jogos['data_apenas'].unique():
                with st.expander(f"📅 Jogos do dia {dia}"):
                    for _, j_i in jogos[jogos['data_apenas'] == dia].iterrows():
                        st.markdown(f"**{j_i['time_a']} x {j_i['time_b']}**")
                        h_j = j_i['datetime_convertido']
                        if agora_br >= h_j:
                            if st.button(f"Ver: {j_i['time_a']} x {j_i['time_b']}", key=f"espiar_{j_i['id']}"):
                                df_p = get_todos_palpites_do_jogo(j_i['id'], liga)
                                ra, rb = j_i['gols_a'], j_i['gols_b']
                                ra_int, rb_int = to_int_seguro(ra), to_int_seguro(rb)
                                st.info(f"Placar Real: {ra_int if ra_int is not None else '?'} x {rb_int if rb_int is not None else '?'}")
                                users_p = df_p['Participante'].tolist()
                                for _, row in df_p.iterrows():
                                    pa, pb = to_int_seguro(row['Gols A']), to_int_seguro(row['Gols B'])
                                    txt = f"**{row['Participante']}**: {pa} x {pb}"
                                    if ra_int is not None and rb_int is not None and pa is not None and pb is not None:
                                        if pa == ra_int and pb == rb_int: st.success(f"🎯 {txt}")
                                        elif (pa > pb and ra_int > rb_int) or (pa < pb and ra_int < rb_int) or (pa == pb and ra_int == rb_int): st.info(f"👍 {txt}")
                                        else: st.error(f"❌ {txt}")
                                    else: st.write(f"⏳ {txt}")
                                for usr in ranking['Participante'].tolist():
                                    if usr not in users_p: st.write(f"⚪ **{usr}** não palpitou.")
                        else:
                            st.warning("🔒 Oculto até o início do jogo.")
                        st.markdown("---")

    with tab_copa:
        df_copa = calcular_tabela_copa()
        if not df_copa.empty:
            for grupo in sorted(df_copa['Grupo'].unique()):
                st.markdown(f"### {grupo}")
                st.dataframe(df_copa[df_copa['Grupo']==grupo].sort_values(by=['Pts','SG','GP'], ascending=False).drop(columns=['Grupo']), use_container_width=True, hide_index=True)

    with tab_regras:
        st.subheader("📜 Regulamento do Bolão")
        st.markdown("""
        <div class='card'><h4 style='color:#00E676 !important;'>🎯 Pontuação</h4>
        <ul>
            <li><b>3 Pontos:</b> Placar exato.</li>
            <li><b>1 Ponto:</b> Acertou o vencedor ou o empate.</li>
            <li><b>0 Pontos:</b> Erro total de análise.</li>
        </ul></div>
        <div class='card'><h4 style='color:#00E676 !important;'>⏱️ Tempo Regulamentar</h4>
        <ul>
            <li><b>90 minutos</b> na fase de grupos.</li>
            <li><b>120 minutos</b> no mata-mata (inclui prorrogação, <b>NÃO</b> conta disputa por pênaltis).</li>
        </ul></div>
        """, unsafe_allow_html=True)

# RODAPÉ
APP_VERSION = "v1.6 — correção limite 1000 registros + função única de ranking (2026-06-24)"
st.markdown(f"<div class='footer'>CRIADO POR LUCAS ALBERTIN • GAZELAS BET 2026<br><span style='opacity:0.5;'>{APP_VERSION}</span></div>", unsafe_allow_html=True)
