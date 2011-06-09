#!/bin/bash
#
# Script to run techtc-builder in 2 parts
# 1) to parse the RDF content and structure files
# 2) to fetch web pages
#
# It assumes of course that build-techtc.py is in the PATH on the
# remote machine
#
# This is offered in case one doesn't have both a powerful machine
# enough to parse (due to the high memory requirement) and fetch web
# pages (due to the high bandwidth requirement).
#
# Usage: ./remote-build-techtc REMOTE_PARSE [Options]
#
# Options are directly passed to build-techtc.py

set -e                          # exist if use undefined variable
set -o errexit                  # output error message when exit

if [ $# -lt 1 ]; then
    echo "Wrong number of arguments"
    echo "Usage: $0 REMOTE_PARSE [Options]"
    echo "where REMOTE_PARSE is the IP of the machine in charge of doing the parsing (which takes a lot of memory)"
    echo "Options are directly passed to build-techtc.py."
    exit 1
fi

REMOTE_PARSE=$1

TECHTC_DUMP=techtc.dump

# passed options
for i in `seq 2 $#`; do
    ARG="$ARG ${!i}"
done
# arguments for parsing
OARG="$ARG -o$TECHTC_DUMP -P"

# run parsing
echo Run parsing
if [ $REMOTE_PARSE == localhost ]; then
    echo build-techtc.py $OARG 
    build-techtc.py $OARG
else
    echo ssh $REMOTE_PARSE \"build-techtc.py $OARG\"
    ssh $REMOTE_PARSE "build-techtc.py $OARG"
    # copy dump file
    echo Copy dump file
    echo scp $REMOTE_PARSE:$TECHTC_DUMP .
    scp "$REMOTE_PARSE:$TECHTC_DUMP" .
fi


# built techtc locally
# arguments for creating techtc
IARG="$ARG -i$TECHTC_DUMP -C"
echo Build techtc locally
echo build-techtc.py $IARG
build-techtc.py $IARG
