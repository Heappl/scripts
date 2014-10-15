#!/usr/bin/python

def parse_command_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("-f", "--format", help="timestamp format")
    return parser.parse_args() 
            

def tounix(timestamp, format):
    from datetime import datetime
    from time import mktime
    date = datetime.strptime(timestamp, format)
    return mktime(date.timetuple()) + date.microsecond / 1000000.0


def main():
    (options, args) = parse_command_options()
    for arg in args:
        print(tounix(arg, options.format))

if __name__ == '__main__':
    main()

