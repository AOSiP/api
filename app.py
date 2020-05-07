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

from utils import get_date_from_zip, get_metadata_from_zip

# pylint: disable=missing-docstring,invalid-name

app = Flask(__name__)

DEVICE_JSON = "devices.json"
BUILDS_JSON = "builds.json"
DIR = os.getenv("BUILDS_DIRECTORY", "/mnt/builds")
ALLOWED_BUILDTYPES = ["alpha", "beta", "official", "gapps"]
ALLOWED_VERSIONS = ["9.0", "10"]

UPSTREAM_URL = os.environ.get("UPSTREAM_URL", "https://aosip.dev/builds.json")
DOWNLOAD_BASE_URL = os.environ.get("DOWNLOAD_BASE_URL", "https://get.aosip.dev")


def get_devices() -> dict:
    """
    Returns a dictionary with the list of codenames and actual
    device names
    """
    data = open(DEVICE_JSON).read()
    devices = {}
    json_data = json.loads(data)
    for j in json_data:
        devices[j["codename"]] = j["device"]
    return devices


def get_zips(directory: str) -> list:
    """
    Return a the ZIP from a specified directory after running
    some sanity checks
    """
    zips = {}
    for file in [
        os.path.join(dp, file) for dp, dn, fn in os.walk(directory) for file in fn
    ]:
        if file.split(".")[-1] != "zip":
            continue
        zip_name = file.split("/")[-1]
        if zip_name.split(".")[0].split("-")[-1] == "img":
            continue
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


def get_builds() -> dict:
    with open('builds.json', 'r') as builds:
        return json.loads(builds.read())


def get_device(device: str) -> list:
    if device not in get_devices().keys():
        return []
    return get_builds()[device]


def get_build_types(device: str, romtype: str) -> list:
    roms = get_device(device)
    roms = [x for x in roms if x["type"] == romtype]
    if len(roms) == 0:
        return {}
    rom = roms[0]

    return [
        {
            "id": rom["sha256"],
            "url": "{}{}{}".format(DOWNLOAD_BASE_URL, rom["filepath"], rom["filename"]),
            "romtype": rom["type"],
            "datetime": arrow.get(rom["date"]).timestamp,
            "version": rom["version"],
            "filename": rom["filename"],
            "size": rom["size"],
        }
    ]


##########################
# API
##########################


@app.route("/")
def show_files():
    """
    Render the template with ZIP info
    """
    zips = get_zips(DIR)
    devices = get_devices()
    build_dates = {}
    for zip in zips:
        zip = os.path.splitext(zip)[0]
        device = zip.split('-')[3]
        if device not in devices:
            devices[device] = device
        build_date = zip.split('-')[4]
        if device not in build_dates or build_date > build_dates[device]:
            build_dates[device] = build_date

    for date in build_dates:
        build_dates[date] = datetime.strftime(
            datetime.strptime(build_dates[date], '%Y%m%d'), '%A, %d %B - %Y'
        )

    return render_template("latest.html", devices=devices, build_dates=build_dates)


@app.route("/<string:target_device>")
def latest_device(target_device: str):
    """
    Show the latest release for the current device
    """
    zip_name = {}
    with open(BUILDS_JSON, "r") as f:
        json_data = json.loads(f.read())

    if target_device not in json_data:
        return f"There isn't any build for {target_device} available here!"

    for build in json_data[target_device]:
        if build.get("type") in ALLOWED_BUILDTYPES:
            zip_name[build.get("type")] = build.get("filename")

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

    if zip_name:
        return render_template(
            "device.html",
            zip=zip_name,
            device=target_device,
            model=model,
            xda=xda_url,
            maintainer=maintainers,
        )


@app.route("/<string:device>/<string:romtype>")
def ota(device: str, romtype: str):
    return jsonify({'response': get_build_types(device, romtype)})


@app.route("/changelog/<string:device>")
def changelog(device: str):
    changelog_base_url = (
        'https://raw.githubusercontent.com/AOSiP-Devices/Updater-Stuff/master'
    )
    changelog_url = os.path.join(changelog_base_url, 'changelog')
    device_changelog_url = os.path.join(changelog_base_url, device, 'changelog')

    changelog = requests.get(changelog_url).text

    response = requests.get(device_changelog_url)
    if response.status_code != 200:
        return f"Fetching changelog for {device} failed!"

    changelog += '\n' + response.text

    return changelog.replace('\n', '<br>')


if __name__ == "__main__":
    app.run()
