#!/usr/bin/env python

#pylint: disable=missing-docstring,invalid-name

from __future__ import print_function
import hashlib
import json
import os
import sys

from app import get_date_from_zip, get_device_from_zip, get_type_from_zip

ALLOWED_BUILDTYPES = ['Beta', 'CI', 'Official']
FILE_BASE: str = os.getenv('FILE_BASE', '/mnt/builds')
builds: dict = {}
zips: dict = {}

for file in [os.path.join(dp, file) for dp, dn, fn in os.walk(FILE_BASE) for file in fn]:
    try:
        if file.split('.')[-1] != 'zip':
            continue
        zip_name = file.replace(FILE_BASE, '')
        device = get_device_from_zip(zip_name)
        builddate = get_date_from_zip(zip_name)
        buildtype = get_type_from_zip(zip_name)
        if buildtype not in ALLOWED_BUILDTYPES:
            continue
        if device in zips:
            for build in zips[device]:
                if buildtype in zips[device]:
                    if builddate > get_date_from_zip(zips[device][buildtype]):
                        zips[device][buildtype] = zip_name
                    else:
                        raise Exception
                else:
                    zips[device][buildtype] = zip_name
        else:
            zips[device] = {}
            zips[device][buildtype] = zip_name
    except Exception as e:
        continue

for key, value in zips.items():
    for device in value:
        file = zips[key][device]
        print(file)
        try:
            filename = file.split('/')[-1]
            file = os.path.join(FILE_BASE, file)
            _, version, buildtype, device, builddate = os.path.splitext(file)[0].split('-')
            print('hashing sha256 for {}'.format(file), file=sys.stderr)
            builds.setdefault(device, []).append({
                'sha256': hashlib.sha256(open(file).read()).hexdigest(),
                'size': os.path.getsize(file),
                'date': '{}-{}-{}'.format(builddate[0:4], builddate[4:6], builddate[6:8]),
                'filename': filename,
                'filepath': file,
                'version': version,
                'type': buildtype.lower()
            })
        except IndexError:
            continue

#pylint: disable=consider-iterating-dictionary
for device in builds.keys():
    builds[device] = sorted(builds[device], key=lambda x: x['date'])
print(json.dumps(builds, sort_keys=True, indent=4))
