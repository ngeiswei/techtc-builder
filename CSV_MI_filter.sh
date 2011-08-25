#!/bin/bash
#
# prefilter a dataset collection using feature-selection

if [ $# != 2 ]; then
    echo "Wrong number of arguments"
    echo "Usage: $0 TECHTC_DIR THRESHOLD"
    exit 1
fi

TECHTC_DIR=$(readlink -f $1) # get the absolute path, no matter what
MI_THRESHOLD=$2
NEW_TECHTC_DIR=${TECHTC_DIR}_MI_$MI_THRESHOLD

set -x
cp -fr "$TECHTC_DIR" "$NEW_TECHTC_DIR"

find "$NEW_TECHTC_DIR" -name "data.csv" | parallel feature-selection -i {} -o {} -ainc "-T$MI_THRESHOLD" -D 0 -L
