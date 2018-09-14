#!/usr/bin/env python

import json
import sys
import yaml

try:
    data = yaml.safe_load(sys.stdin.read())
except yaml.YAMLError as e:
    error_details = str(getattr(e, 'problem_mark', '')).strip()
    sys.stderr.write('YAML parsing error {}\n'.format(error_details))
    sys.exit(1)
else:
    json.dump(data, sys.stdout)
