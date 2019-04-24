#!/usr/bin/env python3
"""
  Flask app that walks through a given directory to index
  ROM ZIPs and renders web pages using templates.
"""

#pylint: disable=missing-docstring,invalid-name

import json
import os

import arrow
import requests
from flask import Flask, jsonify, redirect, request, render_template
from flask_caching import Cache
from custom_exceptions import DeviceNotFoundException, UpstreamApiException
from utils import get_date_from_zip, get_metadata_from_zip

app = Flask(__name__)

cache = Cache(app)

DEVICE_JSON = 'devices.json'
BUILDS_JSON = 'builds.json'
DIR = os.getenv('DIR', '/mnt/builds')
ALLOWED_BUILDTYPES = ['beta', 'official']
ALLOWED_VERSIONS = ['9.0']

UPSTREAM_URL = os.environ.get('UPSTREAM_URL', 'https://aosip.dev/builds.json')
DOWNLOAD_BASE_URL = os.environ.get('DOWNLOAD_BASE_URL', 'https://get.aosip.dev')

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

        try:
            version, buildtype, device, builddate = get_metadata_from_zip(zip_name)
        except IndexError:
            continue

        if buildtype.lower() not in ALLOWED_BUILDTYPES:
            continue
        if version not in ALLOWED_VERSIONS:
            continue

        if device in zips:
            if get_date_from_zip(zips[device]) > builddate:
                continue
        zips[device] = zip_name
    data = list(zips.values())
    data.sort()
    return data


@cache.memoize(timeout=3600)
def get_builds():
    try:
        req = requests.get(UPSTREAM_URL)
        if req.status_code != 200:
            raise UpstreamApiException('Unable to contact upstream API')
        return json.loads(req.text)
    except Exception as e:
        print(e)
        raise UpstreamApiException('Unable to contact upstream API')

def get_device_list():
    return get_builds().keys()

def get_device(device):
    builds = get_builds()
    if device not in builds:
        raise DeviceNotFoundException("This device has no available builds."
                                      "Please select another device.")
    return builds[device]

@cache.memoize(timeout=3600)
def get_build_types(device, romtype, after, version):
    roms = get_device(device)
    roms = [x for x in roms if x['type'] == romtype]
    for rom in roms:
        rom['date'] = arrow.get(rom['date']).datetime
    if after:
        after = arrow.get(after).datetime
        roms = [x for x in roms if x['date'] > after]
    if version:
        roms = [x for x in roms if x['version'] == version]

    data = []

    for rom in roms:
        data.append({
            "id": rom['sha256'],
            "url": '{}{}{}'.format(DOWNLOAD_BASE_URL, rom['filepath'], rom['filename']),
            "romtype": rom['type'],
            "datetime": arrow.get(rom['date']).timestamp,
            "version": rom['version'],
            "filename": rom['filename'],
            "size": rom['size'],
        })
    return jsonify({'response': data})

@cache.memoize(timeout=3600)
def get_device_version(device):
    if device == 'all':
        return None
    return get_device(device)[-1]['version']

##########################
# API
##########################
@app.route('/')
def show_files():
    """
      Render the template with ZIP info
    """
    return render_template('latest.html', zips=get_zips(DIR), devices=get_devices())


@app.route('/<string:device>')
def latest_device(device: str):
    """
      Show the latest release for the current device
    """
    zip_name = {}
    if device == 'beta':
        return redirect('https://get.aosip.dev', code=301)
    xda_url = phone = maintainers = None
    f = open(DEVICE_JSON, 'r')
    data = f.read()
    f.close()
    json_data = json.loads(data)
    for j in json_data:
        try:
            if j['codename'] == device:
                xda_url = j['xda']
                phone = j['device']
                maintainers = j['maintainer']
                break
        except KeyError:
            return f"Unable to get information for {device}"

    f = open(BUILDS_JSON, 'r')
    data = f.read()
    f.close()
    json_data = json.loads(data)
    for j in json_data[device]:
        if j['type'] in ALLOWED_BUILDTYPES:
            zip_name[j['type']] = j['filename']

    if zip_name:
        return render_template('device.html',
                               zip=zip_name, device=device, phone=phone, xda=xda_url,
                               maintainer=maintainers)

    return f"There isn't any build for {device} available here!"


@app.route('/<string:device>/latest')
def latest_device_url(device: str):
    """
      Redirect to the official latest build the device has
    """

    data = json.loads(requests.get(f'{request.host_url}{device}/official').text)
    return redirect(data['response'][0]['url'])

@app.route('/<string:device>/<string:romtype>')
#cached via memoize on get_build_types
def index(device, romtype):
    #pylint: disable=unused-argument
    after = request.args.get("after")
    version = request.args.get("version")

    return get_build_types(device, romtype, after, version)

@app.route('/types/<string:device>/')
@cache.cached(timeout=3600)
def get_types(device):
    data = get_device(device)
    types = set(['official'])
    for build in data:
        types.add(build['type'])
    return jsonify({'response': list(types)})

@app.route('/devices')
@cache.cached(timeout=3600)
def api_v1_devices():
    data = get_builds()
    versions = {}
    for device in data.keys():
        for build in data[device]:
            versions.setdefault(build['version'], set()).add(device)
    #pylint: disable=consider-iterating-dictionary
    for version in versions.keys():
        versions[version] = list(versions[version])
    return jsonify(versions)


if __name__ == '__main__':
    app.run()
