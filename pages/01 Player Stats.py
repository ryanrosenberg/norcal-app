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

st.title(f'{st.session_state.tournament.capitalize()} Player Stats')

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

player_cat_ranks = full_buzzes.groupby(['player', 'team', 'category', 'value']).agg(
    'size'
).reset_index().pivot(
    index=['player', 'team', 'category'], columns='value', values=0
).reset_index().rename(columns=column_dict)

player_summary = qbstreamlit.utils.fill_out_tossup_values(player_summary)
player_cat_ranks = qbstreamlit.utils.fill_out_tossup_values(player_cat_ranks)

player_summary = player_summary[['player', 'team', 'Games'] + buzz_values + ['BPA', 'ACC']].fillna(0).assign(
    Pts=lambda x: qbstreamlit.utils.calc_pts(x)
).sort_values(['Pts'], ascending=False)
player_summary['PPG'] = round(player_summary['Pts']/player_summary['Games'], 2)
player_summary = player_summary[['player', 'team', 'Games'] + buzz_values + ['Pts', 'PPG', 'BPA', 'ACC']].rename(
    columns=rename_dict
)

player_cat_ranks = player_cat_ranks[['player', 'team', 'category'] + buzz_values].fillna(0).assign(
    Pts=lambda x: qbstreamlit.utils.calc_pts(x)
)
player_cat_ranks['rank'] = player_cat_ranks.groupby(
    'category')['Pts'].rank('min', ascending=False)

player_list, player_stats = st.columns([5, 4])
qbstreamlit.utils.hr()

with player_list:
    st.write("Click on a player's row to show more information!")
    selection = qbstreamlit.tables.aggrid_interactive_table(player_summary)

if selection["selected_rows"]:
    with player_stats:
        st.header(
            f"{selection['selected_rows'][0]['player']}, {selection['selected_rows'][0]['team']}")
        player_buzzes = full_buzzes[full_buzzes['player'] == selection["selected_rows"]
                                    [0]['player']][full_buzzes['team'] == selection["selected_rows"][0]['team']]
        player_cats = player_buzzes.groupby(
            ['player', 'team', 'category', 'value']
        ).agg('size').reset_index().pivot(
            index=['player', 'team', 'category'], columns='value', values=0
        ).reset_index().rename(columns=column_dict)

        player_cats = qbstreamlit.utils.fill_out_tossup_values(player_cats)

        player_cats = player_cats[['player', 'team', 'category'] + buzz_values].fillna(
            0).assign(Pts=lambda x: qbstreamlit.utils.calc_pts(x))
        player_cats[buzz_values + ['Pts']] = player_cats[buzz_values + ['Pts']].astype(
            int).sort_values(['Pts'], ascending=False)

        player_rank = player_cats.merge(player_cat_ranks[[
                                        'player', 'team', 'category', 'rank']], on=['player', 'team', 'category'])
        player_rank = player_rank[['player', 'team', 'category'] + buzz_values + ['Pts', 'rank']].rename(
            columns={'rank': 'Rk'}
            ).merge(
                player_cat_bpa, on=['player', 'team', 'category']
            )
        player_rank['Rk'] = player_rank['Rk'].astype(int)
        player_rank = player_rank[['category'] + buzz_values + ['Pts', 'Rk', 'BPA', 'ACC']].assign(
            BPA = lambda x: round(x.BPA, 3), ACC = lambda x: round(x.ACC, 3),
        )

    player_subcats = player_buzzes.groupby(['category', 'subcategory', 'value']).agg(
        'size'
    ).reset_index().pivot(
        index=['category', 'subcategory'], columns='value', values=0
    ).reset_index().rename(columns=column_dict)

    player_subcats = qbstreamlit.utils.fill_out_tossup_values(player_subcats)

    player_subcats = player_subcats[['category', 'subcategory'] + buzz_values].fillna(
        0).assign(Pts=lambda x: qbstreamlit.utils.calc_pts(x))
    player_subcats[buzz_values + ['Pts']] = player_subcats[buzz_values + ['Pts']].astype(
        int).sort_values(['Pts'], ascending=False)

    with player_stats:
        tab1, tab2 = st.tabs(["Categories", "Subcategories"])
    with tab1:
        st.markdown(
            qbstreamlit.tables.df_to_kable(player_rank),
            unsafe_allow_html=True
            )
    with tab2:
        st.markdown(
            qbstreamlit.tables.df_to_kable(player_subcats),
            unsafe_allow_html=True
            )

    st.header("Buzzes")
    player_buzzes['packet'] = player_buzzes['packet'].astype(int)
    packets = qbstreamlit.data.get_packets(st.session_state.tournament)

    contexts = []
    for i, row in player_buzzes.iterrows():
        packet_sani = packets[f"packets/{st.session_state.tournament}/packet{int(row['packet'])}.json"]['tossups'][row['tossup'] -
                                                                                        1]['question'].split(' ')
        context = packet_sani[row['buzz_position']-6:row['buzz_position']]
        contexts.append(' '.join(context))

    player_buzzes['context'] = [
        context + ' | *buzz* |' for context in contexts]
    player_buzzes['answer'] = [qbstreamlit.utils.sanitize_answer(
        answer, remove_formatting=False) for answer in player_buzzes['answer']]
    qbstreamlit.tables.aggrid_interactive_table(player_buzzes[['packet', 'tossup', 'category', 'subcategory', 'answer', 'buzz_position', 'value', 'context']].rename(
        columns={'buzz_position': 'word'}
    ).sort_values(['packet', 'tossup'])
    )
    qbstreamlit.utils.hr()

    st.header("Category Buzzpoint Graph")
    negs = st.checkbox("Add negs?")
    st.altair_chart(qbstreamlit.charts.make_category_buzz_chart(player_buzzes, negs))