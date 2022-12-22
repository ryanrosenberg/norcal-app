import streamlit as st
st.set_page_config(layout="wide")
import numpy as np
import qbstreamlit.utils
import qbstreamlit.data
import qbstreamlit.tables
import qbstreamlit.charts
import glob

for k, v in st.session_state.items():
    st.session_state[k] = v
    
if st.session_state.powers:
    column_dict = {15: 'P', 10: 'G', -5: 'N'}
    buzz_values = ['P', 'G', 'N']
    rename_dict = {'P': '15', 'G': '10', 'N': '-5', 'Games': 'G'}
else:
    column_dict = {10: 'G', -5: 'N'}
    buzz_values = ['G', 'N']
    rename_dict = {'G': '10', 'N': '-5', 'Games': 'G'}
    
with st.sidebar:
    st.selectbox(
        "Tournament",
        [path[5:] for path in glob.glob('qbjs/*')],
        key = "tournament",
        format_func=lambda x: x.capitalize(),
        on_change=qbstreamlit.utils.populate_db
    )

qbstreamlit.utils.local_css("style.css")

st.title(f'{st.session_state.tournament.capitalize()} Category Stats')

st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
            unsafe_allow_html=True)

buzzes = qbstreamlit.data.load_buzzes()
tossup_meta = qbstreamlit.data.load_tossup_meta()
packet_meta = qbstreamlit.data.get_packet_meta(st.session_state.tournament)

full_buzzes = buzzes.merge(
    tossup_meta, on=['packet', 'tossup']
    ).merge(
        packet_meta, on=['packet', 'tossup']
        )

full_buzzes['celerity'] = 1 - full_buzzes['buzz_position']/full_buzzes['tossup_length']

player_bpa, player_cat_bpa = qbstreamlit.data.load_player_bpa()
team_bpa, team_cat_bpa = qbstreamlit.data.load_team_bpa()

player_stats = qbstreamlit.data.load_player_stats()
player_games = player_stats.groupby(
    ['player', 'team']
    ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})

team_stats = qbstreamlit.data.load_team_stats()
team_games = team_stats.groupby(
    ['team']
    ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})

cats = full_buzzes['category'].unique()
cats.sort()
filter_categories = st.multiselect('Categories', cats, default=[])

tossup_cat = st.container()

with tossup_cat:
    if len(filter_categories) > 0:
        filter_buzzes = full_buzzes[full_buzzes['category'].isin(filter_categories)]
        subcats = filter_buzzes['subcategory'].unique()
        filter_subcategories = st.multiselect('Subcategories', subcats, default=subcats)
        chart_buzzes = filter_buzzes[filter_buzzes['subcategory'].isin(filter_subcategories)]
        chart_buzzes['num'] = chart_buzzes.groupby(['buzz_position']).cumcount()+1
        category_summary = chart_buzzes.groupby(
            ['player', 'team', 'category', 'value']
            ).agg(
                'size'
                ).reset_index().pivot(
                    index = ['player', 'team', 'category'], columns='value', values=0
                    ).reset_index().rename(columns=column_dict).merge(
                        player_games, on=['player', 'team']
                        )
                        
        if len(filter_categories) == 1 and len(filter_subcategories) == len(subcats):
            print(len(filter_categories))
            category_summary = category_summary.merge(
                            player_cat_bpa, on=['player', 'team', 'category']
                        )

        team_category_summary = chart_buzzes.groupby(
            ['team', 'category', 'value']
            ).agg(
                'size'
                ).reset_index().pivot(
                    index = ['team', 'category'], columns='value', values=0
                    ).reset_index().rename(columns=column_dict).merge(
                        team_games, on=['team']
                        )
        if len(filter_categories) == 1 and len(filter_subcategories) == len(subcats):
            team_category_summary = team_category_summary.merge(
                        team_cat_bpa, on=['team', 'category']
                    )

    else:
        chart_buzzes = full_buzzes
        chart_buzzes['num'] = full_buzzes.groupby(['buzz_position']).cumcount()+1
        category_summary = full_buzzes.groupby(
            ['player', 'team', 'value']
            ).agg(
                'size'
                ).reset_index().pivot(
                    index = ['player', 'team'], columns='value', values=0
                    ).reset_index().rename(columns=column_dict).merge(
                        player_games, on=['player', 'team']
                        ).merge(
                            player_bpa, on=['player', 'team']
                        )
        team_category_summary = chart_buzzes.groupby(
            ['team', 'value']
            ).agg(
                'size'
                ).reset_index().pivot(
                    index = ['team'], columns='value', values=0
                    ).reset_index().rename(columns=column_dict).merge(
                        team_games, on=['team']
                        ).merge(
                            team_bpa, on=['team']
                        )

    for x in buzz_values:
        if x not in category_summary.columns:
            category_summary[x] = 0

    if len(filter_categories) == 1 and len(filter_subcategories) == len(subcats):
        player_stats = category_summary[['player', 'team', 'Games'] + buzz_values + ['BPA']].fillna(0).assign(
            Pts = lambda x: qbstreamlit.utils.calc_pts(x),
            BPA = lambda x: round(x.BPA, 3)
            ).sort_values(('Pts'), ascending=False)

        team_stats = team_category_summary[['team', 'Games'] + buzz_values + ['BPA']].fillna(0).assign(
            Pts = lambda x: qbstreamlit.utils.calc_pts(x),
            BPA = lambda x: round(x.BPA, 3)
            ).sort_values(('Pts'), ascending=False)

    elif len(filter_categories) == 0:
        player_stats = category_summary[['player', 'team', 'Games'] + buzz_values + ['BPA']].fillna(0).assign(
            Pts = lambda x: qbstreamlit.utils.calc_pts(x),
            BPA = lambda x: round(x.BPA, 3)
            ).sort_values(('Pts'), ascending=False)

        team_stats = team_category_summary[['team', 'Games'] + buzz_values + ['BPA']].fillna(0).assign(
            Pts = lambda x: qbstreamlit.utils.calc_pts(x),
            BPA = lambda x: round(x.BPA, 3)
            ).sort_values(('Pts'), ascending=False)
            
    else:
        if st.session_state['powers']:
            player_stats = category_summary[['player', 'team', 'Games'] + buzz_values].groupby(
                ['player', 'team']
                ).agg(
                    Games= ('Games', np.mean), P = ('P', np.sum), 
                    G = ('G', np.sum), N = ('N', np.sum)
                ).reset_index().fillna(0).assign(
                Pts = lambda x: qbstreamlit.utils.calc_pts(x)
                ).sort_values(('Pts'), ascending=False)

            team_stats = team_category_summary[['team', 'Games'] + buzz_values].groupby(
            ['team']
            ).agg(
                Games= ('Games', np.mean), P = ('P', np.sum), 
                G = ('G', np.sum), N = ('N', np.sum)
            ).reset_index().fillna(0).assign(
            Pts = lambda x: qbstreamlit.utils.calc_pts(x)
            ).sort_values(('Pts'), ascending=False)
        else:
            player_stats = category_summary[['player', 'team', 'Games'] + buzz_values].groupby(
                ['player', 'team']
                ).agg(
                    Games= ('Games', np.mean), 
                    G = ('G', np.sum), N = ('N', np.sum)
                ).reset_index().fillna(0).assign(
                Pts = lambda x: qbstreamlit.utils.calc_pts(x)
                ).sort_values(('Pts'), ascending=False)

            team_stats = team_category_summary[['team', 'Games'] + buzz_values].groupby(
            ['team']
            ).agg(
                Games= ('Games', np.mean),
                G = ('G', np.sum), N = ('N', np.sum)
            ).reset_index().fillna(0).assign(
            Pts = lambda x: qbstreamlit.utils.calc_pts(x)
            ).sort_values(('Pts'), ascending=False)
        player_stats[buzz_values + ['Pts']] = player_stats[buzz_values + ['Pts']].astype(int)

        
 
    team_stats[buzz_values + ['Pts']] = team_stats[buzz_values + ['Pts']].astype(int)

players, teams = st.tabs(["Players", "Teams"])

with players:
    st.markdown(qbstreamlit.tables.df_to_kable(player_stats),
            unsafe_allow_html=True)

with teams:
    st.markdown(qbstreamlit.tables.df_to_kable(team_stats),
            unsafe_allow_html=True)