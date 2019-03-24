#!/usr/bin/env python3
"""
  Flask app that walks through a given directory to index
  ROM ZIPs and renders web pages using templates.
"""
import json
import os

from flask import Flask, redirect, render_template

app = Flask(__name__) # pylint: disable=invalid-name

DEVICE_JSON = 'devices.json'
DIR = os.getenv('DIR', '/var/www/get.aosiprom.com')

def get_date_from_zip(zip_name: str) -> str:
    """
      Helper function to parse a date from a ROM ZIP's name
    """
    return zip_name.split('-')[-1].split('.')[0]


def get_devices() -> dict:
    """
      Returns a dictionary with the list of codenames and actual
      device names
    """
    data = open(DEVICE_JSON).read()
    devices = {}
    json_data = json.loads(data)
    for j in json_data:
        devices[j['codename']] = j['device']
    return devices


def get_zips(directory: str) -> list:
    """
      Return a the ZIP from a specified directory after running
      some sanity checks
    """
    zips = {}
    for file in [os.path.join(dp, file) for dp, dn, fn in os.walk(directory) for file in fn]:
        if file.split('.')[-1] != 'zip':
            continue
        zip_name = file.split('/')[-1]
        device = zip_name.split('-')[3]
        if device in zips:
            if get_date_from_zip(zips[device]) > get_date_from_zip(zip_name):
                continue
        zips[device] = zip_name
    data = list(zips.values())
    data.sort()
    return data

@app.route('/')
def show_files():
    """
      Render the template with ZIP info
    """
    return render_template('latest.html', zips=get_zips(DIR), devices=get_devices())


@app.route('/<device>')
def latest_device(device: str):
    """
      Show the latest release for the current device
    """
    if device == 'beta':
        return redirect('https://get.aosiprom.com', code=301)
    xda_url = phone = maintainers = None
    data = open(DEVICE_JSON).read()
    json_data = json.loads(data)
    for j in json_data:
        try:
            if j['codename'] == device:
                xda_url = j['xda']
                phone = j['device']
                maintainers = j['maintainer']
                break
        except KeyError:
            return "Unable to get information for {}".format(device)

    if os.path.isdir(os.path.join(DIR, device)):
        return render_template('device.html',
                               zip=get_zips(os.path.join(DIR, device))[0],
                               device=device, phone=phone, xda=xda_url, maintainer=maintainers)

    return "There isn't any build for {} available here!".format(device)


if __name__ == '__main__':
    app.run()
