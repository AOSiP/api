"""
  Flask app that walks through a given directory to index
  ROM ZIPs and renders web pages using templates.
"""
import json
import os
import requests

from flask import Flask, render_template

app = Flask(__name__) # pylint: disable=invalid-name

DEVICE_JSON = 'https://raw.githubusercontent.com/AOSiP/api/master/devices.json'

DIR = os.getenv('DIR', '/var/www/get.aosiprom.com')


def get_date_from_zip(zip_name):
    """
      Helper function to parse a date from a ROM ZIP's name
    """
    return zip_name.split('-')[-1].split('.')[0]


def get_zips(directory):
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
    return render_template('latest.html', zips=get_zips(DIR))


@app.route('/<device>')
def latest_device(device):
    """
      Show the latest release for the current device
    """
    data = requests.get(DEVICE_JSON)
    if data.status_code != 200:
        return "Unable to get information for {}".format(device)
    json_data = json.loads(data.text)
    device_in_json = False
    for j in json_data:
        try:
            if j['codename'] == device:
                xda_url = j['xda']
                phone = j['device']
                maintainers = j['maintainer']
                device_in_json = True
                break
        except KeyError:
            return "Unable to get information for {}".format(device)

    if os.path.isdir(os.path.join(DIR, device)):
        if device_in_json:
            return render_template('device.html',
                                   zip=get_zips(os.path.join(DIR, device))[0],
                                   device=device, phone=phone, xda=xda_url, maintainer=maintainers)
        return render_template('device_serveronly.html',
                               zip=get_zips(os.path.join(DIR, device))[0],
                               device=device)

    return "There isn't any build for {} available here!".format(device)


if __name__ == '__main__':
    app.run()
