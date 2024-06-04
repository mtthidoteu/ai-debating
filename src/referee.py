from pprint import pprint
import datetime
from textblob import TextBlob
import spacy
from src.arguments import *
import syllapy
from scipy.spatial.distance import cosine
from collections import defaultdict
from src.database import *
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.arguments import *


class ScoreCalculator:
    def __init__(self, text, query, agent):
        self.agent = agent.id
        self.text = text
        self.query = query
        self.nlp = spacy.load('en_core_web_sm')
        self.doc = self.nlp(text)
        self.text_vector = self.doc.vector
        self.query_doc = self.nlp(query)

    def analyse_subjectivity(self):
        analysis = TextBlob(self.text)
        sentiment_score = analysis.sentiment.subjectivity
        #Flip the score so that higher values are better
        sentiment_score = 1 - sentiment_score
        return sentiment_score

    def analyse_clarity(self):
        total_sentences = len(list(self.doc.sents))
        total_words = len([token for token in self.doc if token.is_alpha])
        total_syllables = sum(syllapy.count(word.text) for word in self.doc if word.is_alpha)
        average_words_per_sentence = total_words / total_sentences
        average_syllables_per_word = total_syllables / total_words
        score = 206.835 - 1.015 * average_words_per_sentence - 84.6 * average_syllables_per_word  # Flesch Reading Ease Score Formula
        return score

    def analyse_relevance(self):
        similarity = cosine(self.doc.vector, self.query_doc.vector)
        return similarity

    def analyse_coherence(self):
        vector_blobs_thoughts = InitialThought.select().where(InitialThought.agent == self.agent)
        vectors_thoughts = [np.frombuffer(blob.vector, dtype=np.float32) for blob in vector_blobs_thoughts if
                            blob.vector is not None]

        vector_blobs_responses = Response.select().where(Response.agent == self.agent)
        vectors_responses = [np.frombuffer(blob.vector, dtype=np.float32) for blob in vector_blobs_responses if
                             blob.vector is not None]

        vectors = vectors_thoughts + vectors_responses

        similarity_scores = cosine_similarity(self.text_vector.reshape(1, -1), np.array(vectors))

        average_similarity = np.mean(similarity_scores)

        return average_similarity




class Referee:

    def __init__(self, text: str, query: str, agent, debate: Debate, context):
        self.text = text
        self.query = query
        self.agent = agent
        self.debate = debate
        self.context = context

    def score_argument(self):
        calc = ScoreCalculator(self.text, self.query, self.agent)
        score_types = ['subjectivity', 'clarity', 'relevance', 'coherence']
        scores = []

        for score_type in score_types:
            score_value = getattr(calc, f'analyse_{score_type}')()
            score_context_instance, created = ScoreContext.get_or_create(name=self.context)
            score_type_instance, created = ScoreType.get_or_create(name=score_type)
            score = Scores.create(
                agent=self.agent.id,
                score=score_value,
                debate=self.debate,
                timestamp=datetime.datetime.now(),
                score_type=score_type_instance,
                context=score_context_instance
            )
            scores.append(score)
        return scores






