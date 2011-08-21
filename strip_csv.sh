#!/bin/bash
#
# Remove text files after producing CSV file with techtc2CSV.py

if [ $# != 1 ]; then
    echo "Wrong number of arguments"
    echo "Usage: $0 TECHTC_DIR"
    exit 1
fi

TECHTC_DIR=$(readlink -f $1) # get the absolute path, no matter what

# remove all txt files
find "${TECHTC_DIR}" -name "*.txt" -exec rm {} \;

# remove all html files
find "${TECHTC_DIR}" -name "*.html" -exec rm {} \;

# remove all empty directories
find "${TECHTC_DIR}" -type d | (while read x; do if [ -z "$(ls -A $x)" ]; then rm -fr "$x"; fi; done)
