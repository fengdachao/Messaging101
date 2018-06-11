import httplib, urllib

class MessageSender:
    def __init__(self):
        conn = httplib.HTTPConnection('localhost/MessagingServer')
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    def send(self, text):
        params = urllib.urlencode({'text': text})
        conn.request('POST', '/ajax/message', params, headers)
        #response = conn.getresponse()

