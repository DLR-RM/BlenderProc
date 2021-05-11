#!/bin/bash

sphinx-apidoc -e -P -f -o source/ ../src/ ../src/run.py ../src/debug.py ../src/debug_startup.py
make html

cp source/readme.jpg build/html
cp source/BlenderProcVideoImg.jpg build/html
cd source
cp examples/**/*.jpg ../build/html/ --parents
cp examples/**/*.png ../build/html/ --parents
