import streamlit as st
st.set_page_config(layout="wide")
import qbstreamlit.utils
import qbstreamlit.data
import qbstreamlit.tables
import qbstreamlit.charts
import glob

for k, v in st.session_state.items():
    st.session_state[k] = v

with st.sidebar:
    st.selectbox(
        "Tournament",
        [path[5:] for path in glob.glob('qbjs/*')],
        key = "tournament",
        format_func=lambda x: x.capitalize(),
        on_change=qbstreamlit.utils.populate_db
    )

qbstreamlit.utils.local_css("style.css")

st.title(f'{st.session_state.tournament.capitalize()} Miscellaneous Graphs')

if st.session_state.powers:
    column_dict = {15: 'P', 10: 'G', -5: 'N'}
    buzz_values = ['P', 'G', 'N']
    rename_dict = {'P': '15', 'G': '10', 'N': '-5', 'Games': 'G'}
else:
    column_dict = {10: 'G', -5: 'N'}
    buzz_values = ['G', 'N']
    rename_dict = {'G': '10', 'N': '-5', 'Games': 'G'}

buzzes = qbstreamlit.data.load_buzzes()
tossup_meta = qbstreamlit.data.load_tossup_meta()
packet_meta = qbstreamlit.data.get_packet_meta(st.session_state.tournament)

full_buzzes = buzzes.merge(
    tossup_meta, on=['packet', 'tossup']
    ).merge(
        packet_meta, on=['packet', 'tossup']
        )

full_buzzes['celerity'] = 1 - full_buzzes['buzz_position']/full_buzzes['tossup_length']

player_stats = qbstreamlit.data.load_player_stats()
player_games = player_stats.groupby(
    ['player', 'team']
    ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})
player_bpa, player_cat_bpa = qbstreamlit.data.load_player_bpa()

player_summary = full_buzzes.groupby(
    ['player', 'team', 'value']
).agg(
    'size'
).reset_index().pivot(
    index=['player', 'team'], columns='value', values=0
).reset_index().rename(columns=column_dict).merge(
                        player_games, on=['player', 'team']
                        ).merge(
                            player_bpa, on = ['player', 'team']
                        ).assign(
                            BPA = lambda x: round(x.BPA, 3),
                            ACC = lambda x: round(x.ACC, 3),
                        )

player_summary = player_summary[['player', 'team', 'Games'] + buzz_values + ['BPA', 'ACC']].fillna(0).assign(
    Pts=lambda x: qbstreamlit.utils.calc_pts(x)
).sort_values(['Pts'], ascending=False)
player_summary['PPG'] = round(player_summary['Pts']/player_summary['Games'], 2)
player_summary = player_summary[['player', 'team', 'Games'] + buzz_values + ['Pts', 'PPG', 'BPA', 'ACC']].rename(
    columns=rename_dict
)


st.altair_chart(qbstreamlit.charts.make_bpa_ppg_chart(player_summary))