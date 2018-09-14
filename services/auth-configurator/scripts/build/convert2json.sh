#!/bin/bash

# This script tries to convert all YAML configuration files to JSON
# configuration files.

set -euo pipefail

function yaml2json {
    for filename in $1; do
        if [[ -f $filename ]]; then
            echo "Processing $filename"
            /scripts/build/yaml2json.py < ${filename} > ${filename}.json
            rm ${filename}
        fi
    done
}

yaml2json "/config/hydra/clients/*.yaml"
yaml2json "/config/hydra/clients/*.yml"
yaml2json "/config/oathkeeper/rules/*.yaml"
yaml2json "/config/oathkeeper/rules/*.yml"
yaml2json "/config/keto/policies/*.yaml"
yaml2json "/config/keto/policies/*.yml"
