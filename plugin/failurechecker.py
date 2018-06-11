# -*- coding: cp936 -*-
import time
import traceback
import json
from sqlalchemy import text
import urllib2
from sqlalchemy import create_engine
from memcachesender import memcachesender
from messageSender import messageSender

class failurechecker:
    #datetimeforamt
    DATETIMEFORMAT = '%Y-%m-%d %H:%M:%S'
    
    ISALARMINGFIELD = "isalarming"
    BREAKTIMEFIELD = "breaktime"
    BREAKTIMESTAMPFIELD = "breaktimestamp"
    ALARMTIMEFIELD = "alarmingtime"
    FAILUREDATAFIELD = "failuredata"
    FAILUREDEVIDFIELD = "failuredevid"
    BEGINCHECK = "begincheck"
    alarm_type = "alarm"
    failure_type = "failure"
    
    conn = None

    #报警信息发布器
    sender = None
    
    condition_cfg = {}

    def __init__(self,controller_count=1):
        tmp = {}
        tmp[self.ALARMTIMEFIELD] = int(time.time())
        tmp[self.ALARMTIMEFIELD] = 0
        tmp[self.ISALARMINGFIELD] = False
        tmp[self.BREAKTIMEFIELD] = 0
        tmp[self.BREAKTIMESTAMPFIELD] = 0
        tmp[self.FAILUREDATAFIELD] = 0
        tmp[self.FAILUREDEVIDFIELD] = -1
        tmp[self.BEGINCHECK] = False
        
        self.sender = memcachesender()
        #短信发送器
        self.messageSender = messageSender()
        
##        for index in range(1,controller_count + 1):            
##            self.condition_cfg[index] = tmp
        self.condition_cfg = tmp
        pass

    def endCheck(self,controllerId):
        self.condition_cfg[self.BEGINCHECK] = False

    def checkValue(self,checkData,minVal,maxVal):
        if checkData <= minVal or checkData >= maxVal:
            return True
        return False

    def checkField(self,checkData,alarmValue):
        if checkData == alarmValue:
            return True
        return False
    
    def handleAlarm(self,
                    checkdata,
                    devid,
                    controllerid,
                    devname,
                    isAlarm,
                    alarmDelay,
                    failuredes,
                    alarm_type,
                    check_type
                    ):
        
        nowst = int(time.time())
        checkdata = float(checkdata)
        
        condition_dict = self.condition_cfg
        
        #print 'check devid:%d, controllerid%d,maxdata:%f'%(devid,controllerid,maxValue)
        
        if isAlarm:
            #print 'fail devid:%d, controllerid%d,data:%d,failuredata:%d'%(devid,controllerid,checkdata,minValue)
            if condition_dict[self.ISALARMINGFIELD] == True:
                return
            if condition_dict[self.BEGINCHECK] == False:
                condition_dict[self.ALARMTIMEFIELD] = nowst
                condition_dict[self.BEGINCHECK] = True
                print 'begin'
            else:
                alarmingTime =nowst - condition_dict[self.ALARMTIMEFIELD]
                print 'fail controllerid%d,data:%f release:%d'%(controllerid,checkdata,alarmingTime)
                if alarmingTime > alarmDelay:                    
                    #记录停机
                    print 'alarm !!!'
                    realbreaktimestamp = nowst - alarmDelay
                    #故障开始时间
                    condition_dict[self.BREAKTIMEFIELD] = time.strftime(\
                        self.DATETIMEFORMAT,time.localtime(realbreaktimestamp))
                    condition_dict[self.FAILUREDATAFIELD] = checkdata                 #停机数据
                    condition_dict[self.FAILUREDEVIDFIELD] = devid                      #故障发射机id
                    condition_dict[self.BREAKTIMESTAMPFIELD] = realbreaktimestamp       #时间戳
                    condition_dict[self.ISALARMINGFIELD] = True                        #停机状态
                    condition_dict[self.BEGINCHECK] = False
                    #生成消息
                    message = {}
                    message["Id"] = str(condition_dict[self.BREAKTIMESTAMPFIELD]) + str(controllerid) + str(check_type) + str(alarm_type)
                    my_type = -1
                    if check_type == self.alarm_type:
                        my_type = 1
                    elif check_type == self.failure_type:
                        my_type =2
                    message["MyType"] = my_type
                    message["CreateTimeStamp"] = condition_dict[self.BREAKTIMESTAMPFIELD]            
                    message["Message"] = devname + failuredes
                    
                    self.sender.sendMessage(message)
                    pass
                pass
            pass
        else:
            #更新数据处于正常范围的时刻
            #print 'normal devid:%d, controllerid%d,data:%d'%(devid,controllerid,checkdata)
            if condition_dict[self.ISALARMINGFIELD] == True:                
                #停播数据写入
                alarminfo = {}
                alarminfo["StationName"] = "101"
                alarminfo["Id"] = str(condition_dict[self.BREAKTIMESTAMPFIELD]) + str(controllerid) + str(check_type) + str(alarm_type)
                alarminfo["Controllerid"] = controllerid
                alarminfo["BeginTime"] = condition_dict[self.BREAKTIMEFIELD]
                alarminfo["EndTime"] = time.strftime(self.DATETIMEFORMAT,time.localtime())
                alarminfo["LastSecond"] = nowst-condition_dict[self.BREAKTIMESTAMPFIELD]
                alarminfo["BeginTimeStamp"] = condition_dict[self.BREAKTIMESTAMPFIELD]
                alarminfo["BeginData"] = condition_dict[self.FAILUREDATAFIELD]
                alarminfo["EndData"] = checkdata
                alarminfo["BeginDeviceId"] = condition_dict[self.FAILUREDEVIDFIELD]
                alarminfo["EndDeviceId"] = devid
                alarminfo["Message"] = devname + failuredes
                alarminfo["AlarmType"] = alarm_type
                
                if check_type == self.alarm_type:
                    self.sender.sendAlarm(alarminfo)
                    
                elif check_type == self.failure_type:
                    self.sender.sendFailure(alarminfo)
                    #发送短信
                    self.messageSender.send(alarminfo["Message"])
                #更新报警状态为没有报警
                condition_dict[self.ISALARMINGFIELD] = False
                #删除已恢复的报警
                self.sender.removeMessage(alarminfo)
                pass
            if condition_dict[self.BEGINCHECK] == True:
                condition_dict[self.BEGINCHECK] = False
                pass
            pass
        #print 'controllerid is begin:' + str(condition_dict[self.BEGINCHECK])
        self.condition_cfg = condition_dict
        pass
    
    def checkAlarm(self,                     
                    data,
                    devid,
                    controllerid,
                    devname,
                    minValue,
                    maxValue,
                    alarmDelay,
                    failuredes,
                    alarm_type):
        data = float(data)
        isAlarm = self.checkValue(data,minValue,maxValue)
        self.handleAlarm(
                data,
                devid,
                controllerid,
                devname,
                isAlarm,
                alarmDelay,
                failuredes,
                alarm_type,
                self.alarm_type)

    def checkFailure(self,                     
                 data,
                 devid,
                 controllerid,
                 devname,
                 minValue,
                 maxValue,
                 alarmDelay,
                 failuredes,
                 alarm_type):
        data = float(data)
        isAlarm = self.checkValue(data,minValue,maxValue)
        self.handleAlarm(
                data,
                devid,
                controllerid,
                devname,
                isAlarm,
                alarmDelay,
                failuredes,
                alarm_type,
                self.failure_type)
    def checkFieldAlarm(self,
                         data,
                         devid,
                         controllerid,
                         devname,
                         alarmValue,
                         alarmDelay,
                         failuredes,
                         alarm_type):
        data = float(data)
        isAlarm = self.checkField(data,alarmValue)
        self.handleAlarm(
            data,
            devid,
            controllerid,
            devname,
            isAlarm,
            alarmDelay,
            failuredes,
            alarm_type,
            self.alarm_type)

    def checkFieldFailure(self,
                          data,
                          devid,
                          controllerid,
                          devname,
                          alarmValue,
                          alarmDelay,
                          failuredes,
                          alarm_type):
        data = float(data)
        isAlarm = self.checkField(data,alarmValue)
        self.handleAlarm(
            data,
            devid,
            controllerid,
            devname,
            isAlarm,
            alarmDelay,
            failuredes,
            alarm_type,
            self.failure_type)
        
if __name__=="__main__":
    from sqlalchemy import create_engine
    import json
    import time
    print 'run at main'
    max_value = 201.1
    checker = failurechecker(10)
    while True:
        time.sleep(1)
        checker.checkFailure(
                             0,
                             0,
                             1,                         
                             '1143KHz',
                             1,
                             max_value,
                             10,
                             '欠调幅',
                             'remark...')

    

        




















        
