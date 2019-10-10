#!/bin/bash

sphinx-apidoc -e -P -f -o source/ ../src/ ../src/run.py ../src/debug.py
make html