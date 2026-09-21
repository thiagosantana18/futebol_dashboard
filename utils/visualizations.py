"""
utils/visualizations.py

Funções que constroem os gráficos exibidos no dashboard: mapas de passes e
chutes (mplsoccer), mapa de calor, e gráficos exploratórios com
matplotlib/seaborn.
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from mplsoccer import Pitch, VerticalPitch

sns.set_theme(style="whitegrid")


# ---------------------------------------------------------------------------
# Mapas em campo (mplsoccer)
# ---------------------------------------------------------------------------

def plot_pass_map(events: pd.DataFrame, player: str | None = None):
    """Desenha o mapa de passes (setas) de uma partida, opcionalmente de um único jogador."""
    passes = events[events["type"] == "Pass"].copy()
    if player and player != "Todos":
        passes = passes[passes["player"] == player]

    if passes.empty or "location" not in passes.columns:
        return None

    passes = passes.dropna(subset=["location", "pass_end_location"])
    passes["x"] = passes["location"].apply(lambda loc: loc[0])
    passes["y"] = passes["location"].apply(lambda loc: loc[1])
    passes["end_x"] = passes["pass_end_location"].apply(lambda loc: loc[0])
    passes["end_y"] = passes["pass_end_location"].apply(lambda loc: loc[1])

    completed = passes[passes["pass_outcome"].isna()]
    incomplete = passes[passes["pass_outcome"].notna()]

    pitch = Pitch(pitch_type="statsbomb", pitch_color="#0e1117", line_color="#c7c7c7")
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_facecolor("#0e1117")

    pitch.arrows(
        completed.x, completed.y, completed.end_x, completed.end_y,
        width=2, headwidth=6, headlength=6, color="#00c2a8", ax=ax, label="Certo"
    )
    pitch.arrows(
        incomplete.x, incomplete.y, incomplete.end_x, incomplete.end_y,
        width=2, headwidth=6, headlength=6, color="#e84545", ax=ax, label="Errado"
    )
    ax.legend(facecolor="#0e1117", edgecolor="none", labelcolor="white", loc="upper left", fontsize=9)
    titulo = f"Mapa de passes — {player}" if player and player != "Todos" else "Mapa de passes da partida"
    ax.set_title(titulo, color="white", fontsize=14, pad=12)
    return fig


def plot_shot_map(events: pd.DataFrame, team: str | None = None):
    """Desenha o mapa de chutes (tamanho da bola = xG) de uma partida, opcionalmente por time."""
    shots = events[events["type"] == "Shot"].copy()
    if team and team != "Todos":
        shots = shots[shots["team"] == team]

    if shots.empty or "location" not in shots.columns:
        return None

    shots["x"] = shots["location"].apply(lambda loc: loc[0])
    shots["y"] = shots["location"].apply(lambda loc: loc[1])
    shots["is_goal"] = shots["shot_outcome"] == "Goal"
    if "shot_statsbomb_xg" not in shots.columns:
        shots["shot_statsbomb_xg"] = 0.05

    pitch = VerticalPitch(
        pitch_type="statsbomb", half=True, pitch_color="#0e1117", line_color="#c7c7c7"
    )
    fig, ax = pitch.draw(figsize=(8, 8))
    fig.set_facecolor("#0e1117")

    nao_gol = shots[~shots["is_goal"]]
    gol = shots[shots["is_goal"]]

    pitch.scatter(
        nao_gol.x, nao_gol.y, s=nao_gol.shot_statsbomb_xg * 900 + 60,
        edgecolors="white", c="#e84545", alpha=0.7, ax=ax, label="Sem gol"
    )
    pitch.scatter(
        gol.x, gol.y, s=gol.shot_statsbomb_xg * 900 + 60,
        edgecolors="white", c="#00c2a8", alpha=0.9, ax=ax, label="Gol", marker="*"
    )
    ax.legend(facecolor="#0e1117", edgecolor="none", labelcolor="white", loc="lower left", fontsize=9)
    titulo = f"Mapa de chutes — {team}" if team and team != "Todos" else "Mapa de chutes da partida"
    ax.set_title(titulo, color="white", fontsize=14, pad=12)
    return fig


def plot_heatmap(events: pd.DataFrame, player: str):
    """Mapa de calor de todas as ações de um jogador em campo."""
    df = events[(events["player"] == player) & (events["location"].notna())].copy()
    if df.empty:
        return None

    df["x"] = df["location"].apply(lambda loc: loc[0])
    df["y"] = df["location"].apply(lambda loc: loc[1])

    pitch = Pitch(pitch_type="statsbomb", pitch_color="#0e1117", line_color="#c7c7c7", line_zorder=2)
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_facecolor("#0e1117")
    pitch.kdeplot(
        df.x, df.y, ax=ax, fill=True, levels=100, thresh=0.02,
        cmap="magma", alpha=0.85
    )
    ax.set_title(f"Mapa de calor — {player}", color="white", fontsize=14, pad=12)
    return fig


# ---------------------------------------------------------------------------
# Gráficos exploratórios (matplotlib / seaborn)
# ---------------------------------------------------------------------------

def plot_event_type_distribution(events: pd.DataFrame, team: str | None = None):
    """Gráfico de barras com a contagem dos tipos de evento mais comuns na partida."""
    df = events if not team or team == "Todos" else events[events["team"] == team]
    counts = df["type"].value_counts().head(10)

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=counts.values, y=counts.index, hue=counts.index, palette="viridis", ax=ax, legend=False)
    ax.set_xlabel("Quantidade de eventos")
    ax.set_ylabel("")
    ax.set_title("Tipos de evento mais frequentes")
    fig.tight_layout()
    return fig


def plot_shots_vs_goals(summary: pd.DataFrame):
    """Dispersão gols marcados x saldo de gols por equipe, ao longo da temporada."""
    if summary.empty:
        return None
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(
        data=summary, x="gols_marcados", y="saldo_de_gols",
        size="jogos", hue="media_gols_por_jogo", palette="viridis", ax=ax, sizes=(40, 200)
    )
    for _, row in summary.iterrows():
        ax.text(row["gols_marcados"] + 0.1, row["saldo_de_gols"], row["team"], fontsize=7)
    ax.set_xlabel("Gols marcados na temporada")
    ax.set_ylabel("Saldo de gols")
    ax.set_title("Gols marcados x saldo de gols por equipe")
    fig.tight_layout()
    return fig


def plot_pass_outcome_by_player(events: pd.DataFrame, top_n: int = 10):
    """Barras empilhadas: passes certos x errados pelos jogadores com mais passes."""
    passes = events[events["type"] == "Pass"].copy()
    if passes.empty:
        return None
    passes["resultado"] = passes["pass_outcome"].apply(lambda x: "Errado" if pd.notna(x) else "Certo")
    top_players = passes["player"].value_counts().head(top_n).index
    df = passes[passes["player"].isin(top_players)]
    tabela = df.groupby(["player", "resultado"]).size().unstack(fill_value=0)
    tabela = tabela.loc[top_players]

    fig, ax = plt.subplots(figsize=(8, 5))
    tabela.plot(kind="barh", stacked=True, color=["#00c2a8", "#e84545"], ax=ax)
    ax.set_xlabel("Número de passes")
    ax.set_ylabel("")
    ax.set_title(f"Passes certos x errados (top {top_n} jogadores)")
    ax.legend(title="")
    fig.tight_layout()
    return fig
