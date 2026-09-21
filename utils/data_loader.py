"""
utils/data_loader.py

Funções responsáveis por buscar dados abertos do StatsBomb (via statsbombpy)
e devolvê-los já tratados em DataFrames do pandas. Todas as funções pesadas
usam st.cache_data para evitar requisições repetidas à API pública do StatsBomb.
"""

import pandas as pd
import streamlit as st
from statsbombpy import sb


# ---------------------------------------------------------------------------
# Competições, temporadas e partidas
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_competitions() -> pd.DataFrame:
    """Carrega a lista de competições/temporadas disponíveis nos dados abertos."""
    comps = sb.competitions()
    return comps.sort_values(["competition_name", "season_name"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    """Carrega todas as partidas de uma competição/temporada específica."""
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    if matches.empty:
        return matches
    matches["match_label"] = (
        matches["match_date"].astype(str)
        + " — "
        + matches["home_team"]
        + " "
        + matches["home_score"].astype(str)
        + " x "
        + matches["away_score"].astype(str)
        + " "
        + matches["away_team"]
    )
    return matches.sort_values("match_date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_events(match_id: int) -> pd.DataFrame:
    """Carrega todos os eventos (passes, chutes, desarmes, etc.) de uma partida."""
    events = sb.events(match_id=match_id)
    return events


@st.cache_data(show_spinner=False)
def load_lineups(match_id: int) -> dict:
    """Carrega as escalações (titulares/reservas) das duas equipes da partida."""
    return sb.lineups(match_id=match_id)


# ---------------------------------------------------------------------------
# Funções auxiliares de filtro / extração
# ---------------------------------------------------------------------------

def get_teams(events: pd.DataFrame) -> list:
    """Retorna os nomes dos dois times presentes nos eventos da partida."""
    if events.empty or "team" not in events.columns:
        return []
    return sorted(events["team"].dropna().unique().tolist())


def get_players(events: pd.DataFrame, team: str | None = None) -> list:
    """Retorna a lista de jogadores presentes nos eventos, opcionalmente filtrando por time."""
    if events.empty or "player" not in events.columns:
        return []
    df = events if team is None else events[events["team"] == team]
    return sorted(df["player"].dropna().unique().tolist())


def filter_events(
    events: pd.DataFrame,
    team: str | None = None,
    player: str | None = None,
    event_type: str | None = None,
    minute_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Aplica filtros combinados sobre o DataFrame de eventos de uma partida."""
    df = events.copy()
    if team and team != "Todos":
        df = df[df["team"] == team]
    if player and player != "Todos":
        df = df[df["player"] == player]
    if event_type and event_type != "Todos":
        df = df[df["type"] == event_type]
    if minute_range:
        df = df[(df["minute"] >= minute_range[0]) & (df["minute"] <= minute_range[1])]
    return df


def compute_season_summary(competition_id: int, season_id: int, matches: pd.DataFrame) -> pd.DataFrame:
    """
    Monta uma tabela-resumo por equipe (gols, jogos, chutes agregados a partir dos
    placares) para a aba de análise comparativa da temporada. Usa apenas dados já
    presentes em `matches`, sem precisar baixar eventos de todas as partidas.
    """
    if matches.empty:
        return pd.DataFrame()

    home = matches[["home_team", "home_score", "away_score"]].rename(
        columns={"home_team": "team", "home_score": "goals_for", "away_score": "goals_against"}
    )
    away = matches[["away_team", "away_score", "home_score"]].rename(
        columns={"away_team": "team", "away_score": "goals_for", "home_score": "goals_against"}
    )
    all_games = pd.concat([home, away], ignore_index=True)

    summary = (
        all_games.groupby("team")
        .agg(
            jogos=("goals_for", "count"),
            gols_marcados=("goals_for", "sum"),
            gols_sofridos=("goals_against", "sum"),
        )
        .reset_index()
    )
    summary["saldo_de_gols"] = summary["gols_marcados"] - summary["gols_sofridos"]
    summary["media_gols_por_jogo"] = (summary["gols_marcados"] / summary["jogos"]).round(2)
    return summary.sort_values("gols_marcados", ascending=False).reset_index(drop=True)
