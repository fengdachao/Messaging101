# -*- coding: cp936 -*-
from messageSender import MessageSender

if __name__ == "__main__":
    print "---------测试发送-------"
    sender = MessageSender()
    sender.send(u"测试短信")

