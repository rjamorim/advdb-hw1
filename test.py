import urllib2
import base64
import json


bingUrl = 'https://api.datamarket.azure.com/Bing/Search/Web?Query=%27gates%27&$top=10&$format=json' #&format=Atom'
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