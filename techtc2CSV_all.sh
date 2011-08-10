#!/bin/sh
#
# Author: Nil Geisweiller

if [ -z "$1" ]; then
    echo "Takes the directory containing all subdirectories of techTC,"
    echo "preprocess the text files and write in each directory a CSV file where"
    echo "each row corresponds to a document, columns correspond to words"
    echo "(filtered and stemmed) and the last column correspond to the result (1"
    echo "if it is the first category, 0 if it is in the second category)"

    echo "Usage: $0 TECHTC_DIR"
    exit 1
fi

TECHTC_DIR=$(readlink -f $1) # get the absolute path, no matter what

DIRECTORY=$(cd `dirname "$0"` && pwd)

# this is obviously not useful if the build-techtc has been run under linux
# echo "Convert from DOS to Unix text format"
# find "${TECHTC_DIR}" -name "all*.txt" -type f -exec fromdos {} \;

# convert all_pos.txt and all_neg.txt in each directory into a CSV
# file where each feature is a word appearance (whether it appears in
# the text or not) and the target feature is whether the document
# belongs to the first category
echo "Convert all pos and neg text files into data.csv"
find "${TECHTC_DIR}" -name "Exp_*" -type d | parallel "${DIRECTORY}/techtc2CSV.py" {}"/all_pos.txt" {}"/all_neg.txt" "__target__" -o {}"/data.csv"
