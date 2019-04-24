#!/usr/bin/env python3

#pylint: disable=missing-docstring,invalid-name,broad-except,cell-var-from-loop

import hashlib
import json
import os.path as path
import sys
import arrow
from pathlib import Path
from app import get_metadata_from_zip

if len(sys.argv) < 2:
    print('Please specify the zip you want the JSON to be generated for!')
    exit(1)

file = sys.argv[1]
filename = file.split('/')[-1]
out_dir = Path(file).parent
buildprop = path.join(out_dir, 'build.prop')
host = 'https://build.aosip.dev'

version, buildtype, device, builddate = get_metadata_from_zip(filename)

if path.isfile(buildprop):
    print('build.prop found, reading ro.build.date.utc', file=sys.stderr)
    with open(buildprop, 'r') as f:
        for line in f:
            if line[0] == '#' or line == '\n':
                continue
            k, v = line.rstrip().split('=')
            if k == 'ro.build.date.utc':
                builddate = v
                break
else:
    print(f'build.prop not found, using {builddate}', file=sys.stderr)
    builddate = arrow.get(builddate[0:4] + '-' + builddate[4:6] + '-' + builddate[6:8]).timestamp

print(f'Hashing SHA256 for {filename}!', file=sys.stderr)
sha256 = hashlib.sha256()
with open(file, 'rb') as f:
    for buf in iter(lambda: f.read(128 * 1024), b''):
        sha256.update(buf)

print({'response':[{
    'id': sha256.hexdigest(),
    'url': '{}/{}'.format(host, filename),
    'romtype': buildtype.lower(),
    'datetime': builddate,
    'version': version,
    'filename': filename,
    'size': path.getsize(file),
}]})