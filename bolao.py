import streamlit as st
import pandas as pd
from datetime import datetime
import pytz 
from supabase import create_client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gazelas Bet 2026", layout="centered")

# Conexão com Supabase (Lendo dos Secrets para sua segurança)
SUPABASE_URL = "https://busfsfrcodfnjgkizfme.supabase.co"
SUPABASE_KEY = "sb_publishable_tnx9hoG8lqnwvS2Po02GWQ_d9EcB2AL"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 🔐 CREDENCIAIS DO ADMIN ---
ADMIN_USER = "Admin"
ADMIN_PASS = "gazelas123" 

# --- FUNÇÕES DE BANCO DE DADOS (SUPABASE) ---

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
        return pd.DataFrame()
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
            pts = 0
            
            # Blindagem: Forçando a conversão para inteiro
            pa, pb = int(p['palpite_a']), int(p['palpite_b'])
            ra, rb = int(j['gols_a']), int(j['gols_b'])
            
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
                tabela[ta]['J'] += 1
                tabela[ta]['GP'] += ga
                tabela[ta]['GC'] += gb
                tabela[ta]['SG'] += (ga - gb)
                if ga > gb:
                    tabela[ta]['Pts'] += 3
                    tabela[ta]['V'] += 1
                elif ga == gb:
                    tabela[ta]['Pts'] += 1
                    tabela[ta]['E'] += 1
                else:
                    tabela[ta]['D'] += 1

            if tb in tabela:
                tabela[tb]['J'] += 1
                tabela[tb]['GP'] += gb
                tabela[tb]['GC'] += ga
                tabela[tb]['SG'] += (gb - ga)
                if gb > ga:
                    tabela[tb]['Pts'] += 3
                    tabela[tb]['V'] += 1
                elif gb == ga:
                    tabela[tb]['Pts'] += 1
                    tabela[tb]['E'] += 1
                else:
                    tabela[tb]['D'] += 1

    return pd.DataFrame(list(tabela.values()))

# --- INTERFACE ---
st.title("⚽🦌 Gazelas Bet")

if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.subheader("🔐 Acesso ao Bolão")
    aba_login, aba_criar = st.tabs(["Entrar", "Criar Conta"])
    
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
        st.info("Escolha um nome que seus amigos reconheçam (Ex: Lucas, Alemão, Fer)")
        nn = st.text_input("Novo Nome:")
        sn = st.text_input("Nova Senha:", type="password")
        if st.button("Cadastrar"):
            if nn.upper() == ADMIN_USER.upper():
                st.error("🚨 Nome reservado pelo sistema! Escolha outro.")
            elif nn and sn:
                if criar_usuario(nn, sn): st.success("Conta criada! Vá em 'Entrar'.")
                else: st.error("🚨 Nome já existe ou ocorreu um erro!")
            else: st.warning("Preencha tudo!")

else:
    user = st.session_state.usuario_logado
    col_n, col_s = st.columns([4, 1])
    
    with col_n: 
        if user == "ADMIN":
            st.error("Você está logado como **ADMINISTRADOR MESTRE**.")
        else:
            st.write(f"Bem-vindo(a), **{user}**!")
            
    with col_s: 
        if st.button("Sair"):
            st.session_state.usuario_logado = None
            st.rerun()

    tab1, tab2, tab3, tab_copa, tab4 = st.tabs(["⚽ Palpites", "🏆 Ranking", "👀 Espiar", "🌍 Copa", "⚙️ Admin"])

    with tab1:
        if user == "ADMIN":
            st.warning("⚠️ O Administrador Mestre não pode dar palpites. Saia desta conta e entre com a sua conta de jogador normal.")
        else:
            st.subheader("Meus Palpites")
            jogos = get_jogos()
            if not jogos.empty:
                p_u = get_palpites_usuario(user)
                
                jogos['data_apenas'] = pd.to_datetime(jogos['data_hora'].str.replace('T', ' ')).dt.strftime('%d/%m/%Y')
                dias_unicos = jogos['data_apenas'].unique()
                
                for dia in dias_unicos:
                    with st.expander(f"📅 Jogos do dia {dia}"):
                        jogos_do_dia = jogos[jogos['data_apenas'] == dia]
                        
                        for _, j in jogos_do_dia.iterrows():
                            st.markdown("---")
                            # Mostrando a fase do torneio acima do jogo
                            fase_jogo = j.get('fase', 'Fase de Grupos')
                            if not pd.notna(fase_jogo): fase_jogo = 'Fase de Grupos'
                            st.caption(f"🏆 {fase_jogo}")
                            
                            dt_str = j['data_hora'].replace('T', ' ')
                            h_j = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                            
                            # --- A MÁGICA DO FUSO HORÁRIO BRASILEIRO AQUI ---
                            fuso_br = pytz.timezone('America/Sao_Paulo')
                            agora_br = datetime.now(fuso_br).replace(tzinfo=None)
                            travado = agora_br >= h_j
                            # --------------------------------------------------
                            
                            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                            with c1: st.write(f"**{j['time_a']}**")
                            with c5: st.write(f"**{j['time_b']}**")
                            
                            p_at = p_u[p_u['jogo_id'] == j['id']]
                            v_a = int(p_at.iloc[0]['palpite_a']) if not p_at.empty else 0
                            v_b = int(p_at.iloc[0]['palpite_b']) if not p_at.empty else 0
                            
                            if travado:
                                with c2: st.warning(f"{v_a}", icon="🔒")
                                with c3: st.write("X")
                                with c4: st.warning(f"{v_b}", icon="🔒")
                                st.caption(f"Jogo iniciado ({h_j.strftime('%H:%M')}).")
                            else:
                                with c2: pa_a = st.number_input(f"A_{j['id']}", min_value=0, value=v_a, label_visibility="collapsed")
                                with c3: st.write("X")
                                with c4: pa_b = st.number_input(f"B_{j['id']}", min_value=0, value=v_b, label_visibility="collapsed")
                                if st.button(f"Salvar {j['time_a']} x {j['time_b']}", key=f"btn_{j['id']}"):
                                    salvar_palpite(user, int(j['id']), pa_a, pa_b)
                                    st.success("Salvo!")
                                    st.rerun() # Atualiza a tela imediatamente
                                st.caption(f"Fecha às: {h_j.strftime('%H:%M')}")
            else:
                st.info("Aguardando o Admin cadastrar os jogos da Copa.")

    with tab2:
        st.markdown("### *Gazelas Bet*⚽🦌")
        df_rank = calcular_ranking()
        if not df_rank.empty:
            txt = "_Classificação_ 🏆\n\n"
            for i, r in df_rank.iterrows():
                p = i + 1
                emoji = "🥇" if p==1 else "🥈" if p==2 else "🥉" if p==3 else "▪️" if p<=10 else "🔻"
                txt += f"{emoji}{p}. {r['Participante']} - {r['Pontos']} pts\n"
            st.markdown(txt)
            st.code(txt, language="text")
        else:
            st.info("Nenhum usuário no ranking ainda.")

  with tab3:
        st.subheader("👀 Espiar Palpites")
        js = get_jogos()
        if not js.empty:
            ops = {}
            for _, j in js.iterrows():
                dt_str = j['data_hora'].replace('T', ' ')
                dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                fase_lbl = j.get('fase', 'Fase de Grupos')
                if not pd.notna(fase_lbl): fase_lbl = 'Fase de Grupos'
                ops[j['id']] = f"[{fase_lbl}] {j['time_a']} x {j['time_b']} ({dt_obj.strftime('%d/%m %H:%M')})"
                
            sel = st.selectbox("Escolha o jogo:", options=list(ops.keys()), format_func=lambda x: ops[x])
            if sel:
                j_i = js[js['id'] == sel].iloc[0]
                dt_str = j_i['data_hora'].replace('T', ' ')
                
                # --- A MÁGICA DO FUSO HORÁRIO BRASILEIRO AQUI ---
                fuso_br = pytz.timezone('America/Sao_Paulo')
                agora_br = datetime.now(fuso_br).replace(tzinfo=None)
                
                if agora_br >= datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S'):
                # ------------------------------------------------
                    df_palpites_jogo = get_todos_palpites_do_jogo(sel)
                    
                    if not df_palpites_jogo.empty:
                        ra = j_i['gols_a']
                        rb = j_i['gols_b']
                        
                        placar_a = int(ra) if pd.notnull(ra) else '?'
                        placar_b = int(rb) if pd.notnull(rb) else '?'
                        st.markdown(f"### {j_i['time_a']}  **{placar_a} x {placar_b}** {j_i['time_b']}")
                        st.caption("Legenda: 🟩 Placar Exato (+3) | 🟦 Vencedor/Empate (+1) | 🟥 Errou (0)")
                        st.markdown("---")
                        
                        for _, row in df_palpites_jogo.iterrows():
                            participante = row['Participante']
                            pa = int(row['Gols A'])
                            pb = int(row['Gols B'])
                            txt = f"**{participante}** apostou: **{pa} x {pb}**"
                            
                            if pd.notnull(ra) and pd.notnull(rb):
                                ra_int, rb_int = int(ra), int(rb)
                                if pa == ra_int and pb == rb_int:
                                    st.success(f"🎯 {txt}") 
                                elif (pa > pb and ra_int > rb_int) or (pa < pb and ra_int < rb_int) or (pa == pb and ra_int == rb_int):
                                    st.info(f"👍 {txt}") 
                                else:
                                    st.error(f"❌ {txt}") 
                            else:
                                st.write(f"⏳ {txt}")
                    else:
                        st.info("Ninguém deu palpite para este jogo ainda.")
                else: 
                    st.warning("⚠️ Shhhh! Os palpites estão ocultos para ninguém copiar! Volte na hora do jogo.")
        else:
            st.info("Nenhum jogo cadastrado.")

    with tab_copa:
        st.subheader("🌍 Tabela Oficial da Copa")
        st.write("Classificação baseada nos resultados reais informados no Admin!")
        df_copa = calcular_tabela_copa()
        if not df_copa.empty:
            grupos_ordenados = sorted(df_copa['Grupo'].unique())
            for grupo in grupos_ordenados:
                st.markdown(f"### {grupo}")
                df_grupo = df_copa[df_copa['Grupo'] == grupo].sort_values(
                    by=['Pts', 'SG', 'GP'], ascending=[False, False, False]
                )
                df_grupo = df_grupo.drop(columns=['Grupo']).reset_index(drop=True)
                df_grupo.index = df_grupo.index + 1
                st.dataframe(df_grupo, use_container_width=True)

    with tab4:
        if user == "ADMIN":
            st.subheader("🔑 Painel do Mestre")
            
            with st.expander("👥 Lista de Usuários e Senhas (Sigiloso)"):
                st.dataframe(get_todos_usuarios(), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.write("**Preencha os placares oficiais:**")
            jogos_adm = get_jogos()
            if not jogos_adm.empty:
                for _, jo in jogos_adm.iterrows():
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
                            st.success("Atualizado!")
                            st.rerun() # Atualiza a tela imediatamente para refletir no Ranking
                        
            st.markdown("---")
            st.subheader("➕ Adicionar Jogo (Mata-mata)")
            c_t1, c_t2, c_fase, c_dt, c_bt = st.columns([2, 2, 2, 2, 1])
            with c_t1: novo_t_a = st.text_input("Time A (Ex: 🇧🇷 Brasil)")
            with c_t2: novo_t_b = st.text_input("Time B (Ex: 🇫🇷 França)")
            with c_fase: 
                opcoes_fase = ["Fase de Grupos", "16 avos", "Oitavas", "Quartas", "Semifinal", "3º Lugar", "Final"]
                nova_fase = st.selectbox("Fase do Torneio", opcoes_fase, index=2) # Padrão: Oitavas
            with c_dt: novo_data = st.text_input("Data", value="2026-06-28 16:00:00")
            with c_bt: 
                st.write(""); st.write("")
                if st.button("Criar", type="primary"):
                    if novo_t_a and novo_t_b and novo_data:
                        adicionar_novo_jogo(novo_t_a, novo_t_b, novo_data, nova_fase)
                        st.success("Adicionado!")
                        st.rerun() # Atualiza a tela na hora
                    else:
                        st.warning("Preencha todos os campos!")

            st.markdown("---")
            st.error("🚨 ÁREA DE PERIGO: RESET DO BOLÃO")
            confirmar_reset = st.checkbox("Eu tenho certeza absoluta que quero APAGAR todos os usuários e palpites para o lançamento oficial.")
            
            if confirmar_reset:
                if st.button("LIMPAR TUDO AGORA", type="primary"):
                    reset_banco_dados()
                    st.success("Banco de dados limpo! O sistema está pronto para o lançamento oficial.")
                    st.balloons()
        else:
            st.error("Acesso restrito ao Administrador da Banca.")
