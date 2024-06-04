import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.matcher import Matcher
from string import punctuation
from collections import Counter
from heapq import nlargest
import re


class LanguageProcessor:

    def __init__(self, input):
        self.nlp = spacy.load('en_core_web_sm')
        self.input = input
        self.doc = self.nlp(input)

    def summarise(self):
        """ Source: https://medium.com/analytics-vidhya/text-summarization-using-spacy-ca4867c6b744 """
        stopwords = list(STOP_WORDS)
        keyword = []
        pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB']
        for token in self.doc:
            if (token.text in stopwords or token.text in punctuation):
                continue
            if (token.pos_ in pos_tag):
                keyword.append(token.text)
        freq_word = Counter(keyword)
        max_freq = Counter(keyword).most_common(1)[0][1]
        for word in freq_word.keys():
            freq_word[word] = (freq_word[word] / max_freq)
        freq_word.most_common(5)

        sent_strength = {}
        for sent in self.doc.sents:
            for word in sent:
                if word.text in freq_word.keys():
                    if sent in sent_strength.keys():
                        sent_strength[sent] += freq_word[word.text]
                    else:
                        sent_strength[sent] = freq_word[word.text]
        summarised_sentences = nlargest(3, sent_strength, key=sent_strength.get)
        final_sentences = [w.text for w in summarised_sentences]
        summary = ' '.join(final_sentences)
        return summary


class ArgumentProcessor(LanguageProcessor):

    def __init__(self, input):
        super().__init__(input)
        self.matcher = Matcher(self.nlp.vocab)

    def parse_initial_thoughts(self):
        patterns = {
            "CLAIM": [{"LOWER": "claim"}],
            "REASONING": [{"LOWER": "reasoning"}],
            "EVIDENCE": [{"LOWER": "evidence"}]
        }

        for label, pattern in patterns.items():
            self.matcher.add(label, [pattern])

        return self.extract_sections(patterns.keys())

    def parse_challenge(self):
        patterns = {
            "DISAGREEMENT": [{"LOWER": "disagreement"}],
            "COUNTER_REASONING": [{"LOWER": "counter", "OP": "?"}, {"LOWER": "reasoning"}],
            "ALTERNATIVE_VIEWPOINT": [{"LOWER": "alternative", "OP": "?"}, {"LOWER": "viewpoint"}]
        }

        for label, pattern in patterns.items():
            self.matcher.add(label, [pattern])

        return self.extract_sections(patterns.keys())

    def parse_response(self):
        patterns = {
            "DEFENSE": [{"LOWER": "defense"}],
            "REASONING": [{"LOWER": "strengthened", "OP": "?"}, {"LOWER": "reasoning"}],
            "JUSTIFICATION": [{"LOWER": "philosophical"}, {"LOWER": "justification"}]
        }

        for label, pattern in patterns.items():
            self.matcher.add(label, [pattern])

        return self.extract_sections(patterns.keys())

    def extract_sections(self, labels):
        matches = self.matcher(self.doc)
        matches = sorted(matches, key=lambda x: x[1])

        sections = {}
        for i, (match_id, start, next_start) in enumerate(matches):
            if i < len(matches) - 1:
                next_start = matches[i + 1][1]
            else:
                next_start = len(self.doc)

            label_end = next((tok for tok in self.doc[start:next_start] if tok.text == ":"), None)
            if label_end:
                start = label_end.i + 1

            span = self.doc[start:next_start]
            label = self.nlp.vocab.strings[match_id]
            sections[label.lower()] = span.text.strip()

        return {label.lower(): sections.get(label.lower(), "Section not found.") for label in labels}
