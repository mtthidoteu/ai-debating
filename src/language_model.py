from openai import OpenAI
import asyncio
import os

class ChatModel:

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = 'gpt-3.5-turbo'
        self.latest_response = None,

    def generate_response(self, prompt: iter):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
            stream=True,

        )
        collected_messages = []

        for chunk in response:
            if chunk.choices[0].delta.content:
                collected_messages.append(chunk.choices[0].delta.content)
            yield chunk
        self.latest_response = ''.join(collected_messages)


    def output_response(self, prompt: iter):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
            stream=False)
        response = response.choices[0].message.content
        return response
