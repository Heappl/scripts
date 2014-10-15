#!/usr/bin/python

class Options(object):
    def __init__(self):
        self.__parse_command_options()

    def __parse_command_options(self): 
        from optparse import OptionParser 

        parser = OptionParser() 
        parser.add_option("-o", "--output_dir", help="output directory")
        (self.options, self.files) = parser.parse_args() 
        import os, sys
        if (self.options.output_dir):
            if (not os.path.isdir(self.options.output_dir)):
                print("output directory doesn't exist")
                sys.exit(1)
            self.output = self.options.output_dir
        else:
            self.output = "."
            


def shell(command):
    from subprocess import Popen, PIPE
    return Popen(command, stdout=PIPE).communicate()[0].split("\n")

def getBinaries(filename):
    import os
    scriptDir = os.path.dirname(os.path.realpath(__file__))
    return shell(["bash", scriptDir + "/print_binaries_names.sh", filename])

def extractFile(infile, outfile, regex):
    extracted = shell(["grep", regex, infile])[:-1]
    if (len(extracted) == 0):
        return
    open(outfile, "w").write("\n".join(extracted))

def splitFile(filename, outdir):
    for name in getBinaries(filename):
        if name:
            extractFile(filename, outdir + "/" + filename + "." + name + ".log", "^[^ ]* .. " + name)

def main():
    opts = Options()
    for filename in opts.files:
        splitFile(filename, opts.output)

if __name__ == '__main__':
    main()

