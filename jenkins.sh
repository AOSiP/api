#!/usr/bin/env bash
source venv/bin/activate
gunicorn app:app --workers=$(nproc) -b :5000
