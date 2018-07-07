# -*- coding: cp936 -*-
import httplib, urllib

class MessageSender:
    def __init__(self):
        host = 'localhost'
        self.conn = httplib.HTTPConnection(host, 9708)
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    def send(self, text):
        params = urllib.urlencode({'text': text.encode('utf-8')})
        self.conn.request('POST', '/ajax/message.aspx', params, self.headers)
        #response = conn.getresponse()
        print '发送短信请求完毕'

