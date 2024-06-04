from src.database import *

utilitarian_prompt = """As a debate agent embodying Utilitarianism, your primary focus should be on maximizing overall happiness and minimizing suffering. Emphasize the importance of outcomes and use cost-benefit analyses to argue for solutions that promote the greatest good for the greatest number. You should argue impartially, treating the well-being of all individuals equally, and always consider the long-term consequences of actions. Be ready to counter duty-based and virtue ethics by showing instances where these approaches might fail to prevent harm or overlook broader beneficial outcomes."""

deontologian_prompt = """As a debate agent upholding Deontological ethics, your main objective is to emphasize the importance of moral duties and rules regardless of the consequences. Stress the intrinsic rightness or wrongness of actions, adhering strictly to ethical principles and universal laws. You should argue that moral integrity is non-negotiable and advocate for actions that are consistent with moral duties, such as honesty and justice. Be prepared to challenge utilitarian and consequentialist arguments by illustrating situations where focusing solely on outcomes could lead to morally questionable actions. Uphold the concept that some actions are inherently right or wrong, independent of their effects on overall happiness."""


def get_initial_thought_prompt(agent, query, opponent, debate):
    relevance_score = 0
    coherence_score = 0
    clarity_score = 0
    subjectivity_score = 0
    try:
        previous_debate = Debate.get(id=debate.id - 1)
        previous_debate_scores = Scores.select().where(Scores.debate == previous_debate.id, Scores.agent == agent.id)
        for score in previous_debate_scores:
            previous_relevance = previous_debate_scores.select().where(Scores.score_type == ScoreType.get(name="relevance"))
            relevance_score = mean([score.get_score() for score in previous_relevance])
            previous_coherence = previous_debate_scores.select().where(Scores.score_type == ScoreType.get(name="coherence"))
            coherence_score = mean([score.get_score() for score in previous_coherence])
            previous_clarity = previous_debate_scores.select().where(Scores.score_type == ScoreType.get(name="clarity"))
            clarity_score = mean([score.get_score() for score in previous_clarity])
            previous_subjectivity = previous_debate_scores.select().where(
                Scores.score_type == ScoreType.get(name="subjectivity"))
            subjectivity_score = mean([score.get_score() for score in previous_subjectivity])
    except:
        pass

    initial_thoughts = [
        {"role": "system",
         "content": "Generate one response strictly adhering to your ideological perspective. Structure your response clearly into distinct sections: Claim, Reasoning, and Evidence. Each section should be explicitly labeled and contain concise, complete sentences."},
        {"role": "user",
         "content": f"You are debate agent. Your ideology is {agent.school}, known for its emphasis on {agent.point_of_view}. Last debate you should know you had a relevance to the question score of {relevance_score}, a coherence score of {coherence_score}, a clarity score of {clarity_score} and a objectivity score of {subjectivity_score}. The question for you to address is: '{query}'"},
        {"role": "assistant",
         "content": "Claim: [Insert your main claim here]\n\nReasoning: [Provide the logical basis supporting your claim]\n\nEvidence: [Cite specific evidence to back up your reasoning]\n\nPlease ensure each part is clearly delineated and formulated to facilitate easy parsing and analysis."}
    ]
    return initial_thoughts


def challenge_opponent_prompt(agent, opponent):
    challenge_prompt = [
        {"role": "system",
         "content": "Construct a 150-word rebuttal that challenges the opposing ideology based on your own ideological perspective. Format your rebuttal into sections: Disagreement, Counter-Reasoning, and Alternative Viewpoint. Label each section clearly."},
        {"role": "user",
         "content": f"Your ideology is {agent.school}. You are to challenge an argument by {opponent.school} which states: '{opponent.initial_thoughts}'."},
        {"role": "assistant",
         "content": "Disagreement: [Specify the point you disagree with]\n\nCounter Reasoning: [Explain why you disagree, based on your ideology]\n\nAlternative Viewpoint: [Propose an alternative that aligns with your ideological beliefs]\n\nPlease format your response with clear labels for each section."}
    ]
    return challenge_prompt


def answer_challenge_prompt(agent, opponent, debate):
    summary_initial_thoughts_agent = InitialThought.get(agent=agent.id, debate=debate).summary
    summary_initial_thoughts_opponent = InitialThought.get(agent=opponent.id, debate=debate).summary
    challenge = Challenge.get(agent=opponent.id, debate=debate).summary
    for score in Scores.select().where(Scores.debate == debate, Scores.agent == agent.id):
        if score.score_type.name == "relevance":
            relevance_score = score.score
        elif score.score_type.name == "coherence":
            coherence_score = score.score
        elif score.score_type.name == "clarity":
            clarity_score = score.score
        elif score.score_type.name == 'subjectivity':
            subjectivity_score = score.score

        initial_thought = InitialThought.get(agent=agent.id, debate=debate)

    response_prompt = [
        {"role": "system",
         "content": "Your initial thoughts were: {initial_thought.summary}, they were judged to have a relevance to the question of {relevance_score}%, a coherence with your previous answers of {coherence_score}%, a word clarity of {clarity_score}% and a subjectivity score of {subjectivity_score}%. Respond to the challenge posed by your opponent by structuring your response into: Defense, Strengthened Reasoning, and Philosophical Justification. Clearly label each section."},
        {"role": "user",
         "content": f"Your ideology is {agent.school}. Address this challenge from {opponent.school}, bearing in mind the feedback from your initial thoughts: '{challenge}'."},
        {"role": "assistant",
         "content": f"Defense: [Defend your initial claim]\n\nStrengthened Reasoning: [Enhance your initial reasoning in light of the challenge]\n\nPhilosophical Justification: [Cite philosophical principles that justify your stance]\n\nEnsure each section is well-defined and labeled for thorough analysis."}
    ]
    return response_prompt
