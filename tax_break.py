#!/usr/bin/python3

import subprocess

def checkRequiredArguments(opts, parser):
    from re import match
    missing_options = []
    for option in parser.option_list:
        if match(r'^\[REQUIRED\]', option.help) and eval('opts.' + option.dest) == None:
            missing_options.extend(option._long_opts)
    if len(missing_options) > 0:
        parser.error('Missing REQUIRED parameters: ' + str(missing_options))

def parse_commandline_options(): 
    from optparse import OptionParser 
    parser = OptionParser() 
    parser.add_option("-t", "--target-directory", dest="tdir", help="[REQUIRED] Directory where report will be stored.", metavar="DIR") 
    parser.add_option("-n", "--report-name", dest="name", help="[REQUIRED] Name of the report, files will be named after it.") 
    parser.add_option("", "--since", dest="since", help="[REQUIRED] Date since report will be generated.", metavar="DATE") 
    parser.add_option("", "--author", dest="author", help="[REQUIRED] User name to search commits by.", metavar="DATE") 
    parser.add_option("", "--find-touched-files", dest="only_file_list", action='store_true', help="Instead of generating report, will find touched files and print them to stdout.") 
    parser.add_option("", "--until", dest="until", help="Generate diff until given date", metavar="DATE") 
    (options, args) = parser.parse_args() 
    if (not options.only_file_list):
        checkRequiredArguments(options, parser)
    return (options, args)

(options, args) = parse_commandline_options() 

if not args:
    from sys import exit
    print("ERROR: repository directories, which should generate report, must be passed as command arguments")
    exit(2)


common_git_args = ["--since", options.since, "--author", options.author]
if (options.until):
    common_git_args += ["--until", options.until]
common_git_args += args
def shell(command):
    from subprocess import Popen, PIPE
    return Popen(command, stdout=PIPE).communicate()[0].decode().split("\n")[:-1]
def git(command):
    return shell(["git"] + command)

hashes = git(["log", "--pretty=\"%H\""] + common_git_args)

def find_touched_files():
    ret = set()
    for hsh in hashes:
        hsh = hsh.strip("\"")
        ret = ret.union(set(git(["diff", "--name-only", hsh + "^.." + hsh] + args)))
    return ret

touched_files = find_touched_files()
if (options.only_file_list):
    from sys import exit
    for touched in touched_files:
        print(touched)
    exit(0)

def output_files():
    from os import path
    prefix = path.abspath(options.tdir) + "/" + options.name
    return (prefix + ".zip", prefix + ".log", prefix + ".diff")

(zip_file, log_file, diff_file) = output_files()

def generateDiff():
    ret = []
    for hsh in hashes:
        hsh = hsh.strip("\"")
        ret += (git(["diff", hsh + "^.." + hsh] + args))
    return "\n".join(ret)
    

open(log_file, "+w").write("\n".join(git(["log"] + common_git_args)))
print("generated log file: " + log_file)
open(diff_file, "+w").write(generateDiff())
print("generated diff file: " + diff_file)
shell(["zip", zip_file] + list(touched_files) + [log_file])
print("generated zip file: " + zip_file + " containing " + str(len(touched_files) + 2) + " files")

#logs = subprocess.call(["git", "log", "--since", options.since, "--author", options.author] + args)

