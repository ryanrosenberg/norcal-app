from htbuilder import div, p
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

st.title(f'{st.session_state.tournament.capitalize()} Questions')

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

packet_nums = full_buzzes['packet'].unique().tolist()
packet_nums.sort()
pac = st.selectbox('Packet', options=packet_nums)
if st.session_state.tournament_bonuses:
    question_type = st.selectbox('Question Type', options=['Tossup', 'Bonus'])
else:
    question_type = st.selectbox('Question Type', options=['Tossup'])
if question_type == 'Tossup':
    tu = st.selectbox('Question Number', options=range(1, 21), format_func=lambda x: str(
        x) + ' (' + qbstreamlit.utils.sanitize_answer(full_buzzes['answer'][full_buzzes['packet'] == pac][full_buzzes['tossup'] == x].unique()[0]) + ')')
else:
    tu = st.selectbox('Question Number', options=range(1, 21), format_func=lambda x: str(
        x) + ' (' + qbstreamlit.utils.sanitize_answer(full_bonuses['answers'][full_bonuses['packet'] == pac][full_bonuses['bonus'] == x].unique()[0]) + ')')
qbstreamlit.utils.hr()
packets = qbstreamlit.data.get_packets(st.session_state.tournament)

if question_type == 'Tossup':
    sani = packets[f"packets/{st.session_state.tournament}/packet{pac}.json"]['tossups'][tu -
                                                           1]['question'].split(' ')
    qbuzz = full_buzzes[full_buzzes['packet']
                        == pac][full_buzzes['tossup'] == tu]

    for i, row in qbuzz.iterrows():
        if row['buzz_position'] > len(sani):
            print(row['buzz_position'], len(sani))
            row['buzz_position'] = len(sani)
        if row['value'] in [15, 10]:
            sani[row['buzz_position'] - 1] = str(
                div(_class='buzz')(
                    sani[row['buzz_position'] - 1],
                    p(_class='buzz-value correct-buzz-value')(' ' +
                                                              str(row['value']))
                )
            )
        else:
            sani[row['buzz_position'] - 1] = str(
                div(_class='buzz')(
                    sani[row['buzz_position'] - 1],
                    p(_class='buzz-value incorrect-buzz-value')(' ' +
                                                                str(row['value']))
                )
            )

    sani = ' '.join(sani)

    st.markdown(f'<div class = "question-text">{sani}</div>',
                unsafe_allow_html=True)
    st.markdown('<div class = "question-text">ANSWER: ' + packets[f"packets/{st.session_state.tournament}/packet{pac}.json"]['tossups'][tu - 1]['answer'] + '</div>',
                unsafe_allow_html=True)
    qbuzz['packet'] = qbuzz['packet'].astype(int)
    qbuzz = qbuzz[['player', 'team', 'value', 'buzz_position']]

    qbstreamlit.utils.hr()
    st.markdown(qbstreamlit.tables.df_to_kable(
        qbuzz.sort_values('buzz_position', ascending=True)),
            unsafe_allow_html=True)

else:
    qbonus = full_bonuses[full_bonuses['packet']
                          == pac][full_bonuses['bonus'] == tu]
    bonus_summary = qbonus.assign(
        part1_value=lambda x: x.part1_value/10, part2_value=lambda x: x.part2_value/10, part3_value=lambda x: x.part3_value/10
    ).groupby(['packet', 'bonus', 'category', 'subcategory', 'answers']).agg(
        {'part1_value': 'mean', 'part2_value': 'mean', 'part3_value': 'mean'}
    ).reset_index()
    qbonus = qbonus[['category', 'subcategory', 'team',
                     'part1_value', 'part2_value', 'part3_value']]

    st.markdown(packets[f"packets/packet{pac}.json"]['bonuses'][tu - 1]['leadin'],
                unsafe_allow_html=True)
    for i in range(0, 3):
        conv = [i for i in bonus_summary[f'part{i+1}_value']]

        st.markdown(f""" <p style='size:80%; color: #A3A3A3'>{round(conv[0]*100)}% |</p>
        [10{packets[f"packets/packet{pac}.json"]['bonuses'][tu - 1]['difficultyModifiers'][i]}] {packets[f"packets/packet{pac}.json"]['bonuses'][tu - 1]['parts'][i]}""",
                    unsafe_allow_html=True)
        st.markdown('ANSWER: ' + packets[f"packets/packet{pac}.json"]['bonuses'][tu - 1]['answers'][i],
                    unsafe_allow_html=True)

    qbstreamlit.utils.hr()
    st.markdown(qbstreamlit.tables.df_to_kable(qbonus),
            unsafe_allow_html=True)
