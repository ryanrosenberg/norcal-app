import streamlit as st
st.set_page_config(layout="wide")
import qbstreamlit.utils
import qbstreamlit.data
import qbstreamlit.tables
import qbstreamlit.charts
import numpy as np
import glob

for k, v in st.session_state.items():
    st.session_state[k] = v

qbstreamlit.utils.local_css("style.css")

st.title(f'{st.session_state.tournament.capitalize()} Scoresheets')

st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
            unsafe_allow_html=True)

with st.sidebar:
    st.selectbox(
        "Tournament",
        [path[5:] for path in glob.glob('qbjs/*')],
        key = "tournament",
        format_func=lambda x: x.capitalize(),
        on_change=qbstreamlit.utils.populate_db
    )

buzzes = qbstreamlit.data.load_buzzes()
tossup_meta = qbstreamlit.data.load_tossup_meta()
full_buzzes = buzzes.merge(tossup_meta, on=['packet', 'tossup'])

if st.session_state.tournament_bonuses:
    bonuses = qbstreamlit.data.load_bonuses()
    bonus_meta = qbstreamlit.data.load_bonus_meta()
    full_bonuses = bonuses.merge(bonus_meta, on=['packet', 'bonus'])
else:
    full_bonuses = []

team_stats = qbstreamlit.data.load_team_stats()
player_stats = qbstreamlit.data.load_player_stats()


game_slugs = {}
for game_id in list(np.unique(team_stats['game_id'])):
    game_stats = team_stats[team_stats['game_id'] == game_id]

    if list(game_stats['Pts'])[0] > list(game_stats['Pts'])[1]:
        game_slugs[game_id] = f"{list(game_stats['team'])[0]} {list(game_stats['Pts'])[0]}, {list(game_stats['team'])[1]} {list(game_stats['Pts'])[1]}"
    else:
        game_slugs[game_id] = f"{list(game_stats['team'])[1]} {list(game_stats['Pts'])[1]}, {list(game_stats['team'])[0]} {list(game_stats['Pts'])[0]}"

print(team_stats[['game_id', 'packet']])
round_num = st.selectbox("Round", range(1, 12))
game_num = st.selectbox(
    "Game", 
    list(np.unique(team_stats[team_stats['packet'] == round_num]['game_id'])), 
    format_func=lambda x: game_slugs[x])

team1, team2, scoresheets = st.columns(3)

# @st.cache
# def generate_links(round):
#     links = []

#     links.append(f"<h2 id = 'packet-{int(round)}'>Round {int(round)}</h2>")
#     for i in team_stats[team_stats['packet'] == round]['game_id'].unique():
#         team1_score = team_stats[team_stats['game_id'] == i]['total_points'].tolist()[0]
#         team2_score = team_stats[team_stats['game_id'] == i]['total_points'].tolist()[1]
#         if team1_score > team2_score:
#             line = f"""{team_stats[team_stats['game_id'] == i]['team'].tolist()[0]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[0])},
#             {team_stats[team_stats['game_id'] == i]['team'].tolist()[1]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[1])}"""
#         else:
#             line = f"""{team_stats[team_stats['game_id'] == i]['team'].tolist()[1]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[1])},
#             {team_stats[team_stats['game_id'] == i]['team'].tolist()[0]} {int(team_stats[team_stats['game_id'] == i]['total_points'].tolist()[0])}"""
#         links.append(f"<p><a href='#top' id='{i}'>{line}</a></p>")
#     content = ' '.join(links)
#     return content

# with games:
#     clicked = click_detector(generate_links(round_num))

# scoresheets.markdown(f"**{clicked} clicked**" if clicked != "" else "**No click**")
# scoresheets.dataframe(qbstreamlit.charts.make_scoresheet(clicked, full_buzzes, full_bonuses, player_stats))
game_player_stats = player_stats[player_stats['game_id'] == game_num]
game_player_stats_disp = game_player_stats.rename(columns = {'15': 'P', '10': 'G', '-5': 'N'})
print(game_player_stats_disp)
with team1:
    st.subheader(game_player_stats_disp['team'].unique().tolist()[0])
    st.markdown(qbstreamlit.tables.df_to_kable(game_player_stats_disp[game_player_stats_disp['team'] == game_player_stats_disp['team'].unique().tolist()[0]][['player', 'team', 'G', 'N', 'Pts']].sort_values(['player'])),
            unsafe_allow_html=True)
with team2:
    st.subheader(game_player_stats_disp['team'].unique().tolist()[1])
    st.markdown(qbstreamlit.tables.df_to_kable(game_player_stats_disp[game_player_stats_disp['team'] == game_player_stats_disp['team'].unique().tolist()[1]][['player', 'team', 'G', 'N', 'Pts']].sort_values(['player'])),
            unsafe_allow_html=True)

c = qbstreamlit.charts.make_scoresheet(game_num, full_buzzes, full_bonuses, game_player_stats, has_bonuses = False)

scoresheets.altair_chart(c, theme=None)
# scoresheets.dataframe(c)