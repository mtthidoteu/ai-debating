import streamlit as st
from src.database import *
from src.test.test import *
from src.modelling import *
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

try:
    db.connect()
    db.create_tables(
        [AgentStore, Debate, InitialThought, Challenge, Response, ScoreType, Scores, ScoreContext, HistoricalScores])
except:
    pass

st.set_page_config(
    page_title="Philosophy Debating ",
    page_icon="👋",
)

with st.spinner("Loading..."):
    st.write("# Current Argument Leaderboard")
    leaderboard = create_argument_leaderboard()
    st.dataframe(leaderboard, use_container_width=True)

    st.write("# Historical Debate Winrates")
    historical_winrates = get_historical_winrate()
    data = pd.DataFrame.from_dict(historical_winrates, orient='index').transpose()
    data.index += 1  # Adjust index to start from 1
    st.line_chart(data, use_container_width=True)


    # Evolution of raw response scores
    st.write("# Evolution of Raw Response Scores")
    response_scores = plot_raw_response_scores()
    st.line_chart(response_scores, x="debate_id", y="scaled_score", color="score_type", use_container_width=True)

    # Evolution of raw response scores
    st.write("# Evolution of Response Scores")
    response_scores = plot_response_scores()
    st.line_chart(response_scores, x="debate_id", y="score", color="score_type", use_container_width=True)

    #Correlation Matrix
    st.write("# Correlation Matrix")
    correlation = create_correlation_matrix()
    st.plotly_chart(correlation, use_container_width=True)