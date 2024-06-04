from collections import defaultdict
from playhouse.shortcuts import model_to_dict

from src.database import *
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import zscore
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import pearsonr
import plotly.figure_factory as ff

import pandas as pd


def fetch_winner_counts():
    debates = Debate.select()
    winner_counts = {}
    for debate in debates:
        winner = debate.get_winner()
        if winner:
            if winner.school in winner_counts:
                winner_counts[winner.school] += 1
            else:
                winner_counts[winner.school] = 1
    return winner_counts


def create_pie_chart(winner_counts):
    data = [{'winner': k, 'total_wins': v} for k, v in winner_counts.items()]
    fig = px.pie(data, values='total_wins', names='winner', title='Proportion of Debate Wins')
    return fig


def create_argument_leaderboard():
    leaderboard = []
    initial_thoughts = InitialThought.select()
    for thought in initial_thoughts:
        original_score_query = HistoricalScores.select(HistoricalScores.normalized_score).where(
            HistoricalScores.debate_number == thought.debate.id, HistoricalScores.debate == thought.debate.id,
            HistoricalScores.agent == thought.agent,
            HistoricalScores.score_context == ScoreContext.get(ScoreContext.name == 'initial_thought'))
        original_score = mean([score.normalized_score for score in original_score_query])
        leaderboard.append({
            'Argument': thought,
            'Score': thought.get_current_score(),
            'Original Score': original_score,
            'Agent': thought.agent.school,
            'Type': 'Initial Thought',
            'Query': thought.debate.query,
            'Content (Summary)': thought.summary,
            'Coherence': thought.get_current_coherence(),
            'Relevance': thought.get_current_relevance(),
            'Clarity': thought.get_current_clarity(),
            'Objectivity': thought.get_current_subjectivity()
        })

    responses = Response.select()
    for response in responses:
        original_score_query = HistoricalScores.select(HistoricalScores.normalized_score).where(
            HistoricalScores.debate_number == response.debate.id, HistoricalScores.debate == response.debate.id,
            HistoricalScores.agent == response.agent,
            HistoricalScores.score_context == ScoreContext.get(ScoreContext.name == 'response'))
        original_score = mean([score.normalized_score for score in original_score_query])
        leaderboard.append({
            'Argument': response,
            'Score': response.get_current_score(),
            'Original Score': original_score,
            'Agent': response.agent.school,
            'Type': 'Response',
            'Query': response.debate.query,
            'Content (Summary)': response.summary,
            'Coherence': response.get_current_coherence(),
            'Relevance': response.get_current_relevance(),
            'Clarity': response.get_current_clarity(),
            'Objectivity': response.get_current_subjectivity()
        })
    df = pd.DataFrame(leaderboard)
    df = df.sort_values(by='Score', ascending=False)
    return df


def get_historical_winrate():
    cumulative_wins = defaultdict(int)
    debate_counts = defaultdict(int)
    historical_winrates = defaultdict(list)
    agent_ideologies = {}

    agent_info = {agent.id: agent.school for agent in AgentStore.select()}

    max_debate_number = HistoricalScores.select(fn.MAX(HistoricalScores.debate_number)).scalar()

    for debate_num in range(1, max_debate_number + 1):
        debate_scores = HistoricalScores.select().where(HistoricalScores.debate_number == debate_num)

        scores_by_debate_agent = defaultdict(lambda: defaultdict(list))

        for score in debate_scores:
            scores_by_debate_agent[score.debate_id][score.agent_id].append(score.normalized_score)
            if score.agent_id not in agent_ideologies:
                agent_ideologies[score.agent_id] = agent_info[score.agent_id]

        for debate_id, scores_by_agent in scores_by_debate_agent.items():
            avg_scores = {agent_id: sum(agent_scores) / len(agent_scores) for agent_id, agent_scores in
                          scores_by_agent.items()}
            winner_agent_id = max(avg_scores, key=avg_scores.get)
            cumulative_wins[winner_agent_id] += 1
            agents_in_debate = scores_by_agent.keys()
            for agent_id in agents_in_debate:
                debate_counts[agent_id] += 1

        for agent_id in debate_counts:
            if debate_counts[agent_id] > 0:
                win_rate = cumulative_wins[agent_id] / debate_counts[agent_id]
                historical_winrates[agent_ideologies[agent_id]].append(win_rate)

    return historical_winrates


def plot_raw_response_scores():
    query = Scores.select().where(Scores.context == ScoreContext.get(ScoreContext.name == 'response'))

    data = []
    for score in query:
        data.append({
            'debate_id': score.debate.id,
            'score_type': score.score_type.name,
            'raw_score': score.score
        })
    df = pd.DataFrame(data)

    scaler = MinMaxScaler()

    df['scaled_score'] = df.groupby('score_type')['raw_score'].transform(
        lambda x: scaler.fit_transform(x.values.reshape(-1, 1)).flatten())
    return df


def plot_response_scores():
    query = Scores.select().where(Scores.context == ScoreContext.get(ScoreContext.name == 'response'))

    data = []
    for score in query:
        data.append({
            'debate_id': score.debate.id,
            'score_type': score.score_type.name,
            'score': score.get_score()
        })
    df = pd.DataFrame(data)
    return df


def create_correlation_matrix():
    query = Scores.select()

    data = []
    for score in query:
        data.append({
            'debate_id': score.debate.id,
            'score_type': score.score_type.name,
            'score': score.get_score()
        })
    df = pd.DataFrame(data)

    df_grouped = df.groupby(['debate_id', 'score_type']).mean().reset_index()

    df_pivot = df_grouped.pivot(index='debate_id', columns='score_type', values='score')
    corr_matrix = df_pivot.corr()

    fig = px.imshow(corr_matrix, labels=dict(x="Score Type", y="Score Type", color="Correlation Coefficient"),
                    x=corr_matrix.columns, y=corr_matrix.columns, color_continuous_scale='Viridis')

    return fig

