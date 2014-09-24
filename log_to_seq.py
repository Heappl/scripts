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
    parser.add_option("", "--enable_comps", type='str', dest="enabled_comps", help="comma separated list of components (python regex without comma) that will be displayed in the output diagram (`system` for sut)")
    parser.add_option("", "--disable_comps", type='str', dest="disabled_comps", help="comma separated list of components (python regex without comma) that won't be displayed in the output diagram (`system` for sut)")
    parser.add_option("-s", "--strict_comp_filtering", action='store_true', help="component filtering for enabled components will be strict (both components must match)")
    parser.add_option("", "--internal", action='store_true', help="By default no k3 internal communication is disabled") 
    parser.add_option("", "--duplication_limit", type='int', help="set maximum duplication size to check, by default it is infinity, setting lower limit should improve time consumed") 
    (options, args) = parser.parse_args() 
    if (options.disabled_msgs):
        options.disabled_msgs = options.disabled_msgs.split(',')
    if (options.enabled_comps):
        options.enabled_comps = options.enabled_comps.split(',')
    if (options.disabled_comps):
        options.disabled_comps = options.disabled_comps.split(',')
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

def matchesSomeRegex(arg, regexList):
    for elem in regexList:
        if re.match('.*' + elem + '.*',  arg) != None:
            return True
    return False
def matchingSomeRegex(elems, regexList):
    return [matchesSomeRegex(elem, regexList) for elem in elems]

class CommEvent(Event):
    def __init__(self, line, msgExtractor):
        self.msg = "invalid"
        self.receiver = "invalid"
        self.sender = "invalid"
        self.extractInfo(line, msgExtractor)
    
    def filter(self, options, systemPorts):
        ret = True
        if (not options.internal):
            ret = ret and ((self.sender == "system") or (self.receiver == "system"))
        if (options.disabled_msgs):
            ret = ret and (not matchesSomeRegex(self.msg, options.disabled_msgs))
        if (options.disabled_comps):
            matching = matchingSomeRegex([self.receiver, self.sender], options.disabled_comps)
            ret = ret and (not any(matching))
        if (options.enabled_comps):
            matching = matchingSomeRegex([self.receiver, self.sender], options.enabled_comps)
            ret = ret and (all(matching) if (options.strict_comp_filtering) else any(matching))
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
        CommEvent.__init__(self, line, msgExtractor)
        self.received = 0
    
    def extractInfo(self, line, msgExtractor):
        res = re.search('\|ptqu\|([^=$]+)=[^|]+\|[$]*([^$|]+)\|message\(value=[^.]+\.([^:]+)(.*)timestamp=([0-9T.]+)\)', line)
        if (res == None):
            res = re.search('\|ptqu\|([^|]+)\|[$]*([^$|]+)\|message\(value=[^.]+\.([^:]+)(.*)timestamp=([0-9T.]+)\)', line)
        if (res != None):
            self.msg = msgExtractor(res.group(3), res.group(4))
            self.receiver = res.group(2)
            self.sender = res.group(1)
            self.timestamp = res.group(5)
        else:
            print(line)
    
    def update(self, systemPorts):
        if (self.receiver in systemPorts):
            self.sender = "system"
        if (self.sender == '?'):
            self.sender = "system"
        self.receiver = getComponent(self.receiver)
        self.sender = getComponent(self.sender)

    def setReceived(self, msgQueuedTimes):
        self.received = msgQueuedTimes

    def produce(self, out):
        CommEvent.produce(self, out)
        if (self.received == 0):
            out.write("destroy " + self.receiver + "\n")
    def filter(self, options, systemPorts):
        return (self.received < 2) and CommEvent.filter(self, options, systemPorts)

    @staticmethod
    def descr():
        return "ptqu"

class PtrxEvent(CommEvent):
    def __init__(self, line, msgExtractor):
        CommEvent.__init__(self, line, msgExtractor)
        self.queued = True

    def extractInfo(self, line, msgExtractor):
        res = re.search('\|ptrx\|[^|]+\|([^|]+)\|.*\|ready\(match=message\(value=[^.]+\.([^:]+):(.*).*,sender=(.*),timestamp=([0-9T.]+)\)\)\+consume', line)
        if (res != None):
            self.msg = msgExtractor(res.group(2), res.group(3))
            self.receiver = res.group(1)
            self.sender = res.group(4)
            self.timestamp = res.group(5)
        else:
            print(line)
    
    def update(self, systemPorts):
        if (self.receiver in systemPorts):
            self.sender = "system"
        self.receiver = getComponent(self.receiver)
        self.sender = getComponent(self.sender)
    def standalone(self):
        self.queued = False
    def filter(self, options, systemPorts):
        return not self.queued

    @staticmethod
    def descr():
        return "ptrx.*consume"
        

#sending to system - can be extracted only through ptsd event
class PtsdEvent(CommEvent):
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
        res = re.search('\|ulog\|[^|]+\|("([A-Z]*)[: ]*""([^"]*)".*)', line)
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
    eventTypes = [UlogEvent, PtsdEvent, PtquEvent, PtrxEvent]

    def is_event(eventType, line):
        return re.match('[0-9.T]+\|' + eventType.descr(), line) != None
    def is_interesting(line):
        return any(map(lambda eventType : is_event(eventType, line), eventTypes))
    def extractInfo(line):
        eventType = next((eventType for eventType in eventTypes if is_event(eventType, line)), Invalid)
        return eventType(line, msgExtractor) 
    return [extractInfo(line) for line in log if is_interesting(line)]

def contract(events, options):
    if (options.duplication_limit == 0):
        return events
    def generateHashes(events):
        hashes = [hash(event) for event in events]
        ret = {}
        reduction = len(hashes) if (not options.duplication_limit) else options.duplication_limit
        for i in range(0, len(hashes)):
            for j in range(i + 1, min(i + reduction, len(hashes) + 1)):
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
            if (start == prevend) and (events[start:end] == events[prevstart:prevend]):
                ret.append(elem)
            else:
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
    def compareDuplicates((times1, start1, end1), (times2, start2, end2)):
        size1 = (end1 - start1)
        size2 = (end2 - start2)
        if (size1 == size2):
            if (times1 > times2):
                return -1
            elif (times1 < times2):
                return 1
            else:
                return 0
        elif (size1 > size2):
            return -1
        else:
            return 1
    duplicates = sorted(duplicates, compareDuplicates)
    for duplicate in duplicates:
        events = contractRanges(duplicate, events)
    for event in events:
        if (event.size() > 1):
            event.events = contract(event.events, options)
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

def matchQueuedWithReceived(events):
    import itertools
    def getReceiver(event):
        return event.receiver
    def isInstanceAnyOf(inst, classes):
        return any([isinstance(inst, cl) for cl in classes])
    def groupByPort(events):
        import collections
        ret = {}
        for event in events:
            if not event.receiver in ret:
                ret[event.receiver] = collections.deque()
            ret[event.receiver].append(event)
        return ret

    queued = groupByPort([event for event in events if isinstance(event, PtquEvent)])
    received = groupByPort([event for event in events if isinstance(event, PtrxEvent)])

    def matchQueueWithReceived_singlePort(queued, received):
        def areEqual(first, second):
            return (first.msg == second.msg) and (first.timestamp == second.timestamp)

        for event in received:
            if (not queued) or (not areEqual(queued[0], event)):
                event.standalone()
                continue
            count = 1
            while (queued and areEqual(queued[0], event)):
                queued.popleft().setReceived(count)
                count = count + 1
        for event in queued:
            print("queued and never received: " + str(event))

    for key in queued.keys():
        receivedByPort = received[key] if key in received else []
        matchQueueWithReceived_singlePort(queued[key], receivedByPort)


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
    matchQueuedWithReceived(events)
    for event in events:
        event.update(systemPorts)
    events = filter(lambda e : e.filter(options, systemPorts), events)
    events = contract(events, options)
    out = open(logfile + ".uml", "w")
    out.write("@startuml\n")
    for event in events:
        event.produce(out)
    out.write("@enduml\n")

if __name__ == "__main__":
    (options, args) = parse_commandline_options() 
    for logfile in args:
        generate_uml(logfile, options)


