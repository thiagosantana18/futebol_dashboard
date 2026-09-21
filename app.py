"""
app.py — Dashboard de Análise de Futebol com dados StatsBomb

Pergunta central do projeto:
    "Quais jogadores mais se destacam ofensivamente em uma partida (passes,
    chutes, gols) e como a eficiência de finalização e a precisão de passe de
    cada equipe se relacionam com o resultado da partida e da temporada?"

"""

import time

import streamlit as st

from utils.data_loader import (
    compute_season_summary,
    filter_events,
    get_players,
    get_teams,
    load_competitions,
    load_events,
    load_lineups,
    load_matches,
)
from utils.metrics import match_metrics, player_metrics
from utils.visualizations import (
    plot_event_type_distribution,
    plot_heatmap,
    plot_pass_map,
    plot_pass_outcome_by_player,
    plot_shot_map,
    plot_shots_vs_goals,
)

st.set_page_config(
    page_title="Dashboard de Futebol — StatsBomb",
    page_icon="⚽",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state — mantém a seleção do usuário entre interações/páginas
# ---------------------------------------------------------------------------
for chave, valor in {
    "competition_id": None,
    "season_id": None,
    "match_id": None,
    "num_eventos": 15,
}.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


# ---------------------------------------------------------------------------
# Sidebar — seleção de competição, temporada e partida
# ---------------------------------------------------------------------------
st.sidebar.title("⚽ Filtros")
st.sidebar.caption("Dados abertos StatsBomb (statsbombpy)")

with st.spinner("Carregando competições disponíveis..."):
    competitions = load_competitions()

nomes_comp = sorted(competitions["competition_name"].unique())
comp_nome = st.sidebar.selectbox("Campeonato", nomes_comp)

temporadas_df = competitions[competitions["competition_name"] == comp_nome]
temporada_nome = st.sidebar.selectbox("Temporada", sorted(temporadas_df["season_name"].unique(), reverse=True))

linha = temporadas_df[temporadas_df["season_name"] == temporada_nome].iloc[0]
st.session_state.competition_id = int(linha["competition_id"])
st.session_state.season_id = int(linha["season_id"])

with st.spinner("Carregando partidas da temporada..."):
    matches = load_matches(st.session_state.competition_id, st.session_state.season_id)

if matches.empty:
    st.sidebar.warning("Nenhuma partida encontrada para essa seleção.")
    st.stop()

match_label = st.sidebar.selectbox("Partida", matches["match_label"])
match_row = matches[matches["match_label"] == match_label].iloc[0]
st.session_state.match_id = int(match_row["match_id"])

st.sidebar.divider()
st.sidebar.markdown(
    "Navegue pelas abas para ver estatísticas gerais, mapas em campo, "
    "comparação de jogadores e a visão da temporada inteira."
)

# ---------------------------------------------------------------------------
# Carregamento dos eventos da partida selecionada (com progresso visível)
# ---------------------------------------------------------------------------
progresso = st.progress(0, text="Carregando eventos da partida...")
progresso.progress(30, text="Buscando eventos...")
events = load_events(st.session_state.match_id)
progresso.progress(70, text="Buscando escalações...")
lineups = load_lineups(st.session_state.match_id)
progresso.progress(100, text="Pronto!")
time.sleep(0.2)
progresso.empty()

times = get_teams(events)

st.title("⚽ Dashboard de Análise de Futebol")
st.caption(
    "Pergunta do projeto: **quais jogadores mais se destacam ofensivamente e como a "
    "eficiência de finalização/passe se relaciona com o resultado da partida?**"
)

tab_geral, tab_mapas, tab_jogador, tab_temporada = st.tabs(
    ["📋 Visão Geral", "🗺️ Mapas em Campo", "🧑‍🤝‍🧑 Comparar Jogadores", "📈 Temporada"]
)

# ---------------------------------------------------------------------------
# ABA 1 — Visão geral da partida
# ---------------------------------------------------------------------------
with tab_geral:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader(match_row["match_label"])
        st.write(
            f"**Campeonato:** {comp_nome}  |  **Temporada:** {temporada_nome}  |  "
            f"**Estádio:** {match_row.get('stadium', 'N/D')}"
        )
    with col_b:
        st.metric("Placar final", f"{match_row['home_score']} x {match_row['away_score']}")

    metrics = match_metrics(events)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de gols", metrics["total_gols"])
    m2.metric("Total de chutes", metrics["total_chutes"])
    m3.metric(
        "Conversão de chutes",
        f"{metrics['taxa_conversao']}%",
        delta=f"{metrics['taxa_conversao'] - 10:.1f} pp vs média 10%",
    )
    m4.metric(
        "Precisão de passe",
        f"{metrics['taxa_passe']}%",
        delta=f"{metrics['taxa_passe'] - 80:.1f} pp vs média 80%",
    )

    st.divider()

    with st.form("form_filtro_eventos"):
        st.write("**Filtrar tabela de eventos**")
        fc1, fc2, fc3, fc4 = st.columns(4)
        time_sel = fc1.selectbox("Equipe", ["Todos"] + times)
        jogadores_disp = get_players(events, None if time_sel == "Todos" else time_sel)
        jogador_sel = fc2.selectbox("Jogador", ["Todos"] + jogadores_disp)
        tipo_sel = fc3.radio("Tipo de evento", ["Todos", "Pass", "Shot", "Duel", "Carry"], horizontal=False)
        minuto_max = int(events["minute"].max()) if "minute" in events.columns and not events.empty else 90
        intervalo = fc4.slider("Intervalo (min)", 0, minuto_max, (0, minuto_max))
        st.session_state.num_eventos = st.number_input(
            "Quantidade de linhas a exibir", min_value=5, max_value=200,
            value=st.session_state.num_eventos, step=5,
        )
        enviado = st.form_submit_button("Aplicar filtros")

    df_filtrado = filter_events(
        events, team=time_sel, player=jogador_sel, event_type=tipo_sel, minute_range=intervalo
    )

    colunas_exibir = [c for c in ["minute", "team", "player", "type", "pass_outcome", "shot_outcome"] if c in df_filtrado.columns]
    st.dataframe(df_filtrado[colunas_exibir].head(st.session_state.num_eventos), width='stretch')

    csv = df_filtrado[colunas_exibir].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar eventos filtrados (CSV)",
        data=csv,
        file_name=f"eventos_partida_{st.session_state.match_id}.csv",
        mime="text/csv",
    )

    st.pyplot(plot_event_type_distribution(events, None if time_sel == "Todos" else time_sel))

# ---------------------------------------------------------------------------
# ABA 2 — Mapas em campo (mplsoccer)
# ---------------------------------------------------------------------------
with tab_mapas:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Mapa de passes")
        jogador_passe = st.selectbox(
            "Jogador (mapa de passes)", ["Todos"] + get_players(events), key="sel_passe"
        )
        fig_passe = plot_pass_map(events, jogador_passe)
        if fig_passe:
            st.pyplot(fig_passe)
        else:
            st.info("Sem dados de passe suficientes para esse filtro.")

    with col2:
        st.subheader("Mapa de chutes")
        time_chute = st.selectbox("Equipe (mapa de chutes)", ["Todos"] + times, key="sel_chute")
        fig_chute = plot_shot_map(events, time_chute)
        if fig_chute:
            st.pyplot(fig_chute)
        else:
            st.info("Sem chutes registrados para esse filtro.")

    st.divider()
    st.subheader("Mapa de calor por jogador")
    jogador_calor = st.selectbox("Escolha um jogador", get_players(events), key="sel_calor")
    if jogador_calor:
        fig_calor = plot_heatmap(events, jogador_calor)
        if fig_calor:
            st.pyplot(fig_calor)

# ---------------------------------------------------------------------------
# ABA 3 — Comparação entre dois jogadores
# ---------------------------------------------------------------------------
with tab_jogador:
    st.subheader("Comparar dois jogadores da partida")
    jogadores_all = get_players(events)
    c1, c2 = st.columns(2)
    jogador_1 = c1.selectbox("Jogador 1", jogadores_all, index=0 if jogadores_all else None)
    jogador_2 = c2.selectbox(
        "Jogador 2", jogadores_all, index=min(1, len(jogadores_all) - 1) if jogadores_all else None
    )

    if jogador_1 and jogador_2:
        m1_stats = player_metrics(events, jogador_1)
        m2_stats = player_metrics(events, jogador_2)

        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(f"**{jogador_1}**")
            st.metric("Gols", m1_stats["gols"])
            st.metric("Chutes", m1_stats["chutes"])
            st.metric("Passes certos", f"{m1_stats['passes_certos']}/{m1_stats['passes']}")
            st.metric("Precisão de passe", f"{m1_stats['taxa_passe']}%")
            st.metric("Duelos disputados", m1_stats["duelos"])
        with cc2:
            st.markdown(f"**{jogador_2}**")
            st.metric("Gols", m2_stats["gols"], delta=m2_stats["gols"] - m1_stats["gols"])
            st.metric("Chutes", m2_stats["chutes"], delta=m2_stats["chutes"] - m1_stats["chutes"])
            st.metric("Passes certos", f"{m2_stats['passes_certos']}/{m2_stats['passes']}")
            st.metric(
                "Precisão de passe", f"{m2_stats['taxa_passe']}%",
                delta=f"{m2_stats['taxa_passe'] - m1_stats['taxa_passe']:.1f} pp",
            )
            st.metric("Duelos disputados", m2_stats["duelos"], delta=m2_stats["duelos"] - m1_stats["duelos"])

    st.divider()
    st.subheader("Ranking de precisão de passe (top 10 jogadores da partida)")
    fig_rank = plot_pass_outcome_by_player(events)
    if fig_rank:
        st.pyplot(fig_rank)

# ---------------------------------------------------------------------------
# ABA 4 — Visão da temporada inteira
# ---------------------------------------------------------------------------
with tab_temporada:
    st.subheader(f"Resumo da temporada — {comp_nome} {temporada_nome}")
    with st.spinner("Calculando resumo da temporada..."):
        resumo = compute_season_summary(
            st.session_state.competition_id, st.session_state.season_id, matches
        )

    if resumo.empty:
        st.info("Não há dados suficientes para montar o resumo da temporada.")
    else:
        with st.container():
            st.dataframe(resumo, width='stretch')
        st.pyplot(plot_shots_vs_goals(resumo))

        csv_temporada = resumo.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar resumo da temporada (CSV)",
            data=csv_temporada,
            file_name=f"resumo_temporada_{st.session_state.season_id}.csv",
            mime="text/csv",
        )
