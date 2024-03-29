#!/usr/bin/env python3

# pylint: disable=missing-docstring,invalid-name,broad-except,cell-var-from-loop

import hashlib
import json
import os
import sys

from utils import get_date_from_zip, get_metadata_from_zip

ALLOWED_BUILDTYPES = ["Official", "Gapps"]
ALLOWED_VERSIONS = ["9.0", "10", "11"]
FILE_BASE: str = os.getenv("FILE_BASE", "/home/kronic/builds")
DEBUG = False
builds: dict = {}
zips: dict = {}

for file in [
    os.path.join(dp, file) for dp, dn, fn in os.walk(FILE_BASE) for file in fn
]:
    try:
        if file.split(".")[-1] != "zip":
            continue
        zip_name = file.replace(FILE_BASE, "")
        if zip_name.split(".")[0].split("-")[-1] == "img":
            continue
        version, buildtype, device, builddate = get_metadata_from_zip(zip_name)
        if buildtype not in ALLOWED_BUILDTYPES:
            if DEBUG:
                print(
                    f"{zip_name} has a buildtype of {buildtype}, which is not allowed!",
                    file=sys.stderr,
                )
            continue
        if version not in ALLOWED_VERSIONS:
            if DEBUG:
                print(
                    f"{zip_name} has a version of {version}, which is not allowed!",
                    file=sys.stderr,
                )
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
    except Exception:
        continue

for key, value in zips.items():
    for device in value:
        file = value[device]
        try:
            filename = file.split("/")[-1]
            if file[0] == "/":
                file = file[1:]
            file = os.path.join(FILE_BASE, file)
            img_file = os.path.isfile(file.replace(".zip", "-img.zip"))
            boot_img = os.path.isfile(file.replace(".zip", "-boot.img"))
            sha256_file = file.replace(".zip", ".sha256")
            version, buildtype, device, builddate = get_metadata_from_zip(file)
            if os.path.isfile(sha256_file):
                if DEBUG:
                    print(
                        f"SHA256 for {filename} already exists, skipping!",
                        file=sys.stderr,
                    )
            else:
                print(f"Hashing SHA256 for {filename}!", file=sys.stderr)
                sha256 = hashlib.sha256()
                with open(file, "rb") as f:
                    for buf in iter(lambda: f.read(128 * 1024), b""):
                        sha256.update(buf)
                with open(sha256_file, "w") as f:
                    f.write(sha256.hexdigest())

            with open(sha256_file, "r") as f:
                zip_sha256 = f.read()
            builds.setdefault(device, []).append(
                {
                    "sha256": zip_sha256,
                    "size": os.path.getsize(file),
                    "date": "{}-{}-{}".format(
                        builddate[0:4], builddate[4:6], builddate[6:8]
                    ),
                    "filename": filename,
                    "filepath": file.replace(filename, "").replace(FILE_BASE, ""),
                    "version": version,
                    "type": buildtype.lower(),
                    "fastboot_images": img_file,
                    "boot_image": boot_img,
                }
            )
        except IndexError:
            continue

# pylint: disable=consider-iterating-dictionary
for device in builds.keys():
    builds[device] = sorted(builds[device], key=lambda x: x["date"])
print(json.dumps(builds, sort_keys=True, indent=4))
