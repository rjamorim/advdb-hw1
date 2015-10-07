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
from operator import attrgetter
from sys import maxsize, argv


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
        # The words in the query are considered stopwords so they don't get reused on queries
        for keyword in self.query_list:
            self.stopwords[keyword] = 1

        # 2. Reinitialize properties for each iteration:
        self.results = run_query(query)
        if len(self.results) < 10:
            print "The desired query returned less than 10 results."
            print "Please try a more general query."
            exit(0)

        self.results_split = []
        self.all_words = defaultdict(Word)
        self.word_count = defaultdict(set)
        self.relevant = []
        self.n_relevant = 0
        self.top_words = []

        # 3. Process query results:
        i = 1
        for entry in self.results:
            # Print results for the query
            print '\t' + str(i) + ':\tURL: ' + entry['Url'].encode('utf-8')
            print '\t\t' + 'Title: ' + entry['Title'].encode('utf-8')
            print '\t\t' + 'Summary: ' + entry['Description'].encode('utf-8') + '\n'
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
        # Updates the query with the most relevant keyword found in descriptions and titles
        for word in self.all_words.keys():
            temp = self.all_words[word].mapping
            pos = len(temp.intersection(self.relevant))
            neg = len(temp.difference(self.relevant))
            score = (float(pos) / self.n_relevant) * ((10. - self.n_relevant - neg) / (10. - self.n_relevant)) * (self.stopwords[word] == 0)
            self.all_words[word].set_score(pos, neg, score)
        self.top_words = sorted(self.all_words.values(), key=attrgetter('score'), reverse=True)[:25]

        # Includes distance in score calculation
        self.get_distance(self.top_words)
        for word in self.all_words.keys():
            score = self.all_words[word].score
            score *= 0.75 + 0.25 * math.exp(-(self.all_words[word].avg_dist - 1) / 10)
            self.all_words[word].update_score(score)
        self.top_words = sorted(self.all_words.values(), key=attrgetter('score'), reverse=True)[:10]

        # Always adds the word with the highest score to the query
        self.query_list.append(self.top_words[0].word)
        count = 0
        score = 1
        i = 1
        # And if another word has a score of at least 70% the highest score, that words gets added too
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
        query_list_old = self.query_list[:]
        temp = defaultdict(int)
        query_position = defaultdict(int)
        # We iterate through the words in the query, twice
        for word in query_list_old:
            position = self.all_words[word].position
            for word2 in query_list_old:
                # If the words are different...
                if word2 != word:
                    position2 = self.all_words[word2].position
                    # ...we recalculate the average distance and the relative position
                    for i in self.relevant:
                        if i in set(position.keys()).intersection(set(position2.keys())):
                            for loc in position[i]:
                                dist = maxsize
                                rel_pos = 0
                                for loc2 in position2[i]:
                                    # If the distances are smaller than a threshold, they get updated
                                    if abs(loc - loc2) < dist:
                                        dist = abs(loc - loc2)
                                        rel_pos = (loc - loc2) / abs(loc - loc2)
                                temp[(word, word2, 'dist')] += dist
                                temp[(word, word2, 'rel_pos')] += rel_pos
                                temp[(word, word2, 'count')] += 1
                    query_position[word] += temp[(word, word2, 'rel_pos')] >= 0
            self.query_list[query_position[word]] = word

    def get_distance(self, test_list):
        # Determines the average distance to the words in the query
        location_att = defaultdict(float)
        word_count = defaultdict(int)

        for i in self.relevant:
            # Read the correspondent relevant split results (title + description)
            text = self.results_split[i - 1]
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

        for entry in test_list:
            word = entry.word
            self.all_words[word].avg_dist = 0
            for word2 in self.query_list:
                if word_count[word] != 0:
                    location_att[(word, word2, 'dist')] /= word_count[word]
                    location_att[(word, word2, 'rel_pos')] /= word_count[word]
                self.all_words[word].avg_dist += location_att[(word, word2, 'dist')]
                self.all_words[word].rel_pos += location_att[(word, word2, 'rel_pos')]
            self.all_words[word].avg_dist /= len(self.query_list)
            self.all_words[word].rel_pos /= len(self.query_list)

    def load_stopwords(self):
        # Loads stopwords from external file
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
    # account_key = 'hTvGEgXTQ8lDLYr8nnHocn7n9GSwF5antgnogEhNDTc'
    account_key = bing

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
    for ch in [", ", ". ", "... ", " ...", " - ", "! ", "? ", ") ", " (", " & ", "/", ': ', ' "', '" ', ".", "'"]:
        if ch in text:
            text = text.replace(ch, " _IGNORE_ ")
    return text.strip()

bing = argv[1]
prec = argv[2]
initial_query = argv[3]

# Instantiates the IRS (Information Retrieval System) class
irs = IRSystem()

current_query = initial_query
print 'Current query:', current_query
print '\nResults:'
irs.get_query_results(current_query)
irs.assign_relevant_results()
precision = irs.get_precision()

while precision < float(prec):
    current_query = irs.update_query()
    print 'Current query:', current_query
    print 'Results:'
    irs.get_query_results(current_query)
    irs.assign_relevant_results()
    precision = irs.get_precision()

print 'The procedure completed successfully!'
