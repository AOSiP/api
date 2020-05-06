#!/usr/bin/env bash

[[ -d "venv" ]] || python3.8 -m venv ./venv
source venv/bin/activate
pip install -U -r requirements.txt
gunicorn app:app --workers=$(nproc) -b :5000
