"""
utils/metrics.py

Funções para calcular indicadores numéricos (métricas) a partir do
DataFrame de eventos de uma partida: gols, chutes, passes, taxa de
conversão, etc.
"""

import pandas as pd


def match_metrics(events: pd.DataFrame) -> dict:
    """Calcula métricas gerais da partida a partir dos eventos brutos."""
    shots = events[events["type"] == "Shot"]
    passes = events[events["type"] == "Pass"]
    goals = shots[shots["shot_outcome"] == "Goal"]

    total_passes = len(passes)
    passes_certos = passes["pass_outcome"].isna().sum()
    taxa_passe = (passes_certos / total_passes * 100) if total_passes else 0.0

    total_chutes = len(shots)
    total_gols = len(goals)
    conversao = (total_gols / total_chutes * 100) if total_chutes else 0.0

    return {
        "total_gols": total_gols,
        "total_chutes": total_chutes,
        "taxa_conversao": round(conversao, 1),
        "total_passes": total_passes,
        "passes_certos": int(passes_certos),
        "taxa_passe": round(taxa_passe, 1),
    }


def player_metrics(events: pd.DataFrame, player: str) -> dict:
    """Calcula métricas individuais de um jogador específico na partida."""
    df = events[events["player"] == player]
    shots = df[df["type"] == "Shot"]
    passes = df[df["type"] == "Pass"]
    goals = shots[shots["shot_outcome"] == "Goal"]
    desarmes = df[df["type"] == "Duel"]

    total_passes = len(passes)
    passes_certos = passes["pass_outcome"].isna().sum()
    taxa_passe = (passes_certos / total_passes * 100) if total_passes else 0.0

    return {
        "gols": len(goals),
        "chutes": len(shots),
        "passes": total_passes,
        "passes_certos": int(passes_certos),
        "taxa_passe": round(taxa_passe, 1),
        "duelos": len(desarmes),
    }
