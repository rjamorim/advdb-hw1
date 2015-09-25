# Information Retrieval System
# Advanced Database Systems
# Pedro Ferro Freitas - pff2108
# Roberto Jose de Amorim - rja2139

from sys import maxsize
from collections import defaultdict

class Word(object):
    # words...

    def __init__(self):
        self.word = ''
        self.mapping = set()
        self.pos = self.neg = self.score = 0
        self.avg_dist = maxsize
        self.rel_pos = 0
        self.position = defaultdict(set)

    def __repr__(self):  # .encode('ascii', 'ignore')
        return self.word + ' ' + str(self.pos) + ' ' + str(self.neg) + ' ' + str(self.score) + ' ' + str(self.avg_dist) + ' ' + str(self.rel_pos) + ' ' + str(self.position)

    # defines the scores for each words found in description fields
    def set_score(self, pos, neg, score):
        self.pos = pos
        self.neg = neg
        self.score = score

    def get_score (self):
        return self.score

    def update_score (self, score):
        self.score = score
