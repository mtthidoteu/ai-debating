import streamlit as st
from src.agent import Agent
from src.database import *
from src.language_model import *
from src.prompts import *
from src.arguments import *
import datetime
import csv
import os

st.set_page_config(page_title="Debate Management", page_icon="🤖")
prompt = st.chat_input(placeholder="Question")


def random_question():
    prompt = [{"role": "system",
               "content": "You are an all knowning being with access to infinite creativity"},
              {"role": "user",
               "content": "Generate a random philosophical and specific question which is morally ambiguous"}, ]
    chat_model = ChatModel()
    response = chat_model.output_response(prompt)
    print(response)
    return response


def get_questions():
    with open('questions.csv', newline='') as f:
        reader = csv.reader(f)
        questions = [item for sublist in reader for item in sublist]
    return questions

placeholder = st.empty()
button_clicked = placeholder.button("Auto Run")
if button_clicked:
    prompt = random_question()


def run_debate(agents, prompt, debate):
    st.markdown(f'# {prompt}')
    st.markdown("## Initial Thoughts")
    for agent in agents:
        st.markdown(f"### {agent.school} {agent.icon}")
        message = st.chat_message(agent.icon)
        opponent = agents[0] if agent == agents[1] else agents[1]
        message.write_stream(agent.get_initial_thought(prompt, debate, opponent))

    st.markdown("## Challenges")
    for challenger, respondent in [(agents[0], agents[1]), (agents[1], agents[0])]:
        st.markdown(f"### {challenger.school} {challenger.icon} Challenges {respondent.school} {respondent.icon}")
        message = st.chat_message(challenger.icon)
        message.write_stream(challenger.challenge_opponent(respondent, debate))

        st.markdown(f"### {respondent.school} {respondent.icon}'s answer to {challenger.school} {challenger.icon}")
        message = st.chat_message(respondent.icon)
        message.write_stream(respondent.answer_challenge(challenger, debate))


if prompt:
    utiliarian_agent = Agent(school="Utilitarian", icon="📊", point_of_view=utilitarian_prompt)
    deontologian_agent = Agent(school="Deontologian", icon="❤️", point_of_view=deontologian_prompt)
    agents = [utiliarian_agent, deontologian_agent]

    if not isinstance(prompt, list):
        prompt = [prompt]
    for p in range(int(os.getenv("QUESTIONS_FROM_CSV_TO_RUN"))):
        p = prompt[p]
        already_ran = Debate.get_or_none(Debate.query == p)
        if already_ran:
            print("Already ran this debate")
        else:
            debate = Debate.create(agent1_id=utiliarian_agent.id, agent2_id=deontologian_agent.id, query=p,
                                   start_time=datetime.datetime.now())
            run_debate(agents, p, debate)
            winner = debate.get_winner()
            debate.log_scores_post_debate()
            st.markdown(f"## Winner: {winner.school} with a provisional score of {debate.get_average_scores()[winner]}")
