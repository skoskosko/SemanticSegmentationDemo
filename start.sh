#!/bin/bash

IMAGE_URL=http://192.168.0.2:56000/jpeg

BASEDIR=$(dirname "$0")

python3 -u "$BASEDIR/main.py" --url $IMAGE_URL "$@"
