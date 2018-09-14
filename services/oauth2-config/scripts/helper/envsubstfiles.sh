#!/bin/bash

# This script expands environment variables in all files of a directory
# ./envsubst.sh path/to/config/files/*

set -euo pipefail

function envsubstfiles {
    usepath=$1
    for filename in $usepath; do
        echo "Substituting environment variables in file $filename"
        envsubst < ${filename} > ${filename}.env
        rm ${filename}
        mv ${filename}.env ${filename}
    done
}
