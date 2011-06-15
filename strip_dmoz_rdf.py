#!/usr/bin/env python
import os
import sys
from optparse import OptionParser

def strip_XML(XMLFileName, options):
    if options.output_file:
        outputFile = open(options.output_file, "w")
    else:
        outputFile = sys.stdout

    with open(XMLFileName) as XMLFile:
        externalPage = False
        alias = False
        isWritable = lambda l: (not externalPage
                                and not alias
                                and "<d:Description>" not in l
                                and "<lastUpdate>" not in l
                                and "<d:Title>" not in l
                                and "<editor" not in l
                                and "<altlang" not in l
                                and "<related" not in l
                                and "<newsgroup" not in l)
        for l in XMLFile:
            if "<ExternalPage" in l:
                externalPage = True
            elif "</ExternalPage>" in l:
                externalPage = False
            elif "<Alias" in l:
                alias = True
            elif "</Alias>" in l:
                alias = False
            elif isWritable(l):
                outputFile.write(l)


def main():
    usage = "Usage: %prog XML_FILE [Options]"
    parser = OptionParser(usage)
    parser.add_option("-o", "--output-file", default="",
                      help="File where to write the XML file once stripped. If no file is provided it writes the result on the stdout.")
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments. Use --help to get more information")

    XMLFileName = args[0]
        
    strip_XML(XMLFileName, options)

if __name__ == "__main__":
    main()
