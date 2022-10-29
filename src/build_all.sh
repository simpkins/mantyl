#!/bin/bash
#
# Copyright (c) 2022, Adam Simpkins
#

PROJECTS=(v1 test)
IDF_PY=idf.py

function fail() {
    echo "Error building $1"
    exit 1
}

for project in ${PROJECTS[@]}; do
    echo "Building $project..."
    ( cd $project && $IDF_PY build ) || fail "$project"
done
echo "All builds successful"
