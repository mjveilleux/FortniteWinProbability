

# This is the final product of the code which ends with an interactive Python Shiny App
# The code is broken up into four categories
#   1. Game Log Extract
#   2. API Connect
#   3. Monte Carlo Simulation
#   4. Shiny App

# Current run time is about 20 seconds: need to optimize API call

# GAME LOG EXRACT
import re
import os
import datetime
import pandas as pd

with open(r"C:\Users\mason\AppData\Local\FortniteGame\Saved\Logs\FortniteGame.log", 'r', encoding='utf-8')  as f:
    skydive_lines = [line.strip() for line in f if 'begin skydiving from bus' in line] # take all the lines that have this string
    player_data = {'match_time': [], 'code': [], 'player_id': [], 'player_name': []} # make your columns
    for line in skydive_lines:
        data = re.findall(r'\[(.*?)\]', line) # antthing within the brackets
        player_data['match_time'].append(pd.to_datetime(data[0], format='%Y.%m.%d-%H.%M.%S:%f')) # time is the first bracket in this line
        player_data['code'].append(data[1]) # the code is the second bracket of the line
        player_data['player_id'].append(data[2]) # and so on.....
        player_data['player_name'].append(data[3])

    df = pd.DataFrame.from_dict(player_data) # convert this dict into a pandas dataframe

    # Calculate match number based on time difference
    time_diff = df['match_time'].diff().fillna(pd.Timedelta(seconds=0))
    is_new_match = time_diff >= pd.Timedelta(minutes=5) # if the time difference between two lines is more than 5 minutes, then we are in a new match
    df['match_number'] = is_new_match.cumsum() + 1 # add in the new match number
    df.to_csv(f"C:/Users/mason/Dropbox/FortniteSkillMatch_project/script/match_data/skydiving_data{datetime.datetime.now().strftime('%m-%d-%Y.%H.%M.%S')}.csv", index=False) # save to a csv ... Will need to update this and save to DB later


# API CONNECT

import json
import requests
import pandas as pd

url = 'https://fortnite-api.com/v2/stats/br/v2'

player_names = df[df["match_number"] == df["match_number"].max()]["player_name"].tolist()
account_types = ['epic'] #, 'xbl', 'psn'

headers = dict(
    Authorization = 'ca628b24-87e1-4722-adcf-5d866a5df690'
)

data_rows = []
for name in player_names:
    found = False
    for account_type in account_types:
        params = dict(
            name=name,
            AccountType=account_type,
            timeWindow='lifetime',
            image='none'
        )
        data = requests.get(url=url, params=params, headers=headers)
        if data.status_code == 200:
            data_json = data.json()
            # get player stats
            indent1_stats = data_json["data"]
            indent2_stats = indent1_stats['stats']
            indent3_stats = indent2_stats['all']
            indent4_stats = indent3_stats['solo']

            # This is the unique players solo data
            # df = pd.DataFrame(d.indent4_stats(), columns=['group', 'value'])
            df_stats = pd.DataFrame([indent4_stats])
            df_stats = df_stats.rename_axis("group").reset_index()
            df_stats['player_name'] = name
            df_stats['status'] = 'public'
            data_rows.append(df_stats)
            found = True
            break
    if not found:
        df_stats = pd.DataFrame({'player_name': [name], 'status': ['private']})
        data_rows.append(df_stats)

df_stats = pd.concat(data_rows)

# left join df stats on df

merged_df = pd.merge(df, df_stats, on="player_name", how="inner")
unique_df = merged_df.drop_duplicates()

# MONTE CARLO SIMULATION

## Get player and skill measure
import numpy as np

latest_match = unique_df[unique_df["match_number"] == unique_df["match_number"].max()]
#latest_match = latest_match[["player_name", "kd"]]
latest_match = latest_match.loc[:, ["player_name", "kd"]][~latest_match["kd"].isna()]
latest_match = latest_match.reset_index(drop=True)

## Get the overall outcome of the match based on skill


# Define a function to simulate a game
def simulate_game(kd1, kd2):
    p1_score = np.random.normal(kd1, 1)
    p2_score = np.random.normal(kd2, 1)
    if p1_score > p2_score:
        return 1
    else:
        return 2



def overall_rankings(latest_match):
    # Create a DataFrame to store the win-loss records for each player
    records = pd.DataFrame({'player_name': latest_match['player_name'], 'wins': 0, 'losses': 0})
    
    # Iterate through all player matchups and update records accordingly
    for i, row in latest_match.iterrows():
        for j, other_row in latest_match.iterrows():
            if i != j:
                num_wins = 0
                num_losses = 0
                num_simulations = 10000
                for _ in range(num_simulations):
                    winner = simulate_game(row['kd'], other_row['kd'])
                    if winner == 1:
                        num_wins += 1
                    else:
                        num_losses += 1
                records.loc[records['player_name'] == row['player_name'], 'wins'] += num_wins
                records.loc[records['player_name'] == row['player_name'], 'losses'] += num_losses
    
    # Calculate win percentages and add a rank column
    records['win_pct'] = records['wins'] / (records['wins'] + records['losses'])
    records = records.sort_values('win_pct', ascending=False).reset_index(drop=True)
    records['rank'] = records.index + 1
    
    return records


overall_rankings_df = overall_rankings(latest_match)
#print(overall_rankings_df)


## Get the individual probability of win against oppenent

def simulate_matchups(latest_match):
    num_players = len(latest_match)
    matchups = pd.DataFrame(np.zeros((num_players, num_players)), index=latest_match['player_name'], columns=latest_match['player_name'])
    
    for i, p1 in enumerate(latest_match['player_name']):
        for j, p2 in enumerate(latest_match['player_name']):
            if i != j:
                p1_wins = 0
                num_simulations = 10000
                for _ in range(num_simulations):
                    if simulate_game(latest_match['kd'][i], latest_match['kd'][j]) == 1:
                        p1_wins += 1
                matchups.loc[p1, p2] = p1_wins / num_simulations
    user_name = 'Keep_OLS_Blue'
    a_wins = matchups.loc[user_name].sort_values(ascending=False)
    ranks = pd.DataFrame({'player_name': a_wins.index, 'win_prob': a_wins.values, 'rank': range(1, num_players + 1)})
    
    return ranks

rankings = simulate_matchups(latest_match)
#print(rankings)


# SHINY APP
# Run shiny app file


















