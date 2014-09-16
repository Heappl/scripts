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
    parser.add_option("", "--external_only", action='store_true', help="only communication with system will be inserted") 
    (options, args) = parser.parse_args() 
    if (options.disabled_msgs):
        options.disabled_msgs = options.disabled_msgs.split(',')
    return (options, args)

def components(log):
    cocrs = [re.search('\|cocr\|.*\|(.*)\|(once|alive)', line) for line in log]
    return set([res.group(1) for res in cocrs if res != None])
def mapped(log):
    ports = [re.search('\|ptmp\|.*\|([^|]+)\|SYSTEM', line) for line in log]
    return set([res.group(1) for res in ports if res != None])
    

def writeCommOp(out, msg, receiver, sender):
    out.write(sender + " -> " + receiver + ": " + msg + "\n")

class Event:
    def equals(self, other):
        return False if (self.__class__ != other.__class__) else self.equals_impl(other)

class CommEvent(Event):
    def __init__(self):
        self.msg = "invalid"
        self.receiver = "invalid"
        self.sender = "invalid"
    
    def filter(self, options):
        externals = ["system", "null"]
        ret = True
        if (options.external_only):
            ret = ret and (self.receiver in externals) or (self.sender in externals)
        if (options.disabled_msgs):
            if (self.msg in options.disabled_msgs):
                ret = False
        return ret
    def produce(self, out):
        writeCommOp(out, self.msg, self.receiver, self.sender)
    def equals_impl(self, other):
        return (self.msg == other.msg) and (self.receiver == other.receiver) and (self.sender == other.sender)

class PtrxEvent(CommEvent):
    def __init__(self, line):
        CommEvent.__init__(self)
        self.extractInfo(line)

    def extractInfo(self, line):
        res = re.search('\|ptrx\|([^=]+)=.*value=[^.]+\.([^:]+).*sender=[^:]*:(.*),timestamp=.*consume', line)
        if (res != None):
            self.msg = res.group(2)
            self.receiver = res.group(1)
            self.sender = res.group(3)
        res = re.search("(.*)\(running\)", self.sender)
        if (res != None):
            self.sender = res.group(1)
    
    def update(self, comps, systemPorts):
        if not (self.sender in comps) and (self.sender != "null"):
            self.sender = "system"
        

class PtsdEvent(CommEvent):
    def __init__(self, line):
        CommEvent.__init__(self)
        self.extractInfo(line)

    def extractInfo(self, line):
        res = re.search('\|ptsd\|([^=]+)=[^|]+\|[^|]+\|([^|:]+):[^|]+\|[^.]+\.([^|]+)\|', line)
        if (res != None):
            self.msg = res.group(3)
            self.receiver = res.group(2)
            self.sender = res.group(1)
            if (len(self.receiver) > len("SYSTEM")) and (self.receiver[:len("SYSTEM")] == "SYSTEM"):
                self.receiver = "system"
    def filter(self, options):
        return self.receiver == "system"
    def update(self, comps, systemPorts):
        if (self.receiver in systemPorts):
            print (self.receiver)
            self.receiver = "system"

class UlogEvent(Event):
    def __init__(self, line):
        res = re.search('\|ulog\|[^|]+\|("([A-Z]*): *""([^"]*)".*)', line)
        if (res == None):
            res = re.search('\|ulog\|[^|]+\|(.*)', line)
            self.level = "DEBUG"
            self.msg = res.group(1)
        else:
            self.level = res.group(2)
            self.msg = res.group(3)
    def update(self, comps, systemPorts):
        pass
    def filter(self, options):
        return (not options.no_debug) or ((self.level != "DEBUG") and (not options.no_ulogs))
    def produce(self, out):
        out.write("== " + self.level + " " + self.msg + " ==\n")
    def equals_impl(self, other):
        return (self.level == other.level) and (self.msg == other.msg)

class MultipleEvents(Event):
    def __init__(self, event, times):
        self.event = event
        self.times = times
    def update(self, comps, systemPorts):
        pass
    def produce(self, out):
        out.write("loop " + str(self.times) + " times\n")
        self.event.produce(out)
        out.write("end\n")

def createEvents(log):
    def is_ulog(line):
        return re.match('[0-9.T]+\|ulog\|', line) != None
    def is_ptsd(line):
        return re.match('[0-9.T]+\|ptsd\|', line) != None
    def is_ptrx(line):
        return re.match('[0-9.T]+\|ptrx\|.*consume.*', line) != None
    def is_intresting(line):
        return is_ptsd(line) or is_ptrx(line) or is_ulog(line)
    def extractInfo(line):
        if (is_ptsd(line)):
            return PtsdEvent(line)
        if (is_ulog(line)):
            return UlogEvent(line)
        return PtrxEvent(line)
    return [extractInfo(line) for line in log if is_intresting(line)]

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

def generate_uml(logfile, options):
    fromfile = open(logfile).read().split("\n")
    comps = components(fromfile)
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
    events = createEvents(log)
    for event in events:
        event.update(comps, systemPorts)
    events = filter(lambda e : e.filter(options), events)
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


