import core
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

plt.style.use('ggplot')

user = 'roudiere'
dbt = core.DatabaseTool()

def get_time_controls():
    df = dbt.get()
    return set(df["TimeControl"].values)

def plot_games_by_time_control(time_control):
    columns_of_interest = ["Date", "White", "Black", "WhiteElo", "BlackElo", "StartTime"]
    times = None
    if time_control == 'rapid':
        times = ["600", "900+10"]
    elif time_control == 'blitz':
        times = ["300", "180+2", "180"]
    elif time_control == 'bullet':
        times = ["60", "120+1"]
    elif time_control == 'daily':
        times = ["1/86400", "1/259200"]
    else:
        print("[!] Time control not recognized")
        exit(0)

    games = dbt.get({"TimeControl": times[0]})
    for element in times:
        if element != times[0]:
            games = pd.concat([games, dbt.get({"TimeControl": element})])

    games = games[columns_of_interest]

    games['elo'] = [row["WhiteElo"] if row["White"] == user else row["BlackElo"] for index, row in games.iterrows()]
    rapid_games = games[["Date", "elo", "StartTime"]]

    rg = rapid_games.groupby(["Date"])

    elo_stock = {
        "date":   [],
        "open":   [],
        "high":   [],
        "low":    [],
        "close":  [],
        "volume": []
    }

    for key, item in rg:
        group = rg.get_group(key)

        elo_stock["date"].append(group["Date"].values[0])
        elo_stock["open"].append(group[group["StartTime"] == group["StartTime"].min()].elo)
        elo_stock["high"].append(group.elo.max())
        elo_stock["low"].append(group.elo.min())
        elo_stock["close"].append(group[group["StartTime"] == group["StartTime"].max()].elo)
        elo_stock["volume"].append(len(group))


    es_df = pd.DataFrame(elo_stock, index=elo_stock["date"])
    es_df.index.name = "date"
    es_df = es_df[[c for c in es_df.columns if c != "date"]]    # remove 'date' column
    es_df.index = pd.to_datetime(es_df.index)                   # so mpl-finance can parse the index
    es_df = es_df.astype(int)                                   # so mpl-finance can parse the values

    es_df.to_csv('datasets/elo/{}_elostock_{}.csv'.format(user, time_control))

    # https://github.com/matplotlib/mplfinance/blob/master/examples/plot_customizations.ipynb
    # https://github.com/matplotlib/mplfinance/blob/master/examples/savefig.ipynb
    mpf.plot(es_df, type="candle", mav=30, volume=True, title="\n\n{}'s {} elo".format(user, time_control),
             ylabel='Elo', ylabel_lower='Games', savefig='datasets/elo/elo_{}.png'.format(time_control))


print('(chess_stock) creating graphs by time control...')
plot_games_by_time_control("blitz")
plot_games_by_time_control("rapid")
plot_games_by_time_control("bullet")
