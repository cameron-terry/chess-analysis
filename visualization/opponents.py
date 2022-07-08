import sqlite3 as sq3

import pandas.io.sql
import plotly.graph_objects as go
import pandas as pd
import numpy as np

conn = sq3.connect('../datasets/chess_games.db')
cur = conn.cursor()

countries_list = sorted(list(set(pd.read_sql_query("SELECT country FROM players", conn).values[:,0])))
country_codes = pd.read_csv('../datasets/scraping/ISO_3166-1_alpha-3_codes.csv')

op_df = pd.DataFrame()
op_df["country"] = countries_list
op_df["code"] = "None"
op_df["wins"] = 0
op_df["losses"] = 0
op_df["draws"] = 0
op_df["score"] = 0

for idx, country in enumerate(countries_list):
    try:
        # spain
        if country in ['Basque Country', 'Catalonia']:
            continue

        # united kingdom
        if country in ['England', 'Scotland', 'Wales']:
            continue

        # can't assign a country
        if country in ['International', 'Unknown']:
            continue

        # replace country with 3 digit code
        if country == "United Kingdom":
            code = "GBR"
        elif country == "South Korea":
            code = "KOR"
        elif country == "North Korea":
            code = "PRK"
        else:
            code = country_codes.loc[country_codes['country'] == country]["code"].values[0]

        op_df.at[idx, "code"] = code
    except IndexError:
        print("Country not accounted for: ", country)

    if country == 'Spain':
        players_df = pd.read_sql_query("SELECT * from players WHERE country = 'Spain' "
                                       "OR country = 'Basque Country' "
                                       "OR country = 'Catalonia'" , conn)
    elif country == 'United Kingdom':
        players_df = pd.read_sql_query("SELECT * from players WHERE country = 'United Kingdom' "
                                       "OR country = 'England' "
                                       "OR country = 'Scotland' "
                                       "OR country = 'Wales'", conn)
    else:
        players_df = pd.read_sql_query("SELECT * from players WHERE country = '{}'".format(country), conn)

    wins = players_df["wins"].sum()
    losses = players_df["losses"].sum()
    draws = players_df["draws"].sum()

    white_elo, black_elo = 0, 0
    white_games, black_games = 0, 0
    for p in range(len(players_df)):
        query = "SELECT * from games WHERE White = '{}'".format(players_df.iloc[p]["username"])
        try:
            white_df = pd.read_sql_query(query, conn)
            white_elo += int(white_df["WhiteElo"].values[0])
            white_games += len(white_df)
        except pandas.io.sql.DatabaseError:
            pass
        except IndexError:
            pass

        query = "SELECT * from games WHERE Black = '{}'".format(players_df.iloc[p]["username"])
        try:
            black_df = pd.read_sql_query(query, conn)
            black_elo += int(black_df["BlackElo"].values[0])
            black_games += len(black_df)
        except pandas.io.sql.DatabaseError:
            pass
        except IndexError:
            pass

    avg_elo = int((white_elo + black_elo) / (white_games + black_games))

    op_df.at[idx, "wins"] += wins
    op_df.at[idx, "losses"] += losses
    op_df.at[idx, "draws"] += draws
    op_df.at[idx, "text"] = "{}: [{} win(s), {} loss(es), {} draw(s)]\nAverage elo: {}".format(
        op_df.at[idx, "country"],
        op_df.at[idx, "wins"], op_df.at[idx, "losses"], op_df.at[idx, "draws"],
        avg_elo
    )

op_df["score"] = (100 * (op_df["wins"] + 0.5 * op_df["draws"]) / (op_df["wins"] + op_df["losses"] + op_df["draws"]))
op_df = op_df.dropna()

fig = go.Figure(data=go.Choropleth(
    locations = op_df["code"],
    z = np.round(op_df["score"], 2),
    text = op_df['text'],
    colorscale = 'RdYlGn',
    autocolorscale=False,
    colorbar_title = 'score',
))

fig.update_layout(
    title_text='My Results vs. the World',
    geo=dict(
        showframe=False,
        showcoastlines=False,
        showcountries=True,
        # projection_type='orthographic',
        projection_type='equirectangular',
    ),
    annotations = [dict(
        x=0.55,
        y=0.1,
    )]
)

fig.show()