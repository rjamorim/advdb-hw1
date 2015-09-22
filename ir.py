import urllib2
import base64
import json
from sys import maxsize
from collections import defaultdict
from operator import itemgetter, attrgetter, methodcaller


def run_query(query):
    # Execute query
    query_url = urllib2.quote("'" + query + "'")
    bing_url = 'https://api.datamarket.azure.com/Bing/Search/Web?Query=' + query_url + '&$top=10&$format=json'
    # Provide your account key here
    account_key = 'hTvGEgXTQ8lDLYr8nnHocn7n9GSwF5antgnogEhNDTc'

    account_key_enc = base64.b64encode(account_key + ':' + account_key)
    headers = {'Authorization': 'Basic ' + account_key_enc}
    req = urllib2.Request(bing_url, headers=headers)
    response = urllib2.urlopen(req)
    content = response.read()
    # content contains the xml/json response from Bing.
    # print content
    tree = json.loads(content)
    return tree['d']['results']


def process_text(text):
    # Here we ignore punctuation marks
    for ch in [", ", ". ", "... ", " ...", " - ", "! ", "? ", ") ", " (", " & ", "/"]:
        if ch in text:
            text = text.replace(ch, " _IGNORE_ ")
    # Here we ignore common, irrelevant words
    # for ch in ["and", "or", "of", "is", "are", "from", "the", "but", "i", "a", "an"]:
    #    if ch in text:
    #        text = text.replace(ch, " _IGNORE_ ")
    return text


class Word(object):
    # Words...

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


class IRSystem(object):
    # Information Retrieval System

    def __init__(self):
        self.query_list = []
        self.results = []
        self.results_split = []
        self.all_words = defaultdict(Word)
        self.word_count = defaultdict(set)
        self.relevant = []
        self.n_relevant = 0
        self.top_words = []

    def get_query_results(self, query):
        self.query_list = query.split(' ')
        self.results = run_query(query)
        self.results_split = []
        self.all_words = defaultdict(Word)
        self.word_count = defaultdict(set)
        self.relevant = []
        self.n_relevant = 0
        self.top_words = []

        i = 0
        for entry in self.results:
            # Print the top10 results of the query
            i += 1
            print str(i) + ': ' + entry['Title']
            print '\t' + entry['Url']
            print '\t' + entry['Description'] + '\n'
            # Concatenate title and description for cleaning and processing
            text = (entry['Title'] + ' - ' + entry['Description']).lower()
            text = process_text(text)
            text_split = text.split(' ')
            self.results_split.append(text_split)
            # Determine in each text each word appears
            for word in text_split:
                if word not in self.query_list:  # and word != '': Empty strings appear due to repeated spaces...
                    self.all_words[word].word = word
                    self.all_words[word].mapping.add(i)
                    self.word_count[word].add(i)

    def get_precision(self):
        return self.n_relevant / 10.

    def assign_relevant_results(self):
        print "Please input the relevant results to your query in the line below, with space separated numbers:"
        relevantstr = raw_input('> ')
        relevantstr = relevantstr.lstrip()
        print relevantstr
        self.relevant = []
        i = 0
        number = relevantstr.split(' ', 1)
        while number[0]:
            if not number[0].isdigit():
                try:
                    number = number[1].split(' ', 1)
                except IndexError:
                    number[0] = 0
                continue
            if int(number[0]) > 10 or int(number[0]) < 1:
                try:
                    number = number[1].split(' ', 1)
                except IndexError:
                    number[0] = 0
                continue
            self.relevant.append(int(number[0]))
            i += 1
            try:
                number = number[1].split(' ', 1)
            except IndexError:
                number[0] = 0
        self.n_relevant = len(self.relevant)

        if i == 0:
            print "We are sorry you could not find relevant results for your query."
            print "Please try using more descriptive words."
            exit(0)

    def update_query(self):
        for word in self.all_words.keys():
            temp = self.all_words[word].mapping
            pos = len(temp.intersection(self.relevant))
            neg = len(temp.difference(self.relevant))
            score = (float(pos) / self.n_relevant) * ((10. - self.n_relevant - neg) / (10. - self.n_relevant))
            self.all_words[word].set_score(pos, neg, score)

        self.top_words = sorted(self.all_words.values(), key=attrgetter('score'), reverse=True)[:10]
        print self.top_words

        self.query_list.append(self.top_words[0].word)
        return " ".join(self.query_list)

        # location_att = get_distance(fragments, relevant, sorted_test[0], query_list)
        # print location_att[(sorted_test[0][0], query_list[0], 'dist')]
        # print location_att[(sorted_test[0][0], query_list[0], 'rel_pos')]


def get_distance(fragments, relevant, test_list, query_list):
    # get_distance

    location_att = defaultdict(float)
    word_count = defaultdict(int)

    for i in relevant:
        # Read the correspondent relevant fragment
        text = fragments[i - 1]
        print str(i) + ':'
        print text
        word_location = defaultdict(set)
        # Determine position of the words in the query
        for word in query_list:
            count = text.count(word)
            list_location = set()
            location = 0
            while count > 0:
                new_location = text[location:].index(word)
                location += new_location
                list_location.add(location)
                location += 1
                count -= 1
            word_location[word] = list_location
            print word, word_location[word]
        # Determine position of the words that could be added to the query
        for word in test_list:
            count0 = count = float(text.count(word))
            if count0 != 0:
                word_count[word] += count
                list_location = set()
                location = 0
                while count > 0:
                    new_location = text[location:].index(word)
                    location += new_location
                    list_location.add(location)
                    # Calculate distance and relative position to each word in the query
                    for word2 in query_list:
                        dist = maxsize
                        rel_pos = 0
                        for location2 in word_location[word2]:
                            if abs(location - location2) < dist:
                                dist = abs(location - location2)
                                rel_pos = (location - location2) / abs(location - location2)
                        location_att[(word, word2, 'dist')] += dist
                        location_att[(word, word2, 'rel_pos')] += rel_pos
                    location += 1
                    count -= 1
                word_location[word] = list_location
                print word, word_location[word]

    for entry in location_att.keys():
        location_att[entry] /= word_count[entry[0]]

    return location_att


irs = IRSystem()

current_query = raw_input('Please input the desired query: ').lower()
irs.get_query_results(current_query)
irs.assign_relevant_results()
precision = irs.get_precision()

while precision < 0.9:
    current_query = irs.update_query()
    irs.get_query_results(current_query)
    irs.assign_relevant_results()
    precision = irs.get_precision()

print 'fim!!'
