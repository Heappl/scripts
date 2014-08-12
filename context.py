#!/usr/bin/python3


def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("-s", "--stack", action='store_true', dest="stack", help="produces stack trace for each running component") 
    parser.add_option("-l", "--last_line", type='int', dest="line", help="prints n last lines for each running component") 
    return parser.parse_args() 

(options, args) = parse_commandline_options() 

def isStartingEvent(event):
    return event in ["fnen", "cost"]
def isEndingEvent(event):
    return event in ["fnlv", "cofi"]
def interesting(line):
    tokens = line.split("|")
    if (len(tokens) < 2):
        return False
    return isStartingEvent(tokens[1]) or isEndingEvent(tokens[1])
def getEndingFor(event):
    events = {"fnen" : "fnlv", "cost" : "cofi"}
    return events.get(event, "invalid")
def getStackDescriptionFor(event):
    events = {"fnlv" : "->", "cofi" : "component"}
    return events.get(event, "")
    
def getEvent(line):
    tokens = line.split("|")
    return tokens[1]
def getEventData(line):
    tokens = line.split("|")
    if (len(tokens) < 2):
        return (None, None)
    if (tokens[1] in ["fnen", "fnlv"]):
        return (tokens[1], tokens[3].split("(")[0])
    return (tokens[1], tokens[2].split("=")[0])

def getThreadName(line):
    tokens = line.split("|")
    if (len(tokens) < 3):
        return ""
    threadTokens = tokens[2].split("=")
    if (threadTokens[0] == "?"):
        return threadTokens[1]
    return threadTokens[0]

def splitPerThread(content):
    ret = {}
    for line in content:
        name = getThreadName(line)
        if (len(name) == 0):
            continue
        threadLog = ret.get(name, [])
        threadLog.append(line)
        ret[name] = threadLog
    return ret

def generateStackForSingleThread(threadName, logs):
    logs = [line for line in logs if interesting(line)]
    stack = []
    for line in logs:
        (event, ident) = getEventData(line)
        if isEndingEvent(event):
            (topEvent, topIdent) = stack.pop()
            if (topEvent != event) or (topIdent != ident):
                print("ERROR: wrong ending event encountered (expected:{" + topEvent + "," + topIdent + "}" +
                      ", seen:{" + event + "," + ident + "})")
        else:
            stack.append((getEndingFor(event), ident))
    if (len(stack) > 0):
        for (event, name) in stack:
            print(getStackDescriptionFor(event), name)

for filepath in args:
    perThreadLogs = splitPerThread(open(filepath).read().split("\n")[:-1])
    if (options.stack):
        for key in perThreadLogs.keys():
            generateStackForSingleThread(key, perThreadLogs[key])
    if (options.line):
        for key in perThreadLogs.keys():
            if getEvent(perThreadLogs[key][-1]) == 'cofi':
                continue
            for i in range(1, options.line + 1):
                if len(perThreadLogs[key]) >= i:
                    print(perThreadLogs[key][-i])
            print("\n")


