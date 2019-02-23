"""
  Flask app that walks through a given directory to index
  ROM ZIPs and renders web pages using templates.
"""
import json
import os

from collections import OrderedDict
from datetime import datetime

import requests

from flask import Flask, request, render_template, Response

app = Flask(__name__) # pylint: disable=invalid-name

DEVICE_JSON = 'devices.json'
DIR = os.getenv('DIR', '/var/www/get.aosiprom.com')
DATEFORMAT = '%Y-%m-%d'


def get_date_from_zip(zip_name):
    """
      Helper function to parse a date from a ROM ZIP's name
    """
    return zip_name.split('-')[-1].split('.')[0]


def get_devices():
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
    return render_template('latest.html', zips=get_zips(DIR), devices=get_devices())


@app.route('/<device>')
def latest_device(device):
    """
      Show the latest release for the current device
    """
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


@app.route('/changelog')
def get_changelog():
    """
    Function to return list of changes between a certain date change from a gerrit instance
    """
    gerrit_url = "https://review.aosiprom.com"
    if 'from' in request.args:
        try:
            from_date = datetime.utcfromtimestamp(int(request.args.get('from'))).strftime(
                DATEFORMAT)
        except Exception:
            return 'ERROR: <code>from</code> parameter expected to be a unix timestamp', 400
    else:
        return 'ERROR: <code>from</code> parameter has to be specified', 400
    if 'to' in request.args:
        try:
            to_date = datetime.utcfromtimestamp(int(request.args.get('to'))).strftime(DATEFORMAT)
        except Exception:
            return 'ERROR: <code>to</code> parameter expected to be a unix timestamp', 400
    else:
        to_date = datetime.utcnow().strftime(DATEFORMAT)

    if 'filter' in request.args:
        projects_filter = request.args.get('filter')
        url = f'{gerrit_url}/changes/?q=is:merged+projects:{projects_filter}+since:{from_date}+until:{to_date}'
    else:
        url = f'{gerrit_url}/changes/?q=is:merged+since:{from_date}+until:{to_date}'

    data = requests.get(url).text[5:-1]  # fuck gerrit xss protection
    commits = json.loads(data)
    changelog = []
    for commit in commits:
        changelog.append(commit['subject'])

    # Remove duplicate entries
    changelog = list(OrderedDict.fromkeys(changelog))
    return Response('\n'.join(changelog), mimetype='text/plain')


if __name__ == '__main__':
    app.run()
