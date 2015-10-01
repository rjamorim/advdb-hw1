# Information Retrieval System
# Advanced Database Systems
# Pedro Ferro Freitas - pff2108
# Roberto Jose de Amorim - rja2139

import urllib2
import base64
import json
import math
from word import Word
from collections import defaultdict
from operator import attrgetter  # itemgetter, methodcaller
from sys import maxsize


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
        self.stopwords = defaultdict(int)
        self.load_stopwords()

    def get_query_results(self, query):
        # Read and process new query

        # 1. Read new query:
        self.query_list = query.split(' ')
        for keyword in self.query_list:
            self.stopwords[keyword] = 1

        # 2. Reinitialize properties for each iteration:
        self.results = run_query(query)
        self.results_split = []
        self.all_words = defaultdict(Word)
        self.word_count = defaultdict(set)
        self.relevant = []
        self.n_relevant = 0
        self.top_words = []

        # 3. Get query results:
        i = 1
        for entry in self.results:
            # Print results for the query
            print '\t' + str(i) + ': ' + entry['Title'].encode('utf-8')
            print '\t\t' + entry['Url'].encode('utf-8')
            print '\t\t' + entry['Description'].encode('utf-8') + '\n'
            # Concatenate title and description for processing
            text = (entry['Title'] + ' - ' + entry['Description']).lower()
            text = process_text(text).encode('ascii', 'ignore')
            text_split = text.split(' ')
            self.results_split.append(text_split)
            # Determine in each text each word appears
            j = 0
            for word in text_split:
                self.all_words[word].word = word
                self.all_words[word].mapping.add(i)
                self.all_words[word].position[i].add(j)
                self.word_count[word].add(i)
                j += 1
            i += 1

    def get_precision(self):
        return self.n_relevant / 10.

    def assign_relevant_results(self):
        print "Please input the relevant results to your query in the line below, with space separated numbers:"
        relevant_str = raw_input('> ')
        relevant_str = relevant_str.strip()
        self.relevant = set()
        i = 0
        number = relevant_str.split(' ', 1)
        while number[0]:
            # If the substring is not an integer, it gets ignored
            if not number[0].isdigit():
                try:
                    number = number[1].split(' ', 1)
                except IndexError:
                    number[0] = 0
                continue
            # If number is out of range, it gets ignored
            if int(number[0]) > 10 or int(number[0]) < 1:
                try:
                    number = number[1].split(' ', 1)
                except IndexError:
                    number[0] = 0
                continue
            self.relevant.add(int(number[0]))
            i += 1
            try:
                number = number[1].split(' ', 1)
            except IndexError:
                number[0] = 0

        print 'Relevant entries:', sorted(list(self.relevant)), '\n'
        self.n_relevant = len(self.relevant)

        if i == 0:
            print "We are sorry you could not find relevant results for your query."
            print "Please try using more descriptive words."
            exit(0)

    def update_query(self):
        # updates the query with the most relevant keyword found in descriptions
        for word in self.all_words.keys():
            temp = self.all_words[word].mapping
            pos = len(temp.intersection(self.relevant))
            neg = len(temp.difference(self.relevant))
            score = (float(pos) / self.n_relevant) * ((10. - self.n_relevant - neg) / (10. - self.n_relevant)) * (self.stopwords[word] == 0)
            self.all_words[word].set_score(pos, neg, score)
        self.top_words = sorted(self.all_words.values(), key=attrgetter('score'), reverse=True)[:25]
        print self.top_words

        self.get_distance(self.top_words)
        # updates the query with the most relevant keyword found in descriptions
        for word in self.all_words.keys():
            score = self.all_words[word].score
            score *= 0.75 + 0.25 * math.exp(-(self.all_words[word].avg_dist - 1) / 10)
            self.all_words[word].update_score(score)
        self.top_words = sorted(self.all_words.values(), key=attrgetter('score'), reverse=True)[:10]
        print self.top_words

        self.query_list.append(self.top_words[0].word)
        count = 0
        score = 1
        i = 1
        while count < 1 and score >= 0.70 * self.top_words[0].score:
            entry = self.top_words[i]
            score = entry.score
            if entry.rel_pos == self.top_words[0].rel_pos and entry.position.keys() == self.top_words[0].position.keys():
                self.query_list.append(entry.word)
                count += 1
            i += 1

        self.update_query_order()
        return " ".join(self.query_list)

    def update_query_order(self):
        # Precisa ser corrigida pra considerar somente o par de palavras mais proximo, mas ja funciona...
        # Pode ser usada pra melhorar a outra funcao de distancia...

        query_list_old = self.query_list[:]
        temp = defaultdict(int)
        query_position = defaultdict(int)
        for word in query_list_old:
            position = self.all_words[word].position
            for word2 in query_list_old:
                if word2 != word:
                    position2 = self.all_words[word2].position
                    for i in self.relevant:
                        if i in set(position.keys()).intersection(set(position2.keys())):
                            #print i, word, position[i], word2, position2[i]
                            for loc in position[i]:
                                dist = maxsize
                                rel_pos = 0
                                for loc2 in position2[i]:
                                    if abs(loc - loc2) < dist:
                                        dist = abs(loc - loc2)
                                        rel_pos = (loc - loc2) / abs(loc - loc2)
                                #print i, word, loc, word, dist, rel_pos
                                temp[(word, word2, 'dist')] += dist
                                temp[(word, word2, 'rel_pos')] += rel_pos
                                temp[(word, word2, 'count')] += 1
                    #print word, word2, temp[(word, word2, 'rel_pos')]
                    query_position[word] += temp[(word, word2, 'rel_pos')] >= 0
            #print word, query_position[word]
            self.query_list[query_position[word]] = word

    def get_distance(self, test_list):
        # determines the average distance to the words in the query
        location_att = defaultdict(float)
        word_count = defaultdict(int)

        for i in self.relevant:
            # Read the correspondent relevant split results (title + description)
            text = self.results_split[i - 1]
            #print str(i) + ': ', text
            word_location = defaultdict(set)
            # Determine position of the words in the query
            for word in self.query_list:
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
                self.all_words[word].position[i] = list_location
                # print word, word_location[word]

            # Determine position of the words that could be added to the query
            for entry in test_list:
                word = entry.word
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
                        for word2 in self.query_list:
                            dist = maxsize
                            rel_pos = 0
                            for location2 in word_location[word2]:
                                if abs(location - location2) < dist:
                                    dist = abs(location - location2)
                                    if dist > 0:
                                        rel_pos = (location - location2) / abs(location - location2)
                            location_att[(word, word2, 'dist')] += dist
                            location_att[(word, word2, 'rel_pos')] += rel_pos
                        location += 1
                        count -= 1
                    word_location[word] = list_location
                    self.all_words[word].position[i] = list_location
                    # print word, self.all_words[word], word_location[word], list_location

        for entry in test_list:
            word = entry.word
            self.all_words[word].avg_dist = 0
            for word2 in self.query_list:
                if word_count[word] != 0:
                    # print word, word2, location_att[(word, word2, 'dist')], word_count[word]
                    location_att[(word, word2, 'dist')] /= word_count[word]
                    location_att[(word, word2, 'rel_pos')] /= word_count[word]
                # print word, word2, location_att[(word, word2, 'dist')], location_att[(word, word2, 'rel_pos')]
                self.all_words[word].avg_dist += location_att[(word, word2, 'dist')]
                self.all_words[word].rel_pos += location_att[(word, word2, 'rel_pos')]
            self.all_words[word].avg_dist /= len(self.query_list)
            self.all_words[word].rel_pos /= len(self.query_list)

    def load_stopwords(self):
        try:
            with open("stopwords.txt") as f:
                for line in f:
                    self.stopwords[line.strip()] = 1
        except:
            print "Stopwords file not located. Stopwords won't be loaded and processed"


def run_query(query):
    # Execute query
    query_url = urllib2.quote("'" + query + "'")
    bing_url = 'https://api.datamarket.azure.com/Bing/Search/Web?Query=' + query_url + '&$top=10&$format=json'
    account_key = 'hTvGEgXTQ8lDLYr8nnHocn7n9GSwF5antgnogEhNDTc'

    account_key_enc = base64.b64encode(account_key + ':' + account_key)
    headers = {'Authorization': 'Basic ' + account_key_enc}
    req = urllib2.Request(bing_url, headers=headers)
    response = urllib2.urlopen(req)
    content = response.read()
    # content contains the xml/json response from Bing.
    tree = json.loads(content)
    return tree['d']['results']


def process_text(text):
    # Here we ignore punctuation marks
    for ch in [", ", ". ", "... ", " ...", " - ", "! ", "? ", ") ", " (", " & ", "/", ' "', '" ', ".", "'"]:
        if ch in text:
            text = text.replace(ch, " _IGNORE_ ")
    return text.strip()


# Instantiates the IRS (Information Retrieval System) class
irs = IRSystem()

current_query = raw_input('Please input the desired query: ').lower()
print '\nResults:'
irs.get_query_results(current_query)
irs.assign_relevant_results()
precision = irs.get_precision()

while precision < 0.9:
    current_query = irs.update_query()
    print 'Current query:', current_query
    print 'Results:'
    irs.get_query_results(current_query)
    irs.assign_relevant_results()
    precision = irs.get_precision()

print 'The procedure completed successfully!'
