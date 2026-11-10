#!/bin/sh
set -eu
fc-match "$2" | head -n1
