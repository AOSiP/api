#!/usr/bin/env python3
"""
Flask app that walks through a given directory to index
ROM ZIPs and renders web pages using templates.
"""

import json
import os
from datetime import datetime

import arrow
import requests
from flask import (
    Flask,
    jsonify,
    render_template,
)

# pylint: disable=missing-docstring,invalid-name

app = Flask(__name__)

DEVICE_JSON = "devices.json"
BUILDS_JSON = "builds.json"
ALLOWED_BUILDTYPES = ["official", "gapps"]
ALLOWED_VERSIONS = ("9.0", "10", "11")

DOWNLOAD_BASE_URL = os.environ.get("DOWNLOAD_BASE_URL", "https://aosip.dev/dl")


def get_devices() -> dict:
    """
    Returns a dictionary with the list of codenames and actual
    device names
    """
    with open(DEVICE_JSON, 'r') as f:
        data = json.loads(f.read())
    return {d['codename']: d['device'] for d in data}


def get_zips() -> list:
    """
    Returns list of available builds after reading the builds.json
    """
    with open(BUILDS_JSON, 'r') as f:
        builds = json.loads(f.read())

    return [build['filename'] for device in builds for build in builds[device]]


def get_latest(device: str, romtype: str) -> dict:
    if device not in get_devices().keys():
        return {}
    with open('builds.json', 'r') as builds:
        builds = json.loads(builds.read()).get(device, [])

    for build in builds:
        if build['type'] == romtype:
            return build

    return {}


##########################
# API
##########################


@app.route("/")
def show_files():
    """
    Render the template with ZIP info
    """
    zips = get_zips()
    devices = get_devices()
    build_dates = {}
    for zip_file in zips:
        zip_file = os.path.splitext(zip_file)[0]
        device = zip_file.split('-')[3]
        if device not in devices:
            devices[device] = device
        build_date = zip_file.split('-')[4]
        if device not in build_dates or build_date > build_dates[device]:
            build_dates[device] = build_date

    for device in build_dates:
        build_dates[device] = datetime.strftime(
            datetime.strptime(build_dates[device], '%Y%m%d'), '%A, %d %B - %Y'
        )

    devices = {
        device: device_name
        for device, device_name in devices.items()
        if device in build_dates
    }

    return render_template("latest.html", devices=devices, build_dates=build_dates)


@app.route("/<string:target_device>")
def latest_device(target_device: str):
    """
    Show the latest release for the current device
    """
    available_files = {}
    with open(BUILDS_JSON, "r") as f:
        json_data = json.loads(f.read())

    if target_device not in json_data:
        return f"There isn't any build for {target_device} available here!"

    for build in json_data[target_device]:
        buildtype = build.get('type')
        if buildtype in ALLOWED_BUILDTYPES:
            available_files[buildtype] = build.get('filename')
            if build.get('fastboot_images'):
                available_files[buildtype + '-img'] = build.get('filename').replace(
                    '.zip', '-img.zip'
                )
            if build.get('boot_image'):
                available_files[buildtype + '-boot'] = build.get('filename').replace(
                    '.zip', '-boot.img'
                )

    with open(DEVICE_JSON, "r") as f:
        json_data = json.loads(f.read())
    for device in json_data:
        if device['codename'] == target_device:
            xda_url = device.get('xda')
            model = device.get('device')
            maintainers = device.get('maintainer')
            break
    else:
        model = target_device
        xda_url = None
        maintainers = None

    if available_files:
        return render_template(
            "device.html",
            available_files=available_files,
            device=target_device,
            model=model,
            xda=xda_url,
            maintainer=maintainers,
        )


@app.route("/<string:device>/<string:romtype>")
def ota(device: str, romtype: str):
    rom = get_latest(device, romtype)
    if not rom:
        data = []
    else:
        data = [
            {
                "id": rom["sha256"],
                "url": "{}{}{}".format(
                    DOWNLOAD_BASE_URL, rom["filepath"], rom["filename"]
                ),
                "romtype": rom["type"],
                "datetime": arrow.get(rom["date"]).timestamp,
                "version": rom["version"],
                "filename": rom["filename"],
                "size": rom["size"],
            }
        ]
    return jsonify({'response': data})


if __name__ == "__main__":
    app.run()
