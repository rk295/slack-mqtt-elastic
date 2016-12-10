#!/bin/bash

# This script is used to setup all the env vars for the scripts. I don't
# wish to commit my keys to git, so the last thing it does is include a
# local override file.

# MQTT Config
export MQTT_HOST='localhost'
export MQTT_USER='username' # Optional
export MQTT_PASS='password' # Optional

# Source a virtual env if using

if [[ -e "venv/bin/activate" ]] ; then
    . venv/bin/activate
fi

if [[ -e "vars.local.sh" ]]; then
    . vars.local.sh
fi
