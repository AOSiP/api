#!/usr/bin/env python3

#pylint: disable=missing-docstring,invalid-name

import json
import os
import sys
import requests


KRONIC_API_KEY: str = os.getenv('KRONIC_API_KEY')

if not KRONIC_API_KEY:
    exit(1)

data: str = requests.get('https://raw.githubusercontent.com/AOSiP/api/master/devices.json').text
device: str = sys.argv[1]
buildtype: str = sys.argv[2]

if buildtype == 'CI':
    message = f"New CI build for {device} available!"
    data = requests.get(f"""https://api.telegram.org/bot{KRONIC_API_KEY}/sendMessage?text={message}
                        &chat_id=-1001055786180&parse_mode=Markdown""")
    print(data)
    exit(0)

device_found: bool = False
d: dict = ""

for d in json.loads(data):
    if d['codename'] == device:
        device_found = True
        break

if device_found:
    message = f"""New {buildtype} build for [{d['device']}](https://aosip.dev/{device}) available!
\nMaintainer: {d['maintainer']}\n[XDA]({d['xda']}) | [Changelog](https://raw.githubusercontent.com\
/AOSiP-Devices/Updater-Stuff/master/{device}/changelog)"""
    data = requests.get(f"""https://api.telegram.org/bot{KRONIC_API_KEY}/sendMessage?text={message}
                        &chat_id=@AOSiP&parse_mode=Markdown&disable_web_page_preview=True""")
    print(data)
