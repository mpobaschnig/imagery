#!/bin/sh 

exec flatpak-spawn --host nvidia-smi "$@"
