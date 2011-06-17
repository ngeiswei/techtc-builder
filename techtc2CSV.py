#!/usr/bin/env python
#
# Author: Nil Geisweiller

"""Script to convert the TechTC-300 Test Collection found at
http://techtc.cs.technion.ac.il/techtc300/techtc300.html into a CSV
feature vector.

Some preprocessing:
1) All punctuation characters are removed from tokens
2) Everything is converted in lower case
3) Stop words are ignored ### this step is ignore for now ###
4) dash characters between words are removed (brain-washed => brainwashed)
5) numbers and mixed alphanumaric strings (e.g. Win2K) are ignored
6) Stemming is performed using PyStemmer
7) Words appearing in less than 3 documents are removed
"""

import sys
import os
import Stemmer
from collections import Counter
from optparse import OptionParser

# 1) Stop words are removed
# Google's list of stop words
stop_words = set(["i", "a", "about", "an", "are", "as", "at", "be", "by", "com", "de", "en", "for", "from", "how", "in", "is", "it", "la", "of", "on", "or", "that", "the", "this", "to", "was", "what", "when", "where", "who", "will", "with", "und", "the", "www"])

stemmer = Stemmer.Stemmer("english")

def check_file(fileTitle,fileName):
    if not os.path.exists(fileName):
        sys.stderr.write("error: "+ fileTitle+" "+fileName+" not found")
        sys.stderr.write(os.linesep)
        sys.exit()

def preprocessWord(word):
    # 1) All punctuation characters are removed from tokens
    word.strip(",.?:;!\"")
    # 2) Everything is converted in lower case
    word=word.lower()
    # # 3) Stop words are ignored
    # if word in stop_words:
    #     return ""
    # 4) dash characters between words are removed (brain-washed => brainwashed)
    word.replace("-", "")
    # 5) numbers and mixed alphanumaric strings (e.g. Win2K) are ignored
    if not word.isalpha():
        return ""
    # 6) Stemming is performed using PyStemmer
    global stemmer
    word = stemmer.stemWord(word)
    return word

# collect and preprocess (filter and stem) all words of the line
def preprocessLine(line):
    words = set()
    for w in line.split():
        for subw in w.split("'"):    # split ' (e.g. "you're")
            word = preprocessWord(subw)
            if word:
                words.add(word)
    return words
    
# read a dmoz_doc and return the set of words that it contains.
# On the way it filters and stem the words
def DocWords(doc):
    words = set()
    for l in doc:
        words |= preprocessLine(l)
    return words

# Return a list of set of words, each element of the list corresponds
# to a document and the set of words whether it appears or not in the
# document
def FListWords(File):
    lines = File.readlines()
    start_doc = False
    res = []                    # list of word set
    for l in lines:
        if "<dmoz_doc>" in l:
            start_doc = True
            doc = []
        elif "</dmoz_doc>" in l:
            start_doc = False
            res.append(DocWords(doc))
        if start_doc:
            doc.append(l)
    return res

# gather all the words from list of set of words. Words must appear at
# least in 2 documents to be included in the result
def gatherWords(listWS):
    mw = []                     # list of all words including duplicates
    for ws in listWS:
        mw += list(ws)
    cw = Counter(mw)            # multiset of words (using Counter)
    # 7) Words appearing in less than 3 documents are removed
    words = set([w for w in cw.keys() if cw[w] > 2])
    return words

# take dom of positive and negative and write the CSV table on the
# stdout
def convertF2CSV(posFile, negFile, targetVar, outputFileName):
    # list of all positive doc with all present words
    plws = FListWords(posFile)
    # list of all negative doc with all present words
    nlws = FListWords(negFile)
    # list of all words
    words = gatherWords(plws+nlws)

    print len(words)
    
    # write the header of the CSV, i.e. list of words, and targetVar
    # as last argument
    outputFile = open(outputFileName, "w") if outputFileName else sys.stdout
    for w in words:
        outputFile.write(w+",")
    outputFile.write(targetVar)
    outputFile.write(os.linesep)
    # write alternation of positive and negative (so that truncating
    # the data will remained unbiased)
    for i in range(max(len(plws), len(nlws))):
        if i < len(plws):
            for w in words:
                outputFile.write(("1" if w in plws[i] else "0")+",")
            outputFile.write("1")           # because it is positive
            outputFile.write(os.linesep)
        if i < len(nlws):
            for w in words:
                outputFile.write(("1" if w in nlws[i] else "0")+",")
            outputFile.write("0")           # because it is negative
            outputFile.write(os.linesep)

# take file names of positive and negative and write the CSV table on
# the stdout
def convertFN2CSV(posFileName, negFileName, targetVar, outputFileName):
    check_file("Positive XML file", posFileName)
    check_file("Negative XML file", negFileName)
    posFile = open(posFileName)
    negFile = open(negFileName)
    convertF2CSV(posFile, negFile, targetVar, outputFileName)
    
def main():
    usage = "usage: %prog POSITIVE_FILE NEGATIVE_FILE TARGET_VAR_NAME [-o OUTPUT_FILE]"
    parser = OptionParser(usage)
    parser.add_option("-o", "--output-file",
                      dest="outputFile",
                      help="File where to output the result. If not specified the result is printed on stdout.")
    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error("incorrect number of arguments. Use --help to get more information")

    posFN = args[0]
    negFN = args[1]
    targetVar = args[2]

    # # for debugging
    # print "posFN = "+posFN
    # print "negFN = "+negFN
    # print "target = "+targetVar
    # print "outputFN = "+options.outputFile

    convertFN2CSV(posFN, negFN, targetVar, options.outputFile)

if __name__ == '__main__':
    main()
    
