#!/usr/bin/python2

import commands
import re
import time


def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("-o", "--output", dest="output", help="output files") 
    parser.add_option("-d", "--delay", type='float', default=1.0, dest="delay", help="time between measurements") 
    return parser.parse_args() 

(options, args) = parse_commandline_options() 


freeout = commands.getoutput("free -m | grep Mem")
found = re.search("Mem: +[0-9]+ +[0-9]+ +([0-9]+)", freeout)
mem = found.group(1)


while(True):
    log = (str(time.time()) + " " + str(mem))
    if (options.output):
        outfile = open(options.output, "a").write(log + "\n")
    print(log)
    time.sleep(options.delay)


