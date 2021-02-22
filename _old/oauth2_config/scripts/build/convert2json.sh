#!/bin/bash

# This script tries to convert all YAML configuration files to JSON
# configuration files.

set -euo pipefail
shopt -s globstar

function yaml2json {
    for filename in $1; do
        if [[ -f $filename ]]; then
            echo "Processing $filename"
            /scripts/build/yaml2json.py < ${filename} > ${filename}.json
            rm ${filename}
        fi
    done
}

yaml2json "/config/**/*.yaml"
yaml2json "/config/**/*.yml"
