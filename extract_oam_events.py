#!/usr/bin/python

def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("-t", "--with_timestamps", help="events will contain timestamps /timestamp event/") 
    return parser.parse_args() 

def convert_to_events(options, lines):
    import re
    ret = []
    for line in lines:
        res = re.search('([0-9T.]+).( [^ ]+){5} ([^/]+)/([^ ]+) (.*)', line)
        if not res:
            continue
        timestamp = res.group(1)
        level = res.group(3)
        location = res.group(4)
        content = res.group(5)
        content = re.sub('0x[0-9A-Z-a-z]+', ' ', content)
        content = re.sub('[^A-Za-z]', ' ', content)
        content = re.sub(' +', ' ', content)

        res = re.search('^(LGC|CCS|Aa|OAM.OAMThread|OAM.OAMGen)', location)
        if (res != None):
            continue

        if (options.with_timestamps):
            ret.append(timestamp + " " + location)
        else:
            ret.append(location + " " + content)
            
    return ret
    

if __name__ == "__main__":
    (options, args) = parse_commandline_options() 
    for logfile in args:
        lines = open(logfile).read().split("\n")[:-1]
        converted = convert_to_events(options, lines)
        open(logfile + ".events", "w").write("\n".join(converted))

