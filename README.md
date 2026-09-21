# ⚽ Dashboard de Análise de Futebol (Streamlit + StatsBombPy + mplsoccer)

Dashboard interativo para explorar dados abertos de futebol do
[StatsBomb](https://statsbomb.com/), construído com **Streamlit**,
**statsbombpy** e **mplsoccer**.

## Pergunta que o dashboard responde

> **Quais jogadores mais se destacam ofensivamente em uma partida (passes,
> chutes, gols) e como a eficiência de finalização e a precisão de passe de
> cada equipe se relacionam com o resultado da partida e da temporada?**

O usuário escolhe um campeonato, uma temporada e uma partida, e o dashboard
mostra estatísticas gerais, mapas de passes/chutes/calor em campo,
comparação entre dois jogadores e um resumo agregado da temporada inteira.

## Estrutura do projeto

```
futebol_dashboard/
├── app.py                     # aplicação principal (Streamlit)
├── requirements.txt
├── README.md
└── utils/
    ├── data_loader.py         # carregamento de dados (statsbombpy) + cache
    ├── visualizations.py      # mplsoccer / matplotlib / seaborn
    └── metrics.py             # cálculo de métricas de partida e de jogador
```

## Como rodar

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O app abrirá em `http://localhost:8501`. É necessário acesso à internet na
primeira execução, pois os dados são baixados do repositório público de
dados abertos do StatsBomb.

## O que o dashboard oferece

- **Sidebar** com seleção de campeonato, temporada e partida (dados carregados
  via `statsbombpy`, com `st.cache_data` para evitar downloads repetidos).
- **Aba "Visão Geral"**: placar, métricas da partida (`st.metric`), formulário
  de filtro de eventos (equipe, jogador, tipo de evento, intervalo de minutos),
  tabela de eventos e botão de download em CSV.
- **Aba "Mapas em Campo"**: mapa de passes e mapa de chutes (mplsoccer,
  `Pitch`/`VerticalPitch`), além de mapa de calor por jogador.
- **Aba "Comparar Jogadores"**: métricas lado a lado de dois jogadores
  escolhidos pelo usuário, com indicadores de variação (delta), e gráfico de
  passes certos x errados dos jogadores com mais passes na partida.
- **Aba "Temporada"**: tabela-resumo por equipe (gols marcados/sofridos, saldo,
  média por jogo) e gráfico de dispersão gols x saldo de gols, com download
  em CSV.
- **Session State** mantém as seleções de competição/temporada/partida e a
  quantidade de linhas exibida na tabela enquanto o usuário navega entre abas.
- **Cache** (`st.cache_data`) evita reconsultar a API do StatsBomb a cada
  interação, e barras de progresso/spinners indicam o carregamento dos dados.

## Fonte dos dados

Os dados vêm do repositório de dados abertos do StatsBomb
([statsbomb/open-data](https://github.com/statsbomb/open-data)), acessado
através da biblioteca `statsbombpy`. A cobertura de competições/temporadas
varia (inclui, por exemplo, Copas do Mundo, Champions League e ligas
femininas), e o próprio dashboard lista as opções disponíveis no momento da
execução.
