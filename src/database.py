from statistics import mean
from peewee import *
from scipy.stats import norm
import math
import datetime

db = SqliteDatabase('database.db')


class AgentStore(Model):
    school = CharField()
    icon = CharField()
    point_of_view = CharField()

    class Meta:
        database = db


class Debate(Model):
    agent1 = ForeignKeyField(AgentStore, backref='debates')
    agent2 = ForeignKeyField(AgentStore, backref='debates')
    query = CharField()
    start_time = DateTimeField()
    end_time = DateTimeField(null=True)
    winner = ForeignKeyField(AgentStore, backref='debates_won', null=True)

    def get_average_scores(self):
        def calculate_average(agent):
            scores_query = (Scores
                            .select(Scores, ScoreType)
                            .join(ScoreType)
                            .where((Scores.debate == self.id) & (Scores.agent == agent)))

            total_score = 0
            count = 0
            for score_entry in scores_query:
                standardized_score = score_entry.get_score()
                if standardized_score is not None:
                    total_score += standardized_score
                    count += 1

            if count == 0:
                return 0
            return total_score / count

        agent1_average = calculate_average(self.agent1)
        agent2_average = calculate_average(self.agent2)

        return {
            self.agent1: agent1_average,
            self.agent2: agent2_average
        }

    def get_winner(self):
        average = self.get_average_scores()
        if average[self.agent1] > average[self.agent2]:
            return self.agent1
        elif average[self.agent1] < average[self.agent2]:
            return self.agent2
        else:
            return None

    def log_scores_post_debate(self):
        for debate in Debate.select():
            for agent in [debate.agent1, debate.agent2]:
                scores_query = Scores.select().where(
                    (Scores.debate == debate) &
                    (Scores.agent == agent)
                )
                for score_entry in scores_query:
                    raw_score = score_entry.score
                    normalized_score = score_entry.get_score()
                    HistoricalScores.create(
                        agent=agent,
                        debate=debate,
                        score_type=score_entry.score_type,
                        score_context=score_entry.context,
                        raw_score=raw_score,
                        normalized_score=normalized_score,
                        timestamp=datetime.datetime.now(),
                        debate_number=self.id
                    )

    class Meta:
        database = db


class InitialThought(Model):
    agent = ForeignKeyField(AgentStore, backref='initial_thoughts')
    claim = TextField()
    reasoning = TextField()
    evidence = TextField()
    summary = TextField()
    debate = ForeignKeyField(Debate, backref='initial_thoughts')
    timestamp = DateTimeField()
    doc = TextField(null=True)
    vector = BlobField()

    def get_current_score(self):
        scores = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'initial_thought').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id)
        score_list = [score.get_score() for score in scores]
        return sum(score_list) / len(score_list)

    def get_current_coherence(self):
        coherence = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'initial_thought').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'coherence').id)[0]
        return coherence.get_score()

    def get_current_relevance(self):
        relevance = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'initial_thought').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'relevance').id)[0]
        return relevance.get_score()

    def get_current_clarity(self):
        clarity = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'initial_thought').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'clarity').id)[0]

        return clarity.get_score()

    def get_current_subjectivity(self):
        subjectivity = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'initial_thought').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'subjectivity').id)[0]

        return subjectivity.get_score()


    class Meta:
        database = db


class Challenge(Model):
    agent = ForeignKeyField(AgentStore, backref='challenges')
    disagreement = TextField()
    counter_reasoning = TextField()
    alternative_viewpoint = TextField()
    summary = TextField()
    debate = ForeignKeyField(Debate, backref='challenges')
    timestamp = DateTimeField()
    doc = TextField(null=True)

    class Meta:
        database = db


class Response(Model):
    agent = ForeignKeyField(AgentStore, backref='responses')
    defense = TextField()
    strengthened_reasoning = TextField()
    philosophical_justification = TextField()
    summary = TextField()
    debate = ForeignKeyField(Debate, backref='responses')
    timestamp = DateTimeField()
    doc = TextField(null=True)
    vector = BlobField()

    def get_current_score(self):
        scores = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'response').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id)
        score_list = [score.get_score() for score in scores]
        return sum(score_list) / len(score_list)

    def get_current_coherence(self):
        coherence = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'response').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'coherence').id)[0]
        return coherence.get_score()

    def get_current_relevance(self):
        relevance = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'response').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'relevance').id)[0]
        return relevance.get_score()

    def get_current_clarity(self):
        clarity = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'response').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'clarity').id)[0]
        return clarity.get_score()

    def get_current_subjectivity(self):
        subjectivity = Scores.select().where(Scores.context_id == ScoreContext.get(ScoreContext.name == 'response').id,
                                       Scores.debate == self.debate.id, Scores.agent == self.agent.id, Scores.score_type == ScoreType.get(ScoreType.name == 'subjectivity').id)[0]
        return subjectivity.get_score()

    class Meta:
        database = db


class ScoreType(Model):
    name = CharField()

    class Meta:
        database = db


class ScoreContext(Model):
    name = CharField()

    class Meta:
        database = db


class Scores(Model):
    agent = ForeignKeyField(AgentStore, backref='scores')
    score = FloatField()
    debate = ForeignKeyField(Debate, backref='scores')
    timestamp = DateTimeField()
    score_type = ForeignKeyField(ScoreType, backref='scores')
    context = ForeignKeyField(ScoreContext, backref='scores')

    def get_score(self):
        scores_with_type = Scores.select().where(Scores.score_type == self.score_type)
        scores_list = [score.score for score in scores_with_type]

        if not scores_list:
            return None

        mean = sum(scores_list) / len(scores_list)

        stddev = math.sqrt(sum((x - mean) ** 2 for x in scores_list) / len(scores_list))

        if stddev == 0:
            return 100

        # Calculate z-score
        z_score = (self.score - mean) / stddev

        # Convert z-score to percentile using the norm.cdf function from scipy.stats
        percentile = norm.cdf(z_score) * 100
        return percentile

    def get_complete_score(self):
        all_scores = Scores.select().where(Scores.debate == self.debate, Scores.agent == self.agent,
                                           Scores.context == self.context)
        return mean([score.get_score() for score in all_scores])

    class Meta:
        database = db


class HistoricalScores(Model):
    agent = ForeignKeyField(AgentStore, backref='historical_scores')
    debate = ForeignKeyField(Debate, backref='historical_scores')
    score_type = ForeignKeyField(ScoreType, backref='historical_scores')
    score_context = ForeignKeyField(ScoreContext, backref='historical_scores')
    raw_score = FloatField()
    normalized_score = FloatField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    debate_number = IntegerField()


    class Meta:
        database = db


"""
class RelationshipType(Model):
    name = CharField()

    class Meta:
        database = db


class Relationship(Model):
    source = ForeignKeyField(Contribution, backref='relationships')
    target = ForeignKeyField(Contribution, backref='relationships')
    type = ForeignKeyField(RelationshipType, backref='relationships')

    class Meta:
        database = db
"""
