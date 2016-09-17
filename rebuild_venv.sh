#!/usr/bin/env bash

set -euo pipefail

virtualenv venv
venv/bin/pip install -r requirements.txt
