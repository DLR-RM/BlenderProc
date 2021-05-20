#!/bin/bash

sphinx-apidoc -e -P -f -o source/ ../src/ ../src/run.py ../src/debug.py ../src/debug_startup.py
make html

cd source
cp images/* ../build/html/ --parents
cp examples/**/*.jpg ../build/html/ --parents
cp examples/**/*.png ../build/html/ --parents
