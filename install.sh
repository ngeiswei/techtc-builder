#!/bin/bash

# source shflags
. ./shflags

# define a 'prefix' command-line string flag
DEFINE_string 'prefix' '/usr/local' 'where to install build-techtc' 'p'

# parse the command-line
FLAGS "$@" || exit 1
eval set -- "${FLAGS_ARGV}"

# copy the utilies under prefix/bin
echo cp build-techtc.py "${FLAGS_prefix}/bin"
cp build-techtc.py "${FLAGS_prefix}/bin"
echo cp remote-build-techtc.sh "${FLAGS_prefix}/bin"
cp remote-build-techtc.sh "${FLAGS_prefix}/bin"
