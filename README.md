AOSiP Updater Backend
=======================
Copyright (c) 2017 The LineageOS Project<br>
Copyright (c) 2018-2019 AOSiP<br>

Adding a new device
---
1. Add your device to devices.json, sorted alphanumerically by codename. Fields are documented below.
2. Submit your change to [gerrit](https://review.aosiprom.com)

### devices.json
devices.json is an array of objects, each with several fields:

* `codename`: The codename of the device - example `beryllium`
* `device`: The full name - example `Pocophone F1`
* `maintainer`: Your name
* `xda`: URL to XDA thread of your device

Development set up:
---
1. Setup a virtualenv - `python3 -m venv ./venv`
2. Activate it - `source venv/bin/activate`
3. Install requirements with `pip install -r requirements.txt`
4. Configure your environment appropriately - see the beginning of `app.py` for some variables you _may_ need to modify
5. Run with `./app.py`


Example API Calls:
---
Obtaining rom list for a device:<br>
`GET /<device>/<romtype>` <br>
`<device>` - Codename of device. Example: `beryllium`<br>
`<romtype>` - Buildtype of rom. Example: `official`<br>