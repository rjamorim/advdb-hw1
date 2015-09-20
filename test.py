import urllib2
import base64
import json

def relevance():
    print "Please input the relevant results to your query in the line below, with space saparated numbers:"
    relevantstr = raw_input('> ')
    relevantstr = relevantstr.lstrip()
    print relevantstr
    relevant = []
    i = 0
    number = relevantstr.split(' ', 1)
    while number[0]:
        i += 1
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
        try:
            number = number[1].split(' ', 1)
        except IndexError:
            number[0] = 0

    return relevant

def runQuery(query):
    query = urllib2.quote("'" + query + "'",':/')
    bingUrl = 'https://api.datamarket.azure.com/Bing/Search/Web?Query=' + query + '&$top=10&$format=json' #&format=Atom'
    #bingUrl = 'https://api.datamarket.azure.com/Bing/Search/v1/Web?Query=%27gates%27&Options=%27EnableHighlighting%27&WebSearchOptions=%27DisableQueryAlterations%27&Market=%27ar-XA%27&Adult=%27Off%27&Latitude=0&Longitude=10&WebFileType=%27HTML%27'
    #Provide your account key here
    accountKey = 'hTvGEgXTQ8lDLYr8nnHocn7n9GSwF5antgnogEhNDTc'

    accountKeyEnc = base64.b64encode(accountKey + ':' + accountKey)
    headers = {'Authorization': 'Basic ' + accountKeyEnc}
    req = urllib2.Request(bingUrl, headers = headers)
    response = urllib2.urlopen(req)
    content = response.read()
    #content contains the xml/json response from Bing.
    #print content
    tree = json.loads(content)
    results = tree['d']['results']

    i = 0
    for entry in results:
        i += 1
        print str(i) + ': ' + entry['Title']
        print '\t' + entry['Url']
        print '\t' + entry['Description'] + '\n'

    relevant = relevance()


query = raw_input('Please input the desired query: ')
runQuery(query)
