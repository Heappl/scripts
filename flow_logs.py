#!/usr/bin/python

from time_to_unix import tounix

def parse_command_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    return parser.parse_args() 
      
def shell(command):
    from subprocess import Popen, PIPE
    return Popen(command, stdout=PIPE).communicate()[0].split("\n")      

def matches(line, regex):
    import re
    return re.search(regex, line) != None

def grep(lines, regex):
    return [line for line in lines if matches(line, regex)]
def grepv(lines, regex):
    return [line for line in lines if not matches(line, regex)]

def extractLogData(arg):
    import re
    res = re.search("([^|]+)\|ulog\|[^|]+\|(.*)", arg)
    if (res == None):
        return None
    return (res.group(1), res.group(2))

def replaceall(arg, regex, sub):
    import re
    return re.sub(regex, sub, arg)

def extractFlowLogs(filename):
    lines = open(filename).read().split("\n")
    ulogLines = grep(lines, "\|ulog\|")
    flowLogs = [replaceall(extractLogData(log)[1], "flow [0-9]+:", "flow:") for log in grep(ulogLines, "ulog\|k3r")]
    rest = [extractLogData(log) for log in grepv(ulogLines, "ulog\|k3r")]
    ret = [(extractLogData(ulogLines[0])[0], "START")]
    ret = ret + [(stamp, content) for (stamp, content) in rest if content in flowLogs]
    return ret

def main():
    (options, args) = parse_command_options()
    for filename in args:
        if (len(args) > 1):
            print(filename + ":")
    flowLogs = extractFlowLogs(filename)
    k3format = "%Y%m%dT%H%M%S.%f"
    firsttime = tounix(flowLogs[0][0], k3format)
    for (timestamp, flowstep) in flowLogs:
        print(str(tounix(timestamp, k3format) - firsttime) + " " + flowstep)

if __name__ == '__main__':
    main()

