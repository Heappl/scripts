#!/usr/bin/python

import re

def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("", "--debug_logs", default=True, action='store_false', dest="no_debug", help="turn to produce debug logs, by default only info logs/warning/error are displayed (those starting with DEBUG, WARNING, ERROR)") 
    parser.add_option("", "--no_ulogs", action='store_true', help="disable ulog events completely") 
    parser.add_option("", "--since_line", type='str', dest="since_line", help="the generated logs will start from there - any python regex is accepted and it may consider any line in log")
    parser.add_option("", "--till_line", type='str', dest="till_line", help="the generated logs will end here - any python regex is accepted and it may consider any line in log")
    parser.add_option("", "--disable_msgs", type='str', dest="disabled_msgs", help="comma separated list of messages (python regex without comma) that will not be displayed in output diagram")
    parser.add_option("", "--internal", action='store_true', help="By default no k3 internal communication is disabled") 
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
    def __eq__(self, other):
        return False if (self.__class__ != other.__class__) else self.equals_impl(other)
    def update(self, systemPorts):
        pass
    def size(self):
        return 1

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
        if (not options.internal):
            ret = ret and ((self.sender == "system") or (self.receiver == "system"))
        if (options.disabled_msgs):
            ret = ret and not msgDisabled(self.msg, options.disabled_msgs)
        return ret

    def produce(self, out):
        writeCommOp(out, self.msg, self.receiver, self.sender)
    def equals_impl(self, other):
        return (self.msg == other.msg) and (self.receiver == other.receiver) and (self.sender == other.sender)

    def __hash__(self):
        return hash((self.__class__, self.msg, self.sender, self.receiver))

    def __str__(self):
        return "{" + self.sender + " -> " + self.receiver + ": " + self.msg + "}"


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
        if (self.receiver in systemPorts):
            self.sender = "system"
        if (self.sender == '?'):
            self.sender = "system"
        self.receiver = getComponent(self.receiver)
        self.sender = getComponent(self.sender)

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
        if (self.sender in systemPorts):
            self.receiver = "system"
        self.sender = getComponent(self.sender)
        self.receiver = getComponent(self.receiver)

    @staticmethod
    def descr():
        return "ptsd"

class UlogEvent(Event):
    def __init__(self, line, _):
        res = re.search('\|ulog\|[^|]+\|("([A-Z]*)[: *]""([^"]*)".*)', line)
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
    def __hash__(self):
        return hash((self.__class__, self.level, self.msg))

    @staticmethod
    def descr():
        return "ulog"

    def __str__(self):
        return "{" + self.level + ": " + self.msg + "}"

class MultipleEvents(Event):
    def __init__(self, events, times):
        self.events = events
        self.times = times
    def produce(self, out):
        out.write("loop " + str(self.times) + " times\n")
        for event in self.events:
            event.produce(out)
        out.write("end\n")
    def size(self):
        return self.times * reduce(lambda acc, event : acc + event.size(), self.events, 0)
    def equals_impl(self, other):
        return (self.times, self.events) == (other.times, other.events)
    def extractEvents(self):
        def extractFromEvent(event):
            return event.extractEvents() if (event.__class__ == self.__class__) else [event]
        return sum([extractFromEvent(event) for event in self.events], [])
    def patternSize(self):
        return self.size() / self.times
    def __hash__(self):
        return hash((self.__class__, self.times, self.events))
    def __str__(self):
        return "{" + str(self.times) + " [" + [str(event) for event in self.events] + "]}"

class Invalid(Event):
    def __init__(_1, _2, _3):
        pass

def createEvents(log, msgExtractor):
    eventTypes = [UlogEvent, PtsdEvent, PtquEvent]

    def is_event(eventType, line):
        return re.match('[0-9.T]+\|' + eventType.descr() + '\|', line) != None
    def is_interesting(line):
        return any(map(lambda eventType : is_event(eventType, line), eventTypes))
    def extractInfo(line):
        eventType = next((eventType for eventType in eventTypes if is_event(eventType, line)), Invalid)
        return eventType(line, msgExtractor) 
    return [extractInfo(line) for line in log if is_interesting(line)]

def contract(events):
    def generateHashes(events):
        hashes = [hash(event) for event in events]
        ret = {}
        for i in range(0, len(hashes)):
            for j in range(i + 1, len(hashes)):
                totalHash = reduce(lambda a, b: hash((a, b)), hashes[i:j], 0)
                if not (totalHash in ret):
                    ret[totalHash] = []
                ret[totalHash].append((i, j))
        return ret

    def extractContinuations(first, rangeList, events):
        ret = [first]
        retRangeList = []
        for (start, end) in rangeList:
            elem = (start, end)
            (prevstart, prevend) = ret[-1]
            appended = False
            if (start == prevend):
                if events[start:end] == events[prevstart:prevend]:
                    ret.append(elem)
                    appended = True
            if (not appended):
                retRangeList.append(elem)
        
        (firsti, _) = ret[0]
        (_, lastj) = ret[-1]
        return ((len(ret), firsti, lastj), retRangeList)

    def extractDuplicates(ranges):
        ret = []
        ranges = sorted(ranges)
        while (ranges):
            first = ranges[0]
            ((times, start, end), ranges) = extractContinuations(first, ranges[1:], events)
            if (times > 1):
                ret.append((times, start, end))
        return ret
                
    def contractRanges((times, start, end), events):
        if (times < 2):
            return events
        
        patternSize = (end - start) / times

        ret = []
        retTail = []
        toContract = []
        it = 0
        toContractStart = -1
        toContractEnd = -1

        def inside(pnt, start, end):
            return (start < pnt) and (pnt < end)
        for event in events:
            nextIt = it + event.size()

            if (nextIt <= start):
                ret.append(event)
            elif (it >= end):
                retTail.append(event)
            else:
                toContract.append(event)
                if (toContractStart == -1):
                    toContractStart = it 
                toContractEnd = nextIt

            it = it + event.size()
        if (toContractStart != start) or (toContractEnd != end) or (len(toContract) != (end - start)):
            return ret + toContract + retTail
        
        def contractEvents(toContract, times, start, end):
            if (not toContract):
                return []
            return [MultipleEvents(toContract[:patternSize], times)]

        return ret + contractEvents(toContract, times, start, end) + retTail
        
    hashMap = generateHashes(events)
    duplicates = sum([extractDuplicates(hashMap[key]) for key in hashMap.keys()], [])
    duplicates = reversed(sorted(duplicates, key=lambda (times, start, end): ((end - start), times)))
    for duplicate in duplicates:
        events = contractRanges(duplicate, events)
    for event in events:
        if (event.size() > 1):
            event.events = contract(event.events)
    return events

def msgExtractorExists():
    import imp
    try:
        imp.find_module('msgExtractor')
        return True
    except ImportError:
        return False

def getCustomOrDefaultMsgExtractor():
    if (msgExtractorExists()):
        from msgExtractor import extract
        return extract
    else:
        return lambda msgName, msgContent: msgName

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

    events = createEvents(log, getCustomOrDefaultMsgExtractor())
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


