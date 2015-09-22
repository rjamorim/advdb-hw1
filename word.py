# Information Retrieval System
# Advanced Database Systems
# Pedro Ferro Freitas - pff2108
# Roberto Jose de Amorim - rja2139

class Word(object):
    # words...

    def __init__(self):
        self.word = ''
        self.mapping = set()
        self.pos = self.neg = self.score = 0

    def __repr__(self):
        return self.word.encode('ascii', 'ignore') + ' ' + str(self.pos) + ' ' + str(self.neg) + ' ' + str(self.score)

    def set_score(self, pos, neg, score):
        self.pos = pos
        self.neg = neg
        self.score = score
