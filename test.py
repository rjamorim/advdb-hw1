import urllib2
import base64
import json
from sys import maxsize
from collections import defaultdict


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


def relevance():
    print "Please input the relevant results to your query in the line below, with space separated numbers:"
    relevantstr = raw_input('> ')
    relevantstr = relevantstr.lstrip()
    print relevantstr
    relevant = []
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
        relevant.append(int(number[0]))
        i += 1
        try:
            number = number[1].split(' ', 1)
        except IndexError:
            number[0] = 0

    if i == 0:
        print "We are sorry you could not find relevant results for your query. Please try using more descriptive words"
        exit(0)

    return set(relevant)


def run_query(query):
    query_list = query.split(' ')
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
    results = tree['d']['results']

    i = 0
    fragments = []
    word_count = defaultdict(set)
    for entry in results:
        i += 1
        print str(i) + ': ' + entry['Title']
        print '\t' + entry['Url']
        print '\t' + entry['Description'] + '\n'
        text = (entry['Title'] + ' - ' + entry['Description']).lower()
        # Here we ignore punctuation marks
        for ch in [", ", ". ", "... ", " ...", " - ", "! ", "? ", ") ", " (", " & ", "/"]:
            if ch in text:
                text = text.replace(ch, " _IGNORE_ ")
        # Here we ignore common, irrelevant words
        # for ch in ["and", "or", "of", "is", "are", "from", "the", "but", "i", "a", "an"]:
        #    if ch in text:
        #        text = text.replace(ch, " _IGNORE_ ")
        text_split = text.split(' ')
        for word in text_split:
            if word not in query_list:  # and word != '': Empty strings appear due to repeated spaces...
                word_count[word].add(i)
        fragments.append(text_split)

    relevant = relevance()
    n_relevant = len(relevant)

    test = []
    for word in word_count.keys():
        pos = len(word_count[word].intersection(relevant))
        neg = len(word_count[word].difference(relevant))
        score = (float(pos) / n_relevant) * ((10. - n_relevant - neg) / (10. - n_relevant))
        test.append((word, pos, neg, score))

    sorted_test = sorted(test, key=lambda word_att: word_att[3], reverse=True)[:10]
    print sorted_test

    location_att = get_distance(fragments, relevant, sorted_test[0], query_list)
    print location_att[(sorted_test[0][0], query_list[0], 'dist')]
    print location_att[(sorted_test[0][0], query_list[0], 'rel_pos')]

    return fragments, sorted_test


initial_query = raw_input('Please input the desired query: ').lower()
run_query(initial_query)
