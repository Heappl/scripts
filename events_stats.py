#!/usr/bin/python


def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    return parser.parse_args() 

def shell(command):
    from subprocess import Popen, PIPE
    return Popen(command, stdout=PIPE).communicate()[0].split("\n")

if __name__ == "__main__":
    (options, args) = parse_commandline_options() 
    import os
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    for logfile in args:
        shell(["bash", scriptDir + "/count_events.sh", logfile])



