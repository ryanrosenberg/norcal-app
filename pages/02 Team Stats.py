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

st.title(f'{st.session_state.tournament.capitalize()} Team Stats')

st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
            unsafe_allow_html=True)

if st.session_state.powers:
    column_dict = {15: 'P', 10: 'G', -5: 'N'}
    buzz_values = ['P', 'G', 'N']
    rename_dict = {'P': '15', 'G': '10', 'N': '-5', 'Games': 'G'}
else:
    column_dict = {10: 'G', -5: 'N'}
    buzz_values = ['G', 'N']
    rename_dict = {'G': '10', 'N': '-5', 'Games': 'G'}

buzzes = qbstreamlit.data.load_buzzes()
bonuses = qbstreamlit.data.load_bonuses()
tossup_meta = qbstreamlit.data.load_tossup_meta()
if st.session_state.tournament_bonuses:
    bonus_meta = qbstreamlit.data.load_bonus_meta()
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
player_games['TUH'] = player_games['Games']*20
player_bpa, player_cat_bpa = qbstreamlit.data.load_player_bpa()
team_bpa, team_cat_bpa = qbstreamlit.data.load_team_bpa()
team_games = player_stats.groupby(
    ['team']
    ).agg({'game_id': 'nunique'}).reset_index().rename(columns = {'game_id': 'Games'})

team_summary = full_buzzes.groupby(
    ['team', 'value']
).agg(
    'size'
).reset_index().pivot(
    index=['team'], columns='value', values=0
).reset_index().rename(columns=column_dict).merge(
    team_bpa, on=['team']
)


team_cat_ranks = full_buzzes.groupby(['team', 'category', 'value']).agg(
    'size'
).reset_index().pivot(
    index=['team', 'category'], columns='value', values=0
).reset_index().rename(columns=column_dict)

team_summary = qbstreamlit.utils.fill_out_tossup_values(team_summary)
team_cat_ranks = qbstreamlit.utils.fill_out_tossup_values(team_cat_ranks)

team_summary = team_summary[['team'] + buzz_values + ['BPA', 'ACC']].fillna(0).assign(
    Pts=lambda x: qbstreamlit.utils.calc_pts(x),
    BPA = lambda x: round(x.BPA, 3),
    ACC = lambda x: round(x.ACC, 3)
).sort_values(['Pts'], ascending=False).merge(
    team_games, on="team"
)

team_summary = team_summary[['team', 'Games'] + buzz_values + ['Pts', 'BPA', 'ACC']]

team_cat_ranks = team_cat_ranks[['team', 'category'] + buzz_values].fillna(0).assign(
    Pts=lambda x: qbstreamlit.utils.calc_pts(x)
)
team_cat_ranks['rank'] = team_cat_ranks.groupby(
    'category')['Pts'].rank('min', ascending=False)

team_list, team_detail = st.columns(2)
with team_list:
    st.header('Tossup data')
    st.write("Click on a team's row to show more information!")
    selection = qbstreamlit.tables.aggrid_interactive_table(team_summary)
qbstreamlit.utils.hr()

if selection["selected_rows"]:
    with team_detail:
        st.header(selection['selected_rows'][0]['team'])
        team_buzzes = full_buzzes[full_buzzes['team']
                                  == selection["selected_rows"][0]['team']]

        tab1, tab2, tab3 = st.tabs(['Players', 'Categories', 'Subcategories'])
        with tab1:
            player_stats = team_buzzes.groupby(
                ['player', 'team', 'value']
            ).agg('size').reset_index().pivot(
                index=['player', 'team'], columns='value', values=0
            ).reset_index().rename(columns=column_dict).merge(
                        player_games, on=['player', 'team']
                        ).merge(
                            player_bpa, on=['player', 'team']
                        )

            player_stats = qbstreamlit.utils.fill_out_tossup_values(player_stats).fillna(
                0).assign(Pts=lambda x: qbstreamlit.utils.calc_pts(x))[['player', 'Games'] + buzz_values + ['Pts', 'BPA', 'ACC']]
            player_stats[buzz_values + ['Pts']] = player_stats[buzz_values + ['Pts']].astype(int)
            player_stats['PPG'] = round(player_stats['Pts']/player_stats['Games'], 2)
            player_stats['BPA'] = round(player_stats['BPA'], 3)
            player_stats['ACC'] = round(player_stats['ACC'], 3)
            player_stats = player_stats[['player', 'Games'] + buzz_values + ['Pts', 'PPG', 'BPA', 'ACC']]
            st.markdown(
                qbstreamlit.tables.df_to_kable(
                    player_stats.sort_values('Pts', ascending=False)
                    ),
                    unsafe_allow_html=True)

        team_cats = team_buzzes.groupby(
            ['team', 'category', 'value']
        ).agg('size').reset_index().pivot(
            index=['team', 'category'], columns='value', values=0
        ).reset_index().rename(columns=column_dict)

        team_cats = qbstreamlit.utils.fill_out_tossup_values(team_cats)

        print(team_cats)
        team_cats = team_cats[['team', 'category'] + buzz_values].fillna(
            0).assign(Pts=lambda x: qbstreamlit.utils.calc_pts(x))
        team_cats[buzz_values + ['Pts']] = team_cats[buzz_values + ['Pts']].astype(
            int).sort_values(['Pts'], ascending=False)
        team_rank = team_cats.merge(
            team_cat_ranks[['team', 'category', 'rank']], on=['team', 'category'])
        team_rank = team_rank[['team', 'category'] + buzz_values + ['Pts', 'rank']].rename(
            columns={'rank': 'Rk'}).merge(
                team_cat_bpa, on = ['team', 'category']
            ).assign(
                BPA = lambda x: round(x.BPA, 3),
                ACC = lambda x: round(x.ACC, 3)
            )
        team_rank['Rk'] = team_rank['Rk'].astype(int)
        team_rank = team_rank[['category'] + buzz_values + ['Pts', 'Rk', 'BPA', 'ACC']]

        with tab2:
            st.markdown(qbstreamlit.tables.df_to_kable(team_rank),
            unsafe_allow_html=True)

        team_subcats = team_buzzes.groupby(['category', 'subcategory', 'value']).agg(
            'size'
        ).reset_index().pivot(
            index=['category', 'subcategory'], columns='value', values=0
        ).reset_index().rename(columns=column_dict)

        team_subcats = qbstreamlit.utils.fill_out_tossup_values(team_subcats)

        team_subcats = team_subcats[['category', 'subcategory'] + buzz_values].fillna(
            0).assign(Pts=lambda x: qbstreamlit.utils.calc_pts(x))
        team_subcats[buzz_values + ['Pts']] = team_subcats[buzz_values + ['Pts']].astype(
            int).sort_values(['Pts'], ascending=False)

        with tab3:
            st.markdown(qbstreamlit.tables.df_to_kable(team_subcats),
            unsafe_allow_html=True)

    st.header("Buzzes")
    team_buzzes['packet'] = team_buzzes['packet'].astype(int)
    team_buzzes['answer'] = [qbstreamlit.utils.sanitize_answer(
        answer, remove_formatting=False) for answer in team_buzzes['answer']]
    qbstreamlit.tables.aggrid_interactive_table(
        team_buzzes[['packet', 'tossup', 'category', 'subcategory',
                    'answer', 'player', 'value', 'buzz_position']]
    )
    
    st.header("Category Buzzpoints")
    negs = st.checkbox("Add negs?")
    st.altair_chart(qbstreamlit.charts.make_category_buzz_chart(team_buzzes, negs))

if st.session_state.tournament_bonuses:    
    qbstreamlit.utils.hr()
    bonus_cat = st.container()
    full_bonuses = bonuses.merge(bonus_meta, on=['packet', 'bonus'])

    bonus_summary = full_bonuses.assign(
        tot=lambda x: x.part1_value + x.part2_value + x.part3_value
    ).groupby('team').agg({'tot': 'mean', 'part1_value': 'count'}).reset_index().rename(
        columns={'tot': 'PPB', 'part1_value': 'Bonuses'}
    ).sort_values('PPB', ascending=False)

    bonus_cat_summary = full_bonuses.assign(
        tot=lambda x: x.part1_value + x.part2_value + x.part3_value
    ).groupby(['team', 'category']).agg({'tot': 'mean'}).reset_index().rename(
        columns={'tot': 'PPB'}
    ).sort_values('PPB', ascending=False)

    bonus_summary['PPB'] = round(bonus_summary['PPB'], 2)
    bonus_summary = bonus_summary[['team', 'Bonuses', 'PPB']]

    col3, col4 = st.columns(2)

    with bonus_cat:
        st.header('Bonus data')
        with col3:
            selection = qbstreamlit.tables.aggrid_interactive_table(bonus_summary)
        if selection["selected_rows"]:
            team_bonuses = bonus_cat_summary[bonus_cat_summary['team']
                                            == selection["selected_rows"][0]['team']]
            team_bonuses['PPB'] = round(team_bonuses['PPB'], 2)
            with col4:
                st.altair_chart(qbstreamlit.charts.make_category_ppb_chart(
                    team_bonuses, bonus_cat_summary))
