#!/bin/bash

rm build -r
find source/*.rst ! -name 'index.rst' -type f -exec rm -f {} +
sphinx-apidoc -e -P -f -o source/ ../blenderproc ../blenderproc/command_line ../blenderproc/resources ../blenderproc/external  ../blenderproc/scripts ../blenderproc/run.py ../blenderproc/debug.py ../blenderproc/debug_startup.py
python3 cleanup_api_imports.py
make html

cd source
cp images/* ../build/html/ --parents
#cp images/**/*.jpg ../build/html/ --parents
#cp images/**/*.png ../build/html/ --parents
