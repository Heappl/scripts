#!/usr/bin/python

import re

def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("", "--debug_logs", default=True, action='store_false', dest="no_debug", help="turn to produce debug logs") 
    parser.add_option("", "--no_ulogs", action='store_true', help="disable ulog") 
    parser.add_option("", "--since_line", type='str', dest="since_line", help="the generated logs will start from there")
    parser.add_option("", "--till_line", type='str', dest="till_line", help="the generated logs will end here")
    parser.add_option("", "--disable_msgs", type='str', dest="disabled_msgs", help="comma separated list of messages to not display in output diagram")
    parser.add_option("", "--external_only", action='store_true', help="Disabled - external only is default") 
    (options, args) = parser.parse_args() 
    if (options.disabled_msgs):
        options.disabled_msgs = options.disabled_msgs.split(',')
    return (options, args)

def mapped(log):
    ports = [re.search('\|ptmp\|.*\|([^|]+)\|SYSTEM', line) for line in log]
    return set([res.group(1) for res in ports if res != None])
    

def getComponent(port):
    port = port.replace('~', '')
    port = port.replace('$', '')
    port = port.replace(' ', '_')
    port = port.replace('-', '_')
    res = re.match('([^.]+)\.', port)
    return port if (res == None) else res.group(1)
def writeCommOp(out, msg, receiver, sender):
    out.write(sender + " -> " + receiver + ": " + msg + "\n")

class Event:
    def equals(self, other):
        return False if (self.__class__ != other.__class__) else self.equals_impl(other)
    def update(self, systemPorts):
        pass

def msgDisabled(msg, disabledList):
    for disabledMsg in disabledList:
        if re.match('.*' + disabledMsg + '.*',  msg) != None:
            return True
    return False

class CommEvent(Event):
    def __init__(self):
        self.msg = "invalid"
        self.receiver = "invalid"
        self.sender = "invalid"
    
    def filter(self, options, systemPorts):
        ret = True
        if (options.external_only):
            ret = ret and ((self.sender == "system") or (self.receiver == "system"))
        if (options.disabled_msgs):
            ret = ret and not msgDisabled(self.msg, options.disabled_msgs)
        return ret

    def produce(self, out):
        writeCommOp(out, self.msg, self.receiver, self.sender)
    def equals_impl(self, other):
        return (self.msg == other.msg) and (self.receiver == other.receiver) and (self.sender == other.sender)


#most communication can be extracted through ptqu event
class PtquEvent(CommEvent):
    def __init__(self, line, msgExtractor):
        CommEvent.__init__(self)
        self.extractInfo(line, msgExtractor)

    def extractInfo(self, line, msgExtractor):
        res = re.search('\|ptqu\|([^=$]+)=[^|]+\|[$]*([^$|]+)\|message\(value=[^.]+\.([^:]+)(.*)\)', line)
        if (res == None):
            res = re.search('\|ptqu\|([^|]+)\|[$]*([^$|]+)\|message\(value=[^.]+\.([^:]+)(.*)\)', line)
        if (res != None):
            self.msg = msgExtractor(res.group(3), res.group(4))
            self.receiver = res.group(2)
            self.sender = res.group(1)
        else:
            print(line)
    
    def update(self, systemPorts):
        self.sender = getComponent(self.sender)
        self.receiver = getComponent(self.sender)
        if (self.sender == '?'):
            self.sender = "system"
        if not (self.sender in systemPorts):
            self.sender = "system"

    @staticmethod
    def descr():
        return "ptqu"
        

#sending to system - can be extracted only through ptsd event
class PtsdEvent(CommEvent):
    def __init__(self, line, msgExtractor):
        CommEvent.__init__(self)
        self.extractInfo(line, msgExtractor)

    def extractInfo(self, line, msgExtractor):
        res = re.search('\|ptsd\|[^|]+\|([^|]+)\|[^|]+\|[^.]+\.([^|]+)\|(.*)', line)
        if (res != None):
            self.msg = msgExtractor(res.group(2), res.group(3))
            self.receiver = "invalid"
            self.sender = res.group(1)
            if (len(self.receiver) > len("SYSTEM")) and (self.receiver[:len("SYSTEM")] == "SYSTEM"):
                self.receiver = "system"

    def filter(self, options, systemPorts):
        return (self.receiver == "system") and CommEvent.filter(self, options, systemPorts)
    def update(self, systemPorts):
        self.sender = getComponent(self.sender)
        self.receiver = getComponent(self.sender)
        if (self.sender in systemPorts):
            self.receiver = "system"

    @staticmethod
    def descr():
        return "ptsd"

class UlogEvent(Event):
    def __init__(self, line, _):
        res = re.search('\|ulog\|[^|]+\|("([A-Z]*): *""([^"]*)".*)', line)
        if (res == None):
            res = re.search('\|ulog\|[^|]+\|(.*)', line)
            self.level = "DEBUG"
            self.msg = res.group(1)
        else:
            self.level = res.group(2)
            self.msg = res.group(3)
    def filter(self, options, systemPorts):
        return (not options.no_debug) or ((self.level != "DEBUG") and (not options.no_ulogs))
    def produce(self, out):
        out.write("== " + self.level + " " + self.msg + " ==\n")
    def equals_impl(self, other):
        return (self.level == other.level) and (self.msg == other.msg)

    @staticmethod
    def descr():
        return "ulog"

class MultipleEvents(Event):
    def __init__(self, event, times):
        self.event = event
        self.times = times
    def produce(self, out):
        out.write("loop " + str(self.times) + " times\n")
        self.event.produce(out)
        out.write("end\n")

class Invalid(Event):
    def __init__(_1, _2, _3):
        pass

def createEvents(log, msgExtractor):
    eventTypes = [PtsdEvent, PtquEvent]

    def is_event(eventType, line):
        return re.match('[0-9.T]+\|' + eventType.descr() + '\|', line) != None
    def is_interesting(line):
        return any(map(lambda eventType : is_event(eventType, line), eventTypes))
    def extractInfo(line):
        eventType = next((eventType for eventType in eventTypes if is_event(eventType, line)), Invalid)
        return eventType(line, msgExtractor) 
    return [extractInfo(line) for line in log if is_interesting(line)]

def contract(events):
    def create_multiple_or_not(times, first):
        return first if (times == 1) else MultipleEvents(first, times)
    def contract_two((times, last, acc), event):
        if (last == None):
            return (1, event, acc)
        elif (last.equals(event)):
            return (times + 1, last, acc)
        else:
            return (1, event, acc + [create_multiple_or_not(times, last)])
    (times, last, events) = reduce(contract_two, events, (0, None, []))
    if (last == None):
        return []
    return events + [create_multiple_or_not(times, last)]

def msgExtractor(msg, line):
    if (msg == "IMUpdateNotification") or (msg == "IMExecutionRequest"):
        res = re.search('.*distname:="([^"]+)"', line)
        return msg if (res == None) else msg + "(" + res.group(1) + ")"

    if (msg == "IMChangeRequest"):
        res = re.search('request_id:=([^,]+).*distname:="([^"]+)"', line)
        #res = re.search("object:=.*object:={([^:]+):=", line)
        return msg if (res == None) else msg + "#" + res.group(1) + "(" + res.group(2) + ")"

    if (msg == "IMOperationExecuted"):
        res = re.search('request_id:=([^,]+)', line)
        return msg if (res == None) else msg + "#" + res.group(1)

    if (msg == "IMExecutionResult"):
        res = re.search('request_id:=([^,]+).*execution_status:=([^,}]+)', line)
        return msg if (res == None) else msg + "#" + res.group(1) + "(" + res.group(2) + ")"
    return msg

def generate_uml(logfile, options):
    fromfile = open(logfile).read().split("\n")
    systemPorts = mapped(fromfile)

    since_log_seen = (options.since_line == None)
    log = []
    for line in fromfile:
        if (options.since_line and not since_log_seen):
            if (re.match(".*" + options.since_line, line)):
                since_log_seen = True
        if (options.till_line and since_log_seen):
            if (re.match(".*" + options.till_line, line)):
                break
        if (since_log_seen):
            log.append(line)
    events = createEvents(log, msgExtractor)
    for event in events:
        event.update(systemPorts)
    events = filter(lambda e : e.filter(options, systemPorts), events)
    events = contract(events)
    out = open(logfile + ".uml", "w")
    out.write("@startuml\n")
    for event in events:
        event.produce(out)
    out.write("@enduml\n")

if __name__ == "__main__":
    (options, args) = parse_commandline_options() 
    for logfile in args:
        generate_uml(logfile, options)


