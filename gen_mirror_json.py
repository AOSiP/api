#!/usr/bin/env python

#pylint: disable=missing-docstring,invalid-name

from __future__ import print_function
import hashlib
import glob
import json
import os
import sys

FILE_BASE = os.getenv('FILE_BASE', '/mnt/builds')
builds = {}
cwd = os.getcwd()
os.chdir(FILE_BASE)
for f in sorted(glob.glob('*')):
    if f[0] != '.' and f[0] != '_':
        os.chdir(f)
        try:
            filename = sorted(glob.glob('*Official*.zip'))[-1]
            _, version, buildtype, device, builddate = os.path.splitext(filename)[0].split('-')
            print('hashing sha256 for {}'.format(filename), file=sys.stderr)
            builds.setdefault(device, []).append({
                'sha256': hashlib.sha256(open(filename).read()).hexdigest(),
                'size': os.path.getsize(filename),
                'datetime': '{}{}{}'.format(builddate[0:4], builddate[4:6], builddate[6:8]),
                'filename': filename,
                'filepath': '/{}/{}'.format(f, filename),
                'version': version,
                'type': buildtype.lower()
            })
        except IndexError:
            continue
        finally:
            os.chdir('../')

#pylint: disable=consider-iterating-dictionary
for device in builds.keys():
    builds[device] = sorted(builds[device], key=lambda x: x['date'])
print(json.dumps(builds, sort_keys=True, indent=4))
os.chdir(cwd)
