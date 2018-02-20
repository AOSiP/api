#!/usr/bin/env python3
#pylint: disable=line-too-long,missing-docstring,invalid-name
from __future__ import absolute_import

import json
import os
from time import time, strftime

import arrow
import requests
from config import Config
from custom_exceptions import DeviceNotFoundException, UpstreamApiException
from flask import Flask, jsonify, request, render_template, Response
from flask_caching import Cache

app = Flask(__name__)
app.config.from_object("config.Config")

cache = Cache(app)

##########################
# Exception Handling
##########################

@app.errorhandler(DeviceNotFoundException)
def handle_unknown_device(error):
    oem_to_devices, device_to_oem = get_oem_device_mapping()
    return render_template("error.html", header='Whoops - this page doesn\'t exist', message=error.message, oem_to_devices=oem_to_devices, device_to_oem=device_to_oem), error.status_code

@app.errorhandler(UpstreamApiException)
def handle_upstream_exception(error):
    oem_to_devices, device_to_oem = get_oem_device_mapping()
    return render_template("error.html", header='Something went wrong', message=error.message, oem_to_devices=oem_to_devices, device_to_oem=device_to_oem), error.status_code


##########################
# Mirrorbits Interface
##########################

@cache.memoize(timeout=3600)
def get_builds():
    try:
        req = requests.get(app.config['UPSTREAM_URL'])
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
        raise DeviceNotFoundException("This device has no available builds. Please select another device.")
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
            "url": '{}{}'.format(app.config['DOWNLOAD_BASE_URL'], rom['filepath']),
            "romtype": rom['type'],
            "datetime": arrow.get(rom['date']).timestamp,
            "version": rom['version'],
            "filename": rom['filename']
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

@app.route('/api/v1/<string:device>/<string:romtype>/<string:incrementalversion>')
#cached via memoize on get_build_types
def index(device, romtype, incrementalversion):
    #pylint: disable=unused-argument
    after = request.args.get("after")
    version = request.args.get("version")

    return get_build_types(device, romtype, after, version)

@app.route('/api/v1/types/<string:device>/')
@cache.cached(timeout=3600)
def get_types(device):
    data = get_device(device)
    types = set(['nightly'])
    for build in data:
        types.add(build['type'])
    return jsonify({'response': list(types)})

@app.route('/api/v1/devices')
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
