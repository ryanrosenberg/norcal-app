import streamlit as st
st.set_page_config(layout="wide")
import qbstreamlit.utils
import qbstreamlit.data
import qbstreamlit.tables
import qbstreamlit.charts
import glob

for k, v in st.session_state.items():
    st.session_state[k] = v

qbstreamlit.utils.local_css("style.css")

st.title(f'{st.session_state.tournament.capitalize()} Tossups')

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
category_acc = full_buzzes[full_buzzes['value'].isin([15, 10])].groupby(
    ['category']
).agg({'celerity': 'mean'}).reset_index().rename(columns={'celerity': 'ACC'})
category_acc['ACC'] = round(category_acc['ACC'], 3)

subcategory_acc = full_buzzes[full_buzzes['value'].isin([15, 10])].groupby(
    ['category', 'subcategory']
).agg({'celerity': 'mean'}).reset_index().rename(columns={'celerity': 'ACC'})
subcategory_acc['ACC'] = round(subcategory_acc['ACC'], 3)

tossup_acc = full_buzzes[full_buzzes['value'].isin([15, 10])].groupby(
    ['packet', 'tossup', 'category', 'subcategory']
).agg({'celerity': 'mean'}).reset_index().rename(columns={'celerity': 'ACC'})
tossup_acc['ACC'] = round(tossup_acc['ACC'], 3)

tossup_summary = full_buzzes.groupby(
        ['packet', 'tossup', 'category', 'subcategory', 'answer', 'value']
        ).agg(
            'size'
            ).reset_index().pivot(
                index = ['packet', 'tossup', 'category', 'subcategory', 'answer',], columns='value', values=0
                ).reset_index().rename(columns=column_dict)

for x in buzz_values:
        if x not in tossup_summary.columns:
            tossup_summary[x] = 0

packet_games = full_buzzes.groupby('packet').agg(
    {'game_id': 'nunique'}
    ).reset_index().rename(columns={'game_id': 'TU'})
packet_games[['packet']] = packet_games[['packet']].astype(int)

tossup_table = tossup_summary.merge(packet_games, on = 'packet')
tossup_table['answer'] = [qbstreamlit.utils.sanitize_answer(answer, remove_formatting=False) for answer in tossup_table['answer']]
tossup_table = tossup_table[['packet', 'tossup', 'category', 'subcategory', 'answer', 'TU'] + buzz_values].fillna(0)
tossup_table[['packet'] + buzz_values] = tossup_table[['packet'] + buzz_values].astype(int)

if st.session_state['powers']:
    tossup_table_sum = tossup_table.assign(
        power_pct = lambda x: round((x.P)/x.TU, 3), 
        conv_pct = lambda x: round((x.P + x.G)/x.TU, 3), 
        neg_pct = lambda x: round(x.N/x.TU, 3)
        ).rename(columns={'power_pct': 'Power%', 'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
            tossup_acc, on = ['packet', 'tossup', 'category', 'subcategory']
        )

    category_summary = tossup_table_sum.groupby(['category'], as_index=False).agg(
        {'TU': 'sum', 'P': 'sum', 'G': 'sum', 'N': 'sum'}
        ).assign(
        power_pct = lambda x: round((x.P)/x.TU, 3), 
        conv_pct = lambda x: round((x.P + x.G)/x.TU, 3), 
        neg_pct = lambda x: round(x.N/x.TU, 3)
        ).rename(columns={'power_pct': 'Power%', 'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
            category_acc, on = 'category'
        )
    subcategory_summary = tossup_table_sum.groupby(['category', 'subcategory'], as_index=False).agg(
        {'TU': 'sum', 'P': 'sum', 'G': 'sum', 'N': 'sum'}
        ).assign(
        power_pct = lambda x: round((x.P)/x.TU, 3), 
        conv_pct = lambda x: round((x.P + x.G)/x.TU, 3), 
        neg_pct = lambda x: round(x.N/x.TU, 3)
        ).rename(columns={'power_pct': 'Power%', 'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
            subcategory_acc, on = ['category', 'subcategory']
        )

else:
    tossup_table_sum = tossup_table.assign(
        conv_pct = lambda x: round((x.G)/x.TU, 3), 
        neg_pct = lambda x: round(x.N/x.TU, 3)
        ).rename(columns={'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
            tossup_acc, on = ['packet', 'tossup', 'category', 'subcategory']
        )

    category_summary = tossup_table_sum.groupby(['category'], as_index=False).agg(
        {'TU': 'sum', 'G': 'sum', 'N': 'sum'}
        ).assign(
        conv_pct = lambda x: round((x.G)/x.TU, 3), 
        neg_pct = lambda x: round(x.N/x.TU, 3)
        ).rename(columns={'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
            category_acc, on = 'category'
        )
    subcategory_summary = tossup_table_sum.groupby(['category', 'subcategory'], as_index=False).agg(
        {'TU': 'sum', 'G': 'sum', 'N': 'sum'}
        ).assign(
        conv_pct = lambda x: round((x.G)/x.TU, 3), 
        neg_pct = lambda x: round(x.N/x.TU, 3)
        ).rename(columns={'conv_pct': 'Conv%', 'neg_pct': 'Neg%'}).merge(
            subcategory_acc, on = ['category', 'subcategory']
        )

col1, col2 = st.columns(2)

with col1:
    st.header('Category Summary')
    st.markdown(qbstreamlit.tables.df_to_kable(category_summary),
            unsafe_allow_html=True)    
with col2:
    st.header('Subcategory Summary')
    st.markdown(qbstreamlit.tables.df_to_kable(subcategory_summary) ,
            unsafe_allow_html=True)
qbstreamlit.utils.hr()
st.header('All Tossups')         
qbstreamlit.tables.aggrid_interactive_table(tossup_table_sum)