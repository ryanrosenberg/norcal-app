import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import glob
import qbstreamlit.parser
import qbstreamlit.utils
import qbstreamlit.tables

# streamlit_app.py

import streamlit as st

qbstreamlit.utils.local_css("style.css")

def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
            st.session_state["role"] = 'admin'
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

st.session_state["role"] = 'admin'

with st.sidebar:
    st.selectbox(
        "Tournament",
        [path[5:] for path in glob.glob('qbjs/*')],
        key = "tournament",
        format_func=lambda x: x.capitalize()
    )
with st.spinner():
    qbstreamlit.utils.populate_db()

    if st.session_state.tournament == 'nasat':
        st.session_state['powers'] = False
    else:
        st.session_state['powers'] = True

    st.session_state['tournament_bonuses'] = False

    st.markdown('''<style>
        .buzz {display: inline; background-color: #e4e1e2;}
        .buzz-value {display: inline; background-color: #e4e1e2; font-size: 80%;}
        .buzz-value.correct-buzz-value {color: #555555;}
        .buzz-value.incorrect-buzz-value {color: #ff4b4b;}
        p {display: inline;}
        .row_heading.level0 {display:none}
        .stDataFrame {border:1px solid white}
        .data {font-size: 12px;}
        .blank {display:none}
        .ag-header-row {background-color: blue !important;}
        </style>''',
                    unsafe_allow_html=True)

    accent_color = "#ff4b4b"

    st.markdown("""<h1>Welcome!</h1><br><span class="material-symbols-outlined">
    keyboard_double_arrow_left
    </span><br>
    Check out one of the stats pages on the left.""",
    unsafe_allow_html=True)

    qbstreamlit.utils.hr()
    st.header('Glossary')
    gloss = {
        'Term': [
            '<b>ACC</b>', 
            '<b>BPA</b>', 
            '<b>Easy.Conv</b>, <b>Med.Conv</b>, <b>Hard.Conv</b>',
            '<b>Conv.</b>', 
            '<b>Neg.</b>', 
            '<b>Power.</b>', 
            '<b>PPB</b>', 
            '<b>PPG</b>'
            ],
        'Definition': [
            'Average correct celerity. The average % of a question remaining when a player/team buzzed correctly.',
            'Buzzpoint AUC. The area under the curve of a player/team\'s <a href = "https://hsquizbowl.org/forums/viewtopic.php?t=21962">buzzpoint curve</a>.', 
            'Conversion percentage for the bonus part with the given difficulty. Difficulty was assigned based on which part was converted most/least.',
            'Conversion percentage. The number of rooms where the tossup(s) were converted.',
            'Neg percentage. The number of rooms where the tossup(s) were negged.',
            'Power percentage. The number of rooms where the tossup(s) were powered.',
            'Points per bonus',
            'Points per game'
            ]
        }

    st.markdown(qbstreamlit.tables.df_to_kable(pd.DataFrame(gloss)),
    unsafe_allow_html=True)