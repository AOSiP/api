#!/usr/bin/env bash

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place *.py

isort *.py

black *.py


