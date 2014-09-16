#!/usr/bin/python

import re

def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    #parser.add_option("-s", "--stack", action='store_true', dest="stack", help="produces stack trace for each running component") 
    #parser.add_option("-l", "--last_line", type='int', dest="line", help="prints n last lines for each running component") 
    return parser.parse_args() 

def components(log):
    cocrs = [re.search('\|cocr\|.*\|(.*)\|(once|alive)', line) for line in log]
    return set([res.group(1) for res in cocrs if res != None])

def messages(comps, log):
    def is_ptsd(line):
        return re.match('[0-9.T]+\|ptsd\|.*SYSTE', line) != None
    def is_ptrx(line):
        return re.match('[0-9.T]+\|ptrx\|.*consume.*', line) != None
    def extractRecvInfo(line):
        res = re.search('\|ptrx\|([^=]+)=.*value=[^.]+\.([^:]+).*sender=[^:]*:(.*),timestamp=.*consume', line)
        if (res == None):
            print(line)
            return ("invalid", "invalid", "invalid")
        return (res.group(2), res.group(1), res.group(3))
    def extractSendInfo(line):
        res = re.search('\|ptsd\|([^=]+)=.*\|SYSTEM\.[^|]+\|[^.]+\.([^|]+)\|', line)
        if (res == None):
            print(line)
            return ("invalid", "invalid", "invalid")
        return (res.group(2), "system", res.group(1))
    def extractInfo(line):
        if (is_ptsd(line)):
            return extractSendInfo(line)
        return extractRecvInfo(line)
    return [extractInfo(line) for line in log if (is_ptsd(line) or is_ptrx(line))]

def updateSutMsgs(comps, msgs):
    def convert((msg, receiver, sender)):
        if (sender == "null"):
            return (msg, receiver, sender)
        res = re.search("(.*)\(running\)", sender)
        if (res != None):
            sender = res.group(1)
        return (msg, receiver, sender) if (sender in comps) else (msg, receiver, "system")
    return [convert(msg) for msg in msgs]

def generate_uml(logfile):
    log = open(logfile).read().split("\n")
    comps = components(log)
    msgs = messages(comps, log)
    msgs = updateSutMsgs(comps, msgs)
    out = open(logfile + ".uml", "w")
    out.write("@startuml")
    for (msg, receiver, sender) in msgs:
        out.write(sender + " -> " + receiver + ": " + msg + "\n")
    out.write("@enduml")

if __name__ == "__main__":
    (options, args) = parse_commandline_options() 
    for logfile in args:
        generate_uml(logfile)


