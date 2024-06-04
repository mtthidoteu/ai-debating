from src.language_model import *
from src.prompts import *
from src.arguments import *
from src.database import *
import datetime
from src.referee import *



class Agent:
    def __init__(self, school: str, icon: str, point_of_view: str):
        self.school = school
        self.model = ChatModel()
        self.point_of_view = point_of_view
        self.icon = icon
        self.initial_thoughts =  ""
        agent, created = AgentStore.get_or_create(school=school, icon=icon, point_of_view=point_of_view)
        self.id = agent.id


    def generate_point_of_view(self, school):
        ideology = school
        metaprompt = f"Generate a detailed prompt for a debate agent that will embody the ideology of {ideology}. The prompt should guide the agent to argue consistently with the core principles and typical reasoning styles of this ideology. Include key concepts, ethical priorities, and typical argumentative approaches associated with {ideology}. "
        return self.model.generate_response(metaprompt)

    def get_initial_thought(self, query: str, debate: Debate, opponent: AgentStore):
        self.query = query
        collected_messages = []
        prompt = get_initial_thought_prompt(self, query, opponent, debate)
        yield self.model.generate_response(prompt)
        full_response = self.model.latest_response
        self.initial_thoughts = full_response
        processor = ArgumentProcessor(full_response)
        initial_thoughts = processor.parse_initial_thoughts()
        cleaned_input = f"{initial_thoughts['claim']} {initial_thoughts['reasoning']} {initial_thoughts['evidence']}"
        processor = LanguageProcessor(cleaned_input)
        summary = processor.summarise()
        InitialThought.create(agent=self.id, claim=initial_thoughts['claim'], reasoning=initial_thoughts['reasoning'], evidence=initial_thoughts['evidence'], summary=summary,
                              debate=debate,
                              timestamp=datetime.datetime.now(), vector=processor.doc.vector.reshape(1, -1).tobytes())
        referee = Referee(text=cleaned_input, query=query, agent=self, debate=debate, context="initial_thought")
        referee.score_argument()



    def challenge_opponent(self, opponent, debate):
        prompt = challenge_opponent_prompt(self, opponent)
        yield self.model.generate_response(prompt)
        full_response = self.model.latest_response
        processor = ArgumentProcessor(full_response)
        challenge = processor.parse_challenge()
        processor = LanguageProcessor(f"{challenge['disagreement']} {challenge['counter_reasoning']} {challenge['alternative_viewpoint']}")
        summary = processor.summarise()
        Challenge.create(agent=self.id, disagreement=challenge['disagreement'], counter_reasoning=challenge['counter_reasoning'],
                         alternative_viewpoint=challenge['alternative_viewpoint'], summary=summary, debate=debate,
                         timestamp=datetime.datetime.now())

    def answer_challenge(self, opponent, debate):
        prompt = answer_challenge_prompt(self, opponent, debate)
        yield self.model.generate_response(prompt)
        full_response = self.model.latest_response
        processor = ArgumentProcessor(full_response)
        response = processor.parse_response()
        cleaned_input = f"{response['defense']} {response['reasoning']} {response['justification']}"
        processor = LanguageProcessor(cleaned_input)
        summary = processor.summarise()
        Response.create(agent=self.id, defense=response['defense'], strengthened_reasoning=response['reasoning'],
                        philosophical_justification=response['justification'], summary=summary, debate=debate,
                        timestamp=datetime.datetime.now(),
                        vector=processor.doc.vector.reshape(1, -1).tobytes())
        referee = Referee(text=cleaned_input, query=self.query, agent=self, debate=debate, context="response")
        scores = referee.score_argument()
        for score in scores:
            print(score.score_type.name, score.get_score())


