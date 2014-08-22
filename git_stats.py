#!/usr/bin/python2

import subprocess, re, os, sys, datetime
import matplotlib.pyplot as plt

def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("", "--author", dest="author", help="User name to search commits by.") 
    parser.add_option("", "--since", dest="since", help="Date since report will be generated.", metavar="DATE") 
    parser.add_option("", "--until", dest="until", help="Generate diff until given date", metavar="DATE") 
    return parser.parse_args() 

(options, args) = parse_commandline_options() 

if not args:
    from sys import exit
    print("ERROR: repository directories, which should generate report, must be passed as command arguments")
    exit(2)

def shell(command):
    from subprocess import Popen, PIPE
    return Popen(command, stdout=PIPE).communicate()[0].decode().split("\n")
def git(command):
    return shell(["git"] + command)

commonGitOpts = []
if (options.author):
    commonGitOpts.append("--author=" + options.author)
if (options.since):
    commonGitOpts.append("--since=" + options.since)
if (options.until):
    commonGitOpts.append("--until=" + options.until)

def additions(line):
    res = re.search('([0-9]+) insert', line)
    if (res == None):
        return 0
    return int(res.group(1))
def deletions(line):
    res = re.search('([0-9]+) delet', line)
    if (res == None):
        return 0
    return int(res.group(1))
def author(line):
    res = re.search('\(author=(.*)\)', line)
    if (res == None):
        return 0
    return res.group(1)
def totals(data):
    ret = {}
    for (author, added, deleted) in data:
        (total, adds, dels, commits) = ret.get(author, (0,0,0,0))
        ret[author] = (total + added - deleted, adds + added, deleted + dels, commits + 1)
    return ret
def countFilesForRevision(hsh, path):
    git(["co", hsh])
    countScript = os.path.dirname(sys.argv[0]) + "/countCppAndCFiles.sh"
    res = shell([countScript, path, "-l"])
    return int(res[0])

data = [line.strip('"').split(",") for line in git(["log", "--pretty=\"%an,%H,%ad\""] + commonGitOpts + args)[:-1]]
data = [(dateOfCommit, countFilesForRevision(hsh, args[0])) for (author, hsh, dateOfCommit) in data]
print(data)
dates = [dateOfCommit for (dateOfCommit, _) in data]
counts = [count for (_, count) in data]
print(counts)

#data = git(["log", "--pretty=\"$^$ (author=%an)\"", "--shortstat"] + commonGitOpts + args);
#data = [(author(line), additions(line), deletions(line)) for line in data]

#totalByAuthor = totals(data)
#for author in totalByAuthor:
    #print(author, totalByAuthor[author])

