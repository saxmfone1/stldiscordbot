#!/bin/bash

Xvfb :1 -screen 0 1920x1080x16 &> xvfb.log  &
export DISPLAY=:1.0
python ./bot.py